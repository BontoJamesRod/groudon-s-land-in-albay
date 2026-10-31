"""Task T-013: read only the part of a product that covers the site, and cache it.

NISAR products are several gigabytes, but one site is a small corner of a frame.
HDF5 files can be read in pieces, so instead of downloading the whole file we ask
the server for only the byte ranges we need ("ranged reads"), and save the cropped
arrays in raw/. A second run finds them there and downloads nothing.

Every byte fetched is counted and logged in raw/download_log.jsonl, and fetching
stops when the night's budget would be exceeded.
"""
import hashlib
import io
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
from pyproj import Transformer

from mrw.search import require_before_cutoff

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_FOLDER = REPO_ROOT / "raw"
BYTE_BUDGET = 20 * 1000**3  # the night plan's limit: 20 GB
BLOCK_SIZE = 4 * 1024 * 1024  # fetch 4 MiB at a time, so small reads share one request
MAX_BLOCKS = 64
CROP_MARGIN_CELLS = 5  # a little extra around the site, so the speckle filter has neighbours


class BudgetExceeded(Exception):
    """Fetching more would go over the download budget."""


def log_path(raw_folder):
    return Path(raw_folder) / "download_log.jsonl"


def total_bytes_logged(raw_folder=RAW_FOLDER):
    """Add up every byte recorded in the download log."""
    path = log_path(raw_folder)
    if not path.is_file():
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    return sum(json.loads(line)["bytes"] for line in lines if line.strip())


def log_bytes(raw_folder, granule_id, dataset, count):
    """Add one line to the download log."""
    path = log_path(raw_folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "granule_id": granule_id, "dataset": dataset, "bytes": count}
    with path.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry) + "\n")


class RangedFile(io.RawIOBase):
    """A file-like object that fetches blocks from a server only when they are read.

    h5py can read from any Python file object. It asks for small pieces in many
    places, so recently used blocks are kept in memory to avoid repeat requests.
    `fetch(start, end)` returns the bytes from start up to, not including, end.
    """

    def __init__(self, fetch, size, spent_before=0, budget=BYTE_BUDGET):
        super().__init__()
        self.fetch = fetch
        self.size = size
        self.position = 0
        self.blocks = OrderedDict()
        self.bytes_fetched = 0
        self.spent_before = spent_before
        self.budget = budget

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.size}[whence]
        self.position = base + offset
        return self.position

    def _block(self, number):
        """Return one block, fetching it if it isn't in memory yet."""
        if number in self.blocks:
            self.blocks.move_to_end(number)
            return self.blocks[number]
        start = number * BLOCK_SIZE
        end = min(start + BLOCK_SIZE, self.size)
        if self.spent_before + self.bytes_fetched + (end - start) > self.budget:
            raise BudgetExceeded(f"Download budget of {self.budget} bytes reached")
        data = self.fetch(start, end)
        self.bytes_fetched += len(data)
        self.blocks[number] = data
        if len(self.blocks) > MAX_BLOCKS:
            self.blocks.popitem(last=False)
        return data

    def readinto(self, buffer):
        view = memoryview(buffer).cast("B")
        wanted = min(len(view), max(0, self.size - self.position))
        done = 0
        while done < wanted:
            number, offset = divmod(self.position, BLOCK_SIZE)
            piece = self._block(number)[offset:offset + wanted - done]
            if not piece:
                raise OSError("The server returned no data for this range")
            view[done:done + len(piece)] = piece
            done += len(piece)
            self.position += len(piece)
        return done


def open_remote(url, raw_folder=RAW_FOLDER):
    """Open a product on ASF for ranged reads, using the saved Earthdata login.

    Imported here so that tests and CI never need the network or a login.
    """
    import earthaccess
    require_before_cutoff(url)
    if not earthaccess.login(strategy="netrc").authenticated:
        raise RuntimeError("Earthdata login failed")
    system = earthaccess.get_fsspec_https_session()
    size = system.info(url)["size"]
    return RangedFile(lambda start, end: system.cat_file(url, start=start, end=end), size,
                      spent_before=total_bytes_logged(raw_folder))


def crop_window(x_values, y_values, bounds, epsg, margin=CROP_MARGIN_CELLS):
    """Find the rows and columns of a grid that cover the site bounds.

    The products are on a map projection (UTM, in metres) while the site bounds are
    in degrees, so the bounds' edges are converted first. Points along each edge
    are converted too, because a straight line in degrees curves slightly in UTM.
    """
    west, south, east, north = bounds
    transformer = Transformer.from_crs(4326, epsg, always_xy=True)
    lons = np.concatenate([np.linspace(west, east, 21), np.linspace(west, east, 21), np.full(21, west), np.full(21, east)])
    lats = np.concatenate([np.full(21, south), np.full(21, north), np.linspace(south, north, 21), np.linspace(south, north, 21)])
    xs, ys = transformer.transform(lons, lats)
    columns = np.flatnonzero((x_values >= xs.min()) & (x_values <= xs.max()))
    rows = np.flatnonzero((y_values >= ys.min()) & (y_values <= ys.max()))
    if not len(columns) or not len(rows):
        raise ValueError("The product doesn't cover the site bounds")
    return (max(rows[0] - margin, 0), min(rows[-1] + margin + 1, len(y_values)),
            max(columns[0] - margin, 0), min(columns[-1] + margin + 1, len(x_values)))


def _read_epsg(group):
    """Read the projection's EPSG code from the group's `projection` dataset."""
    projection = group["projection"]
    if "epsg_code" in projection.attrs:
        return int(projection.attrs["epsg_code"])
    return int(projection[()])


def read_crop_from_file(fileobj, group_path, dataset_names, bounds, axes_path=None):
    """Read cropped datasets plus their coordinates from an open HDF5 file object."""
    with h5py.File(fileobj, "r") as product:
        group = product[group_path]
        axes = product[axes_path] if axes_path else group
        x_values = axes["xCoordinates"][()]
        y_values = axes["yCoordinates"][()]
        epsg = _read_epsg(axes)
        row0, row1, col0, col1 = crop_window(x_values, y_values, bounds, epsg)
        crop = {"x": x_values[col0:col1], "y": y_values[row0:row1], "epsg": np.array(epsg)}
        for name in dataset_names:
            crop[name] = group[name][row0:row1, col0:col1]
    return crop


def cache_path(raw_folder, granule_id, group_path, dataset_names, bounds):
    """Name the cache file. The name changes if the area or the datasets change."""
    key = json.dumps([group_path, list(dataset_names), list(bounds)])
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return Path(raw_folder) / granule_id / f"crop_{digest}.npz"


def read_crop(granule_id, url, group_path, dataset_names, bounds, axes_path=None,
              raw_folder=RAW_FOLDER, opener=open_remote):
    """Return the cropped datasets of a product, from the cache if they're already there."""
    require_before_cutoff(granule_id)
    path = cache_path(raw_folder, granule_id, group_path, dataset_names, bounds)
    if path.is_file():
        with np.load(path) as saved:
            return {name: saved[name] for name in saved.files}
    fileobj = opener(url, raw_folder)
    try:
        crop = read_crop_from_file(fileobj, group_path, dataset_names, bounds, axes_path)
    finally:
        log_bytes(raw_folder, granule_id, ",".join(dataset_names), fileobj.bytes_fetched)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **crop)
    return crop

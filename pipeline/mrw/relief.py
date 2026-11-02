"""Task T-108: the Field map's relief background, as map tiles (F-22, FR-076, ADR-012).

Relief is a picture of the ground's shape, made from height data. It has nothing to do with the
radar: no radar product is read here, and no published radar file changes.

Run from the project folder. It downloads the height data once into raw/, then makes the tiles:
    python pipeline/mrw/relief.py mayon
"""
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
import requests
from PIL import Image
from rasterio.merge import merge
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject

# Lets this file run as a script from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mrw.config import load_site
from mrw.context import DATA_FOLDER
from mrw.contract_check import relief_tile_range

REPO = Path(__file__).resolve().parents[2]
DEM_FOLDER = REPO / "raw" / "context_download" / "relief"
LOG_FOLDER = REPO / "pipeline" / "logs"
DEM_BASE_URL = "https://copernicus-dem-30m.s3.amazonaws.com"
DOWNLOAD_LIMIT_BYTES = 300_000_000  # the owner's limit for this download
TILE_PIXELS = 256
NO_HEIGHT = -32768.0
EARTH_HALF_WIDTH_M = 20037508.342789244  # half of the web map's width, in its own metres
PAPER = np.array([248, 245, 236.0])
SHADOW = np.array([120, 116, 104.0])
SEA = np.array([205, 226, 238.0])
LIGHT_FROM_DEGREES = 315.0  # the northwest, as on a printed map
LIGHT_HEIGHT_DEGREES = 45.0
HEIGHT_EXAGGERATION = 1.6  # steepens the shading only, to make gentle ground readable
CONTOUR_DARKEN = 0.86
BOLD_CONTOUR_DARKEN = 0.72
CONTOUR_M = 100
BOLD_CONTOUR_M = 500
WEBP_QUALITY = 80


class DownloadTooLarge(Exception):
    """The files would go over the owner's download limit. Nothing was downloaded."""


def dem_names(bounds):
    """The Copernicus files covering (west, south, east, north). Each one covers one degree."""
    west, south, east, north = bounds
    names = []
    for lat in range(math.floor(south), math.ceil(north)):
        for lon in range(math.floor(west), math.ceil(east)):
            ns = f"N{lat:02d}" if lat >= 0 else f"S{-lat:02d}"
            ew = f"E{lon:03d}" if lon >= 0 else f"W{-lon:03d}"
            names.append(f"Copernicus_DSM_COG_10_{ns}_00_{ew}_00_DEM")
    return names


def check_download_size(sizes, limit=DOWNLOAD_LIMIT_BYTES):
    """Stop before anything is downloaded if the total isn't under the limit."""
    total = sum(sizes.values())
    if total >= limit:
        raise DownloadTooLarge(f"The DEM files total {total} bytes, and the limit is under {limit} bytes")
    return total


def download_dem(site_id, bounds):
    """Download the height files that aren't saved yet, and log what they weigh."""
    DEM_FOLDER.mkdir(parents=True, exist_ok=True)
    urls = {name: f"{DEM_BASE_URL}/{name}/{name}.tif" for name in dem_names(bounds)}
    replies = {name: requests.head(url, timeout=60) for name, url in urls.items()}
    # Open sea has no file, and the map paints what has no height as sea.
    sizes = {name: int(reply.headers["Content-Length"]) for name, reply in replies.items() if reply.status_code != 404}
    names = list(sizes)
    total = check_download_size(sizes)
    for name in names:
        url = urls[name]
        path = DEM_FOLDER / f"{name}.tif"
        if path.exists() and path.stat().st_size == sizes[name]:
            continue
        with requests.get(url, stream=True, timeout=300) as reply:
            reply.raise_for_status()
            with path.open("wb") as file:
                for chunk in reply.iter_content(1024 * 1024):
                    file.write(chunk)
    saved = sum((DEM_FOLDER / f"{name}.tif").stat().st_size for name in names)
    LOG_FOLDER.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (LOG_FOLDER / f"{now}_relief_download_{site_id}.json").write_text(json.dumps(
        {"site_id": site_id, "files": sizes, "total_bytes": total, "saved_bytes": saved, "limit_bytes": DOWNLOAD_LIMIT_BYTES},
        indent=1), encoding="utf-8")
    print(f"DEM download: {len(names)} files, {total} bytes ({total / 1e6:.1f} MB), limit {DOWNLOAD_LIMIT_BYTES / 1e6:.0f} MB")
    return [DEM_FOLDER / f"{name}.tif" for name in names]


def hillshade(height, cell_m):
    """How much sunlight each cell gets, from 0 to 1, with the light low in the northwest."""
    rise_south, rise_east = np.gradient(height * HEIGHT_EXAGGERATION, cell_m)
    direction, height_angle = np.radians(LIGHT_FROM_DEGREES), np.radians(LIGHT_HEIGHT_DEGREES)
    light_east = np.cos(height_angle) * np.sin(direction)
    light_north = np.cos(height_angle) * np.cos(direction)
    # Ground that rises to the east faces west, and ground that rises to the south faces north.
    # The more squarely it faces the light, the brighter it is.
    sun = (np.sin(height_angle) - rise_east * light_east + rise_south * light_north) / np.sqrt(1 + rise_east ** 2 + rise_south ** 2)
    return np.clip(sun, 0, 1)


def contour_cells(height, step_m):
    """The cells where the height crosses a contour line."""
    level = np.floor(height / step_m)
    return (level != np.roll(level, 1, axis=0)) | (level != np.roll(level, 1, axis=1))


def paint(height, cell_m, zoom):
    """Colour the ground like a printed map: shaded paper, contour lines and a blue sea."""
    rgb = SHADOW + (PAPER - SHADOW) * np.clip(hillshade(height, cell_m)[..., None] * 1.25, 0, 1)
    # Zoomed out, 100 m lines would run together on the volcano, so only the bold ones stay.
    if zoom >= 12:
        rgb[contour_cells(height, CONTOUR_M)] *= CONTOUR_DARKEN
    rgb[contour_cells(height, BOLD_CONTOUR_M)] *= BOLD_CONTOUR_DARKEN
    rgb[height <= 0] = SEA  # the Copernicus DEM sets the sea to 0
    return rgb.astype("uint8")


def render_zoom(sources, bounds, zoom, out_folder):
    """Make every tile of one zoom, from one big picture so that shading matches across tile edges."""
    x_low, y_low, x_high, y_high = relief_tile_range(bounds, zoom)
    columns, rows = x_high - x_low + 1, y_high - y_low + 1
    tile_m = 2 * EARTH_HALF_WIDTH_M / 2 ** zoom
    left = -EARTH_HALF_WIDTH_M + x_low * tile_m
    top = EARTH_HALF_WIDTH_M - y_low * tile_m
    width, height = columns * TILE_PIXELS, rows * TILE_PIXELS
    transform = from_bounds(left, top - rows * tile_m, left + columns * tile_m, top, width, height)
    ground = np.zeros((height, width), dtype="float32")
    data, data_transform = merge(sources)
    # Zooming out averages the heights, and zooming in blends the nearest ones. "No data" must not be
    # 0: that's the sea's real height, and GDAL would nudge it away from 0 so it stopped counting as sea.
    reproject(data[0], ground, src_transform=data_transform, src_crs="EPSG:4326", dst_transform=transform,
              dst_crs="EPSG:3857", resampling=Resampling.average if zoom < 13 else Resampling.bilinear, dst_nodata=NO_HEIGHT)
    ground[ground == NO_HEIGHT] = 0  # past the height files, which the map never shows
    # A web map's metres stretch away from the equator, so the real size of a cell is smaller.
    middle_lat = (bounds[1] + bounds[3]) / 2
    cell_m = tile_m / TILE_PIXELS * math.cos(math.radians(middle_lat))
    picture = paint(ground, cell_m, zoom)
    for column in range(columns):
        folder = out_folder / str(zoom) / str(x_low + column)
        folder.mkdir(parents=True, exist_ok=True)
        for row in range(rows):
            piece = picture[row * TILE_PIXELS:(row + 1) * TILE_PIXELS, column * TILE_PIXELS:(column + 1) * TILE_PIXELS]
            Image.fromarray(piece).save(folder / f"{y_low + row}.webp", quality=WEBP_QUALITY, method=6)
    return columns * rows


def main(site_id):
    site = load_site(site_id)
    bounds = tuple(site[f"relief_bounds_{side}"] for side in ("west", "south", "east", "north"))
    paths = download_dem(site_id, bounds)
    out_folder = DATA_FOLDER / "sites" / site_id / "relief"
    sources = [rasterio.open(path) for path in paths]
    try:
        for zoom in range(site["min_zoom"], site["relief_max_native_zoom"] + 1):
            print(f"Zoom {zoom}: {render_zoom(sources, bounds, zoom, out_folder)} tiles")
    finally:
        for source in sources:
            source.close()
    files = list(out_folder.rglob("*.webp"))
    print(f"Relief: {len(files)} tiles, {sum(path.stat().st_size for path in files) / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

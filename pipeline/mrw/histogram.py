"""Task T-104: how much did the ground's brightness change? (F-21, FR-072, FR-075)

The map only shows the cells past the flag line. This counts every checked cell by its change in
dB, so that a visitor can see how far out those flagged cells are from most of the ground.

It uses the same web cells as the value grid, so the two can be compared exactly.

To write the files for pairs that are already published, from the crops saved in raw/ (no download,
because each crop is read from the saved copy, and the cutoff still applies):
    python pipeline/mrw/histogram.py mayon
"""
import json
import sys
from pathlib import Path

import numpy as np

# Lets this file run as a script from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mrw.channel_areas import LINE_LICENSE, strip_cells
from mrw.classify import HIGH, LOW, NONE
from mrw.config import load_site, utc_now_text
from mrw.context import DATA_FOLDER, write_json

BIN_START_DB = -10.0
BIN_END_DB = 10.0
BIN_WIDTH_DB = 0.25
BIN_COUNT = round((BIN_END_DB - BIN_START_DB) / BIN_WIDTH_DB)


def count_bins(change_db):
    """Count cells by their change. Cells past either end of the bins are counted on their own."""
    edges = np.linspace(BIN_START_DB, BIN_END_DB, BIN_COUNT + 1)
    # np.histogram would put a cell of exactly BIN_END_DB in the last bin, so count those as above.
    inside = change_db[(change_db >= BIN_START_DB) & (change_db < BIN_END_DB)]
    return {
        "counts": np.histogram(inside, bins=edges)[0].tolist(),
        "below": int(np.count_nonzero(change_db < BIN_START_DB)),
        "above": int(np.count_nonzero(change_db >= BIN_END_DB)),
    }


def summarise(change_db, classes):
    """Count one set of cells, taking which are flagged from the value grid's classes."""
    return {**count_bins(change_db), "total_cells": int(change_db.size),
            "flagged_cells": int(np.count_nonzero(np.isin(classes, (LOW, HIGH))))}


def checked_cells(web_change, web_classes, in_reach):
    """Pick land with a radar value inside the reach. Sea and missing data have no change to count."""
    return np.isin(web_classes, (NONE, LOW, HIGH)) & in_reach & np.isfinite(web_change)


def histogram_row(pair_id, site_id, web_change, web_classes, in_reach):
    """Build the pair's histogram.json (docs/05 TBL-13)."""
    chosen = checked_cells(web_change, web_classes, in_reach)
    summary = summarise(web_change[chosen], web_classes[chosen])
    share = summary["flagged_cells"] / summary["total_cells"] if summary["total_cells"] else 0
    return {"pair_id": pair_id, "site_id": site_id, "bin_start_db": BIN_START_DB, "bin_width_db": BIN_WIDTH_DB,
            **summary, "flagged_share": round(share, 6)}


def channel_histogram_row(pair_id, site_id, web_change, web_classes, in_reach, channels, layer):
    """Build the pair's channel_histogram.json (docs/05 TBL-14): the same counts inside each strip."""
    rows = []
    for channel in channels:
        chosen = checked_cells(web_change, web_classes, in_reach) & strip_cells(channel["properties"]["strip_geometry"], layer)
        rows.append({"channel_id": channel["properties"]["id"], **summarise(web_change[chosen], web_classes[chosen])})
    return {"pair_id": pair_id, "site_id": site_id, "bin_start_db": BIN_START_DB, "bin_width_db": BIN_WIDTH_DB, "channels": rows}


def read_channels(site_id, data_folder=DATA_FOLDER):
    """Read a site's channels. A site with no channel file has none."""
    path = Path(data_folder) / "sites" / site_id / "channels.geojson"
    return json.loads(path.read_text(encoding="utf-8"))["features"] if path.is_file() else []


def write_histograms(folder, pair_id, site_id, web_change, web_classes, in_reach, layer, channels, now):
    """Save a pair's histogram files in its folder."""
    write_json(Path(folder) / "histogram.json", histogram_row(pair_id, site_id, web_change, web_classes, in_reach), now)
    if channels:
        write_json(Path(folder) / "channel_histogram.json",
                   channel_histogram_row(pair_id, site_id, web_change, web_classes, in_reach, channels, layer), now, LINE_LICENSE)


def backfill(site_id, data_folder=DATA_FOLDER):
    """Write the files for a site's published pairs, and stop if the result disagrees with the value grid."""
    # Imported here because export.py imports this file to write the same files for a new pair.
    from mrw.download import read_crop
    from mrw.export import GCOV_DATASETS, GCOV_GROUP, load_land, site_bounds, web_cells_of
    from mrw.gcov import process_gcov

    config = load_site(site_id)
    site_folder = Path(data_folder) / "sites" / site_id
    bounds, land, channels, now = site_bounds(config), load_land(site_id, data_folder), read_channels(site_id, data_folder), utc_now_text()
    for path in sorted((site_folder / "pairs").iterdir()):
        pair = json.loads((path / "pair.json").read_text(encoding="utf-8"))["data"]
        # A crop that's saved is read from the disk, and with no url nothing else can be fetched.
        names = [row["granule_id"] for row in pair["passes"]]
        crops = [read_crop(name, None, GCOV_GROUP, GCOV_DATASETS, bounds) for name in names]
        result = process_gcov(crops[0], crops[1], land)
        layer = next(item for item in pair["layers"] if item["kind"] == "new_material")
        web_classes = np.fromfile(path / layer["grid_path"], dtype="uint8").reshape(layer["grid_height"], layer["grid_width"])
        web_change, in_reach = web_cells_of(result, config)
        row = histogram_row(pair["id"], site_id, web_change, web_classes, in_reach)
        # Every flagged cell passes the line, and every cell that passes the line is flagged.
        chosen = checked_cells(web_change, web_classes, in_reach)
        past_line = int(np.count_nonzero(np.abs(web_change[chosen]) >= pair["brightness_threshold_db"]))
        total_flagged = int(np.count_nonzero(np.isin(web_classes, (LOW, HIGH))))
        if not row["flagged_cells"] == past_line == total_flagged:
            raise ValueError(f"{pair['id']}: flagged {row['flagged_cells']}, past the line {past_line}, in the grid {total_flagged}")
        write_histograms(path, pair["id"], site_id, web_change, web_classes, in_reach, layer, channels, now)
        print(f"{pair['id']}: {row['total_cells']} cells, {row['flagged_share']:.2%} flagged")


if __name__ == "__main__":
    backfill(sys.argv[1])

"""Decision prep for T-036: does brightness change show each candidate event in real data?

Run from the project folder:
    python pipeline/reports/second_site_probe.py

Reads a small crop around each event, for the pair spanning it and the pair before, and
measures land flagged by brightness change at a few test levels. Coherence isn't used.
Water isn't masked, and the test box is a rough one. This only says whether a change
stands out: it doesn't test the full method, and it doesn't choose a site.
"""
import json
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import box

REPORTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPORTS.parent))

from mrw.download import read_crop, total_bytes_logged
from mrw.gcov import GCOV_DATASETS, GCOV_GROUP, HAS_VALUE, process_gcov
from mrw.pairs import build_track_pairs
from mrw.search import search_gcov, search_gunw

LEVELS_DB = (3.0, 4.0, 5.0)
# name: (west, south, east, north), the pair spanning the event, and the pair just before.
PROBES = {
    "Azuero Peninsula, Panama, track 4": ((-80.92, 7.43, -80.81, 7.53), "x_A004F005_20260930_20261012"),
    "Azuero Peninsula, Panama, track 40": ((-80.92, 7.43, -80.81, 7.53), "x_D040F085_20261002_20261014"),
    "Azuero Peninsula, Panama, track 76": ((-80.92, 7.43, -80.81, 7.53), "x_A076F005_20261005_20261017"),
    "Azuero Peninsula, Panama, track 141": ((-80.92, 7.43, -80.81, 7.53), "x_D141F085_20260927_20261009"),
    "Fuego, Guatemala": ((-90.94, 14.42, -90.82, 14.52), "x_A134F009_20260717_20260810"),
    "Nyamulagira, DR Congo": ((29.12, -1.48, 29.27, -1.35), "x_A014F001_20260721_20260814"),
}
START = "2026-06-01"


def measure(pair, bounds):
    """Return the share of pixels with a value, and km² flagged at each test level."""
    crops = [read_crop(p["granule_id"], p["url"], GCOV_GROUP, GCOV_DATASETS, bounds) for p in (pair["before"], pair["after"])]
    result = process_gcov(crops[0], crops[1], box(*bounds))
    good = result["reasons"] == HAS_VALUE
    cell_km2 = result["spacing_x_m"] * result["spacing_y_m"] / 1e6
    change = np.abs(result["change_db"][good])
    return {"pair": pair["id"].removeprefix("x_"), "valid_share": round(float(good.mean()), 3),
            "pixel_spacing_m": result["spacing_x_m"], "valid_km2": round(float(good.sum()) * cell_km2, 1),
            "median_change_db": round(float(np.nanmedian(result["change_db"][good])), 2) if good.any() else None,
            "flagged_km2": {str(level): round(float(np.count_nonzero(change >= level)) * cell_km2, 2) for level in LEVELS_DB}}


def main():
    results = {}
    start_bytes = total_bytes_logged()
    for name, (bounds, pair_id) in PROBES.items():
        config = dict(zip(("bounds_west", "bounds_south", "bounds_east", "bounds_north"), bounds))
        passes = search_gcov(config, START)
        pairs = {p["id"]: p for p in build_track_pairs("x", passes, search_gunw(config, START))}
        event = pairs[pair_id]
        results[name] = {"bounds": bounds, "event_pair": measure(event, bounds),
                         "pair_before": measure(event["previous"], bounds) if event["previous"] else None}
        print(name, json.dumps(results[name]), flush=True)
    results["bytes_fetched"] = total_bytes_logged() - start_bytes
    (REPORTS / "second-site-probe.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    print("GB fetched", round(results["bytes_fetched"] / 1e9, 3))


if __name__ == "__main__":
    main()

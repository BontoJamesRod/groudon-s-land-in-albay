"""T-035 draft: did the app flag new material on the gullies PHIVOLCS named in July 2026?

Run from the project folder:
    python pipeline/reports/july_gully_check.py

Only one gully has a named line in OSM, and the channel source isn't chosen, so each gully
is checked as a coarse wedge of its reported flank, out to its reported length. July pairs
are compared with quiet pairs in the same wedge, using the PROVISIONAL thresholds from the
config. It reads cached crops only, and shouldn't download anything.
"""
import json
import sys
from pathlib import Path

import numpy as np
from pyproj import Transformer

REPORTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPORTS.parent))
sys.path.insert(0, str(REPORTS))

from threshold_study_night_1 import PAIRS, read_pair

from mrw.classify import HIGH, LOW, classify
from mrw.config import load_site
from mrw.export import SEARCH_START, load_land, site_bounds
from mrw.gcov import HAS_VALUE
from mrw.pairs import build_track_pairs
from mrw.search import search_gcov, search_gunw

# name: (flank's compass bearing from the summit, half-width in degrees, reach in km).
# Flanks are from search summaries of the reports; reach is the longest reported lava flow.
GULLIES = {"Basud": (90, 30, 4.0), "Bonga": (135, 30, 3.2), "Mi-isi": (180, 30, 2.1)}


def bearings_and_distances(result, config):
    """Work out each pixel's compass bearing and distance from the summit."""
    to_utm = Transformer.from_crs(4326, result["epsg"], always_xy=True)
    x0, y0 = to_utm.transform(config["summit_lon"], config["summit_lat"])
    xs, ys = np.meshgrid(result["x"], result["y"])
    east, north = xs - x0, ys - y0
    return np.degrees(np.arctan2(east, north)) % 360, np.hypot(east, north) / 1000


def wedge_numbers(classes, reasons, bearing, distance, gully, cell_km2):
    """Measure one wedge: flagged area, and the share of its pixels with no radar value."""
    middle, half_width, reach = GULLIES[gully]
    inside = (np.abs((bearing - middle + 180) % 360 - 180) <= half_width) & (distance <= reach)
    return {"flagged_km2": round(float(np.count_nonzero(inside & np.isin(classes, (LOW, HIGH)))) * cell_km2, 3),
            "high_km2": round(float(np.count_nonzero(inside & (classes == HIGH))) * cell_km2, 3),
            "wedge_km2": round(float(np.count_nonzero(inside)) * cell_km2, 2),
            "no_value_share": round(float(np.count_nonzero(inside & (reasons != HAS_VALUE))) / np.count_nonzero(inside), 4)}


def flagged_clusters(classes, bearing, distance, cell_km2):
    """Show where flagged land sits around the summit, in 30-degree slices within 8 km."""
    slices = {}
    near = distance <= 8
    for start in range(0, 360, 30):
        inside = near & (bearing >= start) & (bearing < start + 30)
        slices[start] = round(float(np.count_nonzero(inside & np.isin(classes, (LOW, HIGH)))) * cell_km2, 3)
    return slices


def main():
    config = load_site("mayon")
    bounds, land = site_bounds(config), load_land("mayon")
    pairs = {p["id"]: p for p in build_track_pairs("mayon", search_gcov(config, SEARCH_START),
                                                   search_gunw(config, SEARCH_START))}
    thresholds = config["thresholds"]
    records = []
    for pair_key, kind in PAIRS.items():
        result, loss = read_pair(pairs[pair_key], bounds, land)
        classes = classify(result["change_db"], loss, result["reasons"],
                           thresholds["brightness_threshold_db"], thresholds["coherence_loss_threshold"])
        bearing, distance = bearings_and_distances(result, config)
        cell_km2 = result["spacing_x_m"] * result["spacing_y_m"] / 1e6
        record = {"id": pair_key, "kind": kind, "thresholds": "PROVISIONAL",
                  "gullies": {g: wedge_numbers(classes, result["reasons"], bearing, distance, g, cell_km2) for g in GULLIES},
                  "flagged_by_bearing_within_8_km": flagged_clusters(classes, bearing, distance, cell_km2)}
        records.append(record)
        print(pair_key.removeprefix("mayon_"), kind, {g: v["flagged_km2"] for g, v in record["gullies"].items()},
              record["flagged_by_bearing_within_8_km"], flush=True)
    (REPORTS / "july-gully-check.json").write_text(json.dumps(records, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

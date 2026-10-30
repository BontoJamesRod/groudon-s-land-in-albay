"""Task T-016, analysis only: measure what candidate thresholds would flag.

Run from the project folder:
    python pipeline/reports/threshold_study_night_1.py

It writes threshold-study-night-1.json and the figures next to this file. It uses
only pairs from before 2026-10-30 and doesn't pick the final values or change any
setting: that decision is the owner's.
"""
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
from pyproj import Transformer

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPORTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPORTS.parent))

from mrw.classify import HIGH, LOW, areas_km2, classify
from mrw.coherence import GUNW_DATASETS, GUNW_GROUP, compute_coherence_loss
from mrw.config import load_site
from mrw.download import read_crop, total_bytes_logged
from mrw.export import SEARCH_START, load_land, site_bounds
from mrw.gcov import GCOV_DATASETS, GCOV_GROUP, HAS_VALUE, process_gcov
from mrw.pairs import build_track_pairs
from mrw.search import search_gcov, search_gunw

# Kind of pair: "quiet" has no recorded event, "july" spans the 2026-07-14 event.
PAIRS = {
    "mayon_A111F008_20260820_20260901": "quiet",
    "mayon_A111F008_20260913_20260925": "quiet",
    "mayon_A111F008_20260925_20261007": "quiet",
    "mayon_A111F008_20261007_20261019": "quiet",
    "mayon_A039F008_20260908_20260920": "quiet",
    "mayon_A039F008_20260920_20261002": "quiet",
    "mayon_D104F082_20260913_20260925": "quiet",
    "mayon_A111F008_20260703_20260715": "july",
    "mayon_A039F008_20260710_20260722": "july",
    "mayon_D104F082_20260703_20260715": "july",
}
BRIGHTNESS_CANDIDATES = (2.0, 3.0, 4.0, 5.0, 6.0)
LOSS_CANDIDATES = (0.2, 0.3, 0.4, 0.5)
PERCENTILES = (50, 90, 95, 99, 99.9)
MAP_PAIRS = ("mayon_A039F008_20260710_20260722", "mayon_A111F008_20260703_20260715",
             "mayon_A039F008_20260920_20261002", "mayon_A111F008_20261007_20261019")
MAP_BRIGHTNESS, MAP_LOSS = 3.0, 0.3  # the PROVISIONAL values, shown for comparison only
NEUTRAL = "#8C8C8C"
ACCENT = "#D55E00"
INK = "#1F2328"


def danger_zone_mask(result, config):
    """Mark the pixels within the danger-zone radius of the summit."""
    to_utm = Transformer.from_crs(4326, result["epsg"], always_xy=True)
    x0, y0 = to_utm.transform(config["summit_lon"], config["summit_lat"])
    xs, ys = np.meshgrid(result["x"], result["y"])
    return np.hypot(xs - x0, ys - y0) <= config["danger_zone_radius_km"] * 1000


def read_pair(pair, bounds, land):
    """Read and process one pair. Coherence loss is None if a GUNW is missing."""
    crops = [read_crop(p["granule_id"], p["url"], GCOV_GROUP, GCOV_DATASETS, bounds)
             for p in (pair["before"], pair["after"])]
    result = process_gcov(crops[0], crops[1], land)
    previous = pair["previous"]["gunw"] if pair["previous"] else None
    gunw_crops = [read_crop(g["granule_id"], g["url"], GUNW_GROUP, GUNW_DATASETS, bounds) if g else None
                  for g in (previous, pair["gunw"])]
    loss = compute_coherence_loss(gunw_crops[0], gunw_crops[1], result["x"], result["y"], result["epsg"])
    return result, loss


def summarize_candidates(result, loss, in_zone):
    """Work out how much land each candidate pair of thresholds would flag."""
    rows = []
    spacing = (result["spacing_x_m"], result["spacing_y_m"])
    for brightness in BRIGHTNESS_CANDIDATES:
        for loss_value in LOSS_CANDIDATES:
            classes = classify(result["change_db"], loss, result["reasons"], brightness, loss_value)
            zone_classes = np.where(in_zone, classes, 255).astype("uint8")
            rows.append({"brightness_db": brightness, "coherence_loss": loss_value,
                         **areas_km2(classes, *spacing),
                         "zone_high_km2": areas_km2(zone_classes, *spacing)["high_confidence_area_km2"],
                         "zone_low_km2": areas_km2(zone_classes, *spacing)["low_confidence_area_km2"]})
    return rows


def histogram(values, edges):
    """Return the share of pixels in each bin, as a percentage."""
    counts, _ = np.histogram(values, bins=edges)
    return (100.0 * counts / max(len(values), 1)).tolist()


def study_pair(pair, kind, bounds, land, config):
    """Measure one pair and return its numbers, plus its class grid for the maps."""
    result, loss = read_pair(pair, bounds, land)
    has_value = result["reasons"] == HAS_VALUE
    change = np.abs(result["change_db"][has_value])
    in_zone = danger_zone_mask(result, config)
    record = {
        "id": pair["id"], "kind": kind, "coherence_available": loss is not None,
        "land_km2": round(float(has_value.sum()) * result["spacing_x_m"] * result["spacing_y_m"] / 1e6, 1),
        "median_change_db": round(float(np.nanmedian(result["change_db"][has_value])), 3),
        "abs_change_percentiles": {str(p): round(float(np.nanpercentile(change, p)), 2) for p in PERCENTILES},
        "abs_change_hist": histogram(change, np.arange(0, 12.01, 0.25)),
        "candidates": summarize_candidates(result, loss, in_zone),
    }
    if loss is not None:
        values = loss[has_value]
        values = values[np.isfinite(values)]
        record["loss_percentiles"] = {str(p): round(float(np.percentile(values, p)), 3) for p in PERCENTILES}
        record["loss_hist"] = histogram(values, np.arange(-1, 1.01, 0.05))
    classes = classify(result["change_db"], loss, result["reasons"], MAP_BRIGHTNESS, MAP_LOSS)
    return record, classes[::4, ::4]


def style(axis, title, xlabel, ylabel):
    """Quiet axes: thin grid and no box, so the data stands out."""
    axis.set_title(title, loc="left", color=INK, fontsize=11)
    axis.set_xlabel(xlabel, color=INK)
    axis.set_ylabel(ylabel, color=INK)
    axis.grid(color="#E6E6E6", linewidth=0.8)
    axis.set_axisbelow(True)
    for side in ("top", "right"):
        axis.spines[side].set_visible(False)


def plot_histograms(records, key, edges, title, xlabel, path):
    """Draw every pair's histogram: quiet pairs gray, July pairs in the accent color."""
    figure, axis = plt.subplots(figsize=(8, 4.5))
    centres = (edges[:-1] + edges[1:]) / 2
    labelled = set()
    for record in sorted(records, key=lambda r: r["kind"] == "july"):
        if key not in record:
            continue
        july = record["kind"] == "july"
        label = "Spans 2026-07-14" if july else "Quiet pair"
        axis.plot(centres, record[key], color=ACCENT if july else NEUTRAL, linewidth=2 if july else 1.2,
                  label=None if label in labelled else label)
        labelled.add(label)
    axis.set_yscale("log")
    style(axis, title, xlabel, "Share of land pixels (%, log scale)")
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(path, dpi=110)
    plt.close(figure)


def plot_flagged(records, path):
    """Show the land flagged by brightness alone at each candidate, for every pair."""
    figure, axis = plt.subplots(figsize=(8, 4.5))
    labelled = set()
    for record in sorted(records, key=lambda r: r["kind"] == "july"):
        # Brightness alone is the part that doesn't depend on a coherence baseline.
        rows = [r for r in record["candidates"] if r["coherence_loss"] == LOSS_CANDIDATES[-1]]
        july = record["kind"] == "july"
        label = "Spans 2026-07-14" if july else "Quiet pair"
        axis.plot([r["brightness_db"] for r in rows], [max(r["new_material_area_km2"], 0.01) for r in rows],
                  color=ACCENT if july else NEUTRAL, linewidth=2 if july else 1.2, marker="o", markersize=4,
                  label=None if label in labelled else label)
        labelled.add(label)
    axis.set_yscale("log")
    style(axis, "Land flagged at each brightness threshold (coherence-loss threshold 0.5)",
          "Brightness threshold (dB)", "Flagged land (km², log scale)")
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(path, dpi=110)
    plt.close(figure)


def plot_maps(grids, path):
    """Show where the PROVISIONAL values flag land, for two July and two quiet pairs."""
    figure, axes = plt.subplots(2, 2, figsize=(10, 10))
    for axis, pair_key in zip(axes.flat, MAP_PAIRS):
        grid = grids[pair_key]
        picture = np.full(grid.shape + (3,), 255, dtype="uint8")
        picture[grid == 0] = (230, 230, 230)
        picture[grid == LOW] = (230, 159, 0)
        picture[grid == HIGH] = (213, 94, 0)
        axis.imshow(picture)
        axis.set_title(pair_key.removeprefix("mayon_"), fontsize=10, loc="left", color=INK)
        axis.set_xticks([])
        axis.set_yticks([])
    figure.suptitle("Flagged at the PROVISIONAL values: orange low, vermillion high, white no data", color=INK)
    figure.tight_layout()
    figure.savefig(path, dpi=90)
    plt.close(figure)


def main():
    config = load_site("mayon")
    bounds, land = site_bounds(config), load_land("mayon")
    pairs = {p["id"]: p for p in build_track_pairs("mayon", search_gcov(config, SEARCH_START),
                                                   search_gunw(config, SEARCH_START))}
    records, grids = [], {}
    for pair_key, kind in PAIRS.items():
        print("Studying", pair_key, flush=True)
        record, grid = study_pair(pairs[pair_key], kind, bounds, land, config)
        records.append(record)
        if pair_key in MAP_PAIRS:
            grids[pair_key] = grid
    output = {"status": "analysis only; no thresholds chosen", "bytes_logged_total": total_bytes_logged(),
              "pairs": records}
    (REPORTS / "threshold-study-night-1.json").write_text(json.dumps(output, indent=1), encoding="utf-8")
    plot_histograms(records, "abs_change_hist", np.arange(0, 12.01, 0.25), "Absolute brightness change on land",
                    "Absolute brightness change (dB)", REPORTS / "threshold-study-brightness-hist.png")
    plot_histograms(records, "loss_hist", np.arange(-1, 1.01, 0.05), "Coherence loss on land",
                    "Coherence loss", REPORTS / "threshold-study-coherence-hist.png")
    plot_flagged(records, REPORTS / "threshold-study-flagged-area.png")
    plot_maps(grids, REPORTS / "threshold-study-maps.png")
    print("Done. GB logged:", round(total_bytes_logged() / 1e9, 3))


if __name__ == "__main__":
    main()

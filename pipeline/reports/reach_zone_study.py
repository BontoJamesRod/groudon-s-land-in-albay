"""Afternoon run: split Oct 8 -> Oct 20 by radar signal, and test masks on every pair.

Run from the project folder:
    python pipeline/reports/reach_zone_study.py

It uses only cached radar crops and published grids from before 2026-10-30, and should
download no radar data. Thresholds are the PROVISIONAL values from the site config. The
masks are tested here: they are not pipeline settings, and nothing here changes a default.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPORTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPORTS.parent))
sys.path.insert(0, str(REPORTS))

from false_alarm_study import (CACHE, CROPLAND, JULY_PAIR, STEEP_DEGREES, angle_apart, cell_sizes_m, flagged_km2,
                               grid_axes, gully_masks, load_pairs, short_name, slope_and_aspect)
from threshold_study_night_1 import read_pair

from mrw.classify import HIGH, LOW
from mrw.config import load_site
from mrw.download import total_bytes_logged
from mrw.export import SEARCH_START, load_land, lookup_web_cells, site_bounds
from mrw.filters import remove_small_clusters
from mrw.gcov import HAS_VALUE
from mrw.pairs import build_track_pairs
from mrw.search import search_gcov, search_gunw

OCTOBER_PAIR = "mayon_A111F008_20261007_20261019"
REACH_KM = (8, 10, 12)
CLUSTER_M2 = 2000
# Pass geometry, from the product's metadata: ascending and left-looking, so the radar is to
# the east-northeast. The beam's angle isn't read from the product: 40 degrees is an assumed
# mid-swath value, used only for the local-angle figure.
TOWARD_RADAR_DEGREES = 77
ASSUMED_INCIDENCE_DEGREES = 40
AWAY_WITHIN_DEGREES = 60
GRAZING_DEGREES = 70
# An assumed noise level, not one read from the product. Other levels are in the report.
NOISE_DB = -20
NOISE_LEVELS_DB = (-25, -22, -20, -18)
ONLY_BRIGHTNESS, ONLY_COHERENCE, BOTH = 1, 2, 3
SIGNAL_NAMES = {ONLY_BRIGHTNESS: "Brightness only", ONLY_COHERENCE: "Coherence only", BOTH: "Both"}
SIGNAL_COLORS = {ONLY_BRIGHTNESS: "#E69F00", ONLY_COHERENCE: "#0072B2", BOTH: "#D55E00"}


def signal_split(result, loss, thresholds):
    """Label each land cell by which signals pass. The same tests as classify()."""
    has_value = result["reasons"] == HAS_VALUE
    with np.errstate(invalid="ignore"):
        bright = np.abs(result["change_db"]) >= thresholds["brightness_threshold_db"]
        decorrelated = loss >= thresholds["coherence_loss_threshold"]
    labels = np.zeros(has_value.shape, dtype="uint8")
    labels[has_value & bright & ~decorrelated] = ONLY_BRIGHTNESS
    labels[has_value & ~bright & decorrelated] = ONLY_COHERENCE
    labels[has_value & bright & decorrelated] = BOTH
    return labels


def to_web_grid(values, result, bounds, empty):
    """Sample a radar-grid array onto the published 20 m web grid, as export.py does."""
    rows, columns, inside = lookup_web_cells(result["x"], result["y"], result["epsg"], bounds)
    web = values[rows, columns]
    web[~inside] = empty
    return web


def faintest_db(result):
    """Each cell's lower brightness of the two passes, where a return may be near the noise."""
    with np.errstate(invalid="ignore"):
        return np.fmin(result["before_db"], result["after_db"])


def local_angle(slope, aspect):
    """The beam's angle to the ground's perpendicular. Past 90 degrees is radar shadow."""
    incidence = np.radians(ASSUMED_INCIDENCE_DEGREES)
    tilt = np.radians(slope)
    cosine = np.cos(tilt) * np.cos(incidence) + np.sin(tilt) * np.sin(incidence) * np.cos(np.radians(aspect - TOWARD_RADAR_DEGREES))
    return np.degrees(np.arccos(np.clip(cosine, -1, 1)))


def split_rows(labels, zone, northwest, away, grazing, faint, cell_km2):
    """Measure each signal's area in the danger zone, and how much is on hard ground."""
    rows = {}
    for code, name in SIGNAL_NAMES.items():
        cells = zone & (labels == code)
        rows[name] = {"km2": round(float(np.count_nonzero(cells)) * cell_km2, 3),
                      "northwest_km2": round(float(np.count_nonzero(cells & northwest)) * cell_km2, 3),
                      "away_slope_km2": round(float(np.count_nonzero(cells & away)) * cell_km2, 3),
                      "grazing_km2": round(float(np.count_nonzero(cells & grazing)) * cell_km2, 3),
                      "near_noise_km2": {str(level): round(float(np.count_nonzero(cells & (faint <= level))) * cell_km2, 3)
                                         for level in NOISE_LEVELS_DB}}
    return rows


def figure_split(labels, lons, lats, config, rows, away, path):
    """Map of the danger zone: one color per signal, away-facing slopes shaded."""
    east = (lons - config["summit_lon"]) * 111.32 * np.cos(np.radians(config["summit_lat"]))
    north = (lats - config["summit_lat"]) * 111.32
    extent = (east[0], east[-1], north[-1], north[0])
    figure, axis = plt.subplots(figsize=(7.4, 7.8))
    axis.set_facecolor("#F3F4F6")
    shade = np.zeros(labels.shape + (4,), dtype="float32")
    shade[away] = matplotlib.colors.to_rgba("#6E7781", 0.28)
    axis.imshow(shade, extent=extent, interpolation="nearest")
    picture = np.zeros(labels.shape + (4,), dtype="float32")
    for code, color in SIGNAL_COLORS.items():
        picture[labels == code] = matplotlib.colors.to_rgba(color)
    axis.imshow(picture, extent=extent, interpolation="nearest")
    axis.add_patch(plt.Circle((0, 0), config["danger_zone_radius_km"], fill=False, color="#1F2328", linewidth=1.2, linestyle="--"))
    axis.plot(0, 0, marker="^", color="#1F2328", markersize=8)
    axis.annotate("Summit", (0, 0), xytext=(8, 6), textcoords="offset points", fontsize=9)
    limit = config["danger_zone_radius_km"] + 0.5
    axis.set_xlim(-limit, limit)
    axis.set_ylim(-limit, limit)
    axis.set_aspect("equal")
    axis.set_xlabel("km east of the summit")
    axis.set_ylabel("km north of the summit")
    axis.set_title("Oct 8 to Oct 20, 2026: which signal flagged each cell\n"
                   "(dashed: 6 km danger zone. PROVISIONAL thresholds)", loc="left", fontsize=11)
    handles = [plt.Line2D([], [], marker="s", linestyle="", markersize=9, color=SIGNAL_COLORS[code],
                          label=f"{name}: {rows[name]['km2']:.2f} km²") for code, name in SIGNAL_NAMES.items()]
    handles.append(plt.Line2D([], [], marker="s", linestyle="", markersize=9, color="#6E7781", alpha=0.45,
                              label="Steep, facing away from the radar"))
    axis.legend(handles=handles, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2)
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    figure.savefig(path, dpi=130)
    plt.close(figure)


def mask_options(distance, away):
    """Name each mask: a function from a pair's near-noise cells to the cells it clears."""
    options = {"No mask": lambda faint: None}
    for reach in REACH_KM:
        options[f"Within {reach} km"] = lambda faint, reach=reach: distance > reach
    options["Noise floor and away-facing slopes"] = lambda faint: away | (faint <= NOISE_DB)
    return options


def apply_mask(classes, cleared, with_clusters, cell_m2):
    """Clear masked detections, then optionally drop small patches.

    The mask comes first, so a patch cut by a mask is measured by what's left of it.
    """
    result = classes.copy()
    if cleared is not None:
        result[cleared & np.isin(classes, (LOW, HIGH))] = 0
    return remove_small_clusters(result, CLUSTER_M2, cell_m2) if with_clusters else result


def mask_table(pairs, faint_by_pair, masks, distance, away, cover, cell_m2):
    """Measure every mask, alone and with clusters, on every pair."""
    cell_km2 = cell_m2 / 1e6
    table = {}
    for name, cleared_for in mask_options(distance, away).items():
        for with_clusters in (False, True):
            label = f"{name} + clusters from {CLUSTER_M2:,} m²" if with_clusters else name
            rows = {}
            for pair in pairs:
                grid = apply_mask(pair["classes"], cleared_for(faint_by_pair[pair["id"]]), with_clusters, cell_m2)
                flagged = np.isin(grid, (LOW, HIGH))
                rows[pair["id"]] = {"total_km2": round(flagged_km2(grid, cell_km2), 3),
                                    "cropland_km2": round(float(np.count_nonzero(flagged & (cover == CROPLAND))) * cell_km2, 3),
                                    "flanks_km2": round(sum(flagged_km2(grid, cell_km2, mask) for mask in masks.values()), 3)}
            table[label] = rows
    return table


def summarize(table):
    """The quiet set leaves out both the July pair and Oct 8 to Oct 20."""
    summary = {}
    for name, rows in table.items():
        quiet = [row for key, row in rows.items() if key not in (JULY_PAIR, OCTOBER_PAIR)]
        quiet_total = sum(row["total_km2"] for row in quiet)
        summary[name] = {"quiet_pairs": len(quiet), "quiet_mean_km2": round(quiet_total / len(quiet), 3),
                         "quiet_max_km2": max(row["total_km2"] for row in quiet),
                         "quiet_cropland_share": round(sum(row["cropland_km2"] for row in quiet) / max(quiet_total, 1e-9), 3),
                         "quiet_flanks_max_km2": max(row["flanks_km2"] for row in quiet),
                         "july_total_km2": rows[JULY_PAIR]["total_km2"], "july_flanks_km2": rows[JULY_PAIR]["flanks_km2"],
                         "october_total_km2": rows[OCTOBER_PAIR]["total_km2"]}
    base = summary["No mask"]
    for row in summary.values():
        row["quiet_removed_percent"] = round(100 * (1 - row["quiet_mean_km2"] / base["quiet_mean_km2"]))
        row["july_flanks_kept_percent"] = round(100 * row["july_flanks_km2"] / base["july_flanks_km2"])
        row["july_total_kept_percent"] = round(100 * row["july_total_km2"] / base["july_total_km2"])
        row["october_kept_percent"] = round(100 * row["october_total_km2"] / base["october_total_km2"])
    return summary


def main():
    config = load_site("mayon")
    bounds, land = site_bounds(config), load_land("mayon")
    logged_before = total_bytes_logged()
    found = {p["id"]: p for p in build_track_pairs("mayon", search_gcov(config, SEARCH_START), search_gunw(config, SEARCH_START))}
    pairs = load_pairs()
    layer = pairs[0]["layer"]
    lons, lats = grid_axes(layer)
    masks, distance, bearing = gully_masks(lons, lats, config)
    cell_x, cell_y = cell_sizes_m(layer)
    cell_m2 = cell_x * cell_y
    cell_km2 = cell_m2 / 1e6
    slope, aspect = slope_and_aspect(np.load(CACHE / "dem.npy"), cell_x, cell_y)
    cover = np.load(CACHE / "worldcover.npy")
    away = (slope >= STEEP_DEGREES) & (angle_apart(aspect, TOWARD_RADAR_DEGREES + 180) <= AWAY_WITHIN_DEGREES)
    grazing = local_angle(slope, aspect) >= GRAZING_DEGREES
    zone = distance <= config["danger_zone_radius_km"]
    northwest = (bearing >= 270) & (bearing < 360)
    land_cells = pairs[0]["classes"] != 254
    geometry = {"zone_land_km2": round(float(np.count_nonzero(zone & land_cells)) * cell_km2, 2),
                "zone_away_km2": round(float(np.count_nonzero(zone & land_cells & away)) * cell_km2, 2),
                "zone_grazing_km2": round(float(np.count_nonzero(zone & land_cells & grazing)) * cell_km2, 2),
                "shadow_km2_at_assumed_angle": round(float(np.count_nonzero(zone & land_cells & (local_angle(slope, aspect) >= 90))) * cell_km2, 3)}
    splits, faint_by_pair = {}, {}
    for pair in pairs:
        result, loss = read_pair(found[pair["id"]], bounds, land)
        faint = to_web_grid(faintest_db(result).astype("float64"), result, bounds, np.nan)
        faint_by_pair[pair["id"]] = faint
        if loss is None:
            splits[short_name(pair["id"])] = None
            continue
        labels = to_web_grid(signal_split(result, loss, config["thresholds"]), result, bounds, 0)
        rows = split_rows(labels, zone, northwest, away, grazing, faint, cell_km2)
        # With unequal gaps the app ignores coherence, so these numbers aren't on the map.
        rows["app_uses_coherence"] = pair["record"]["coherence_used"]
        rows["zone_faint_median_db"] = round(float(np.nanmedian(faint[zone & land_cells])), 1)
        splits[short_name(pair["id"])] = rows
        if pair["id"] == OCTOBER_PAIR:
            figure_split(labels, lons, lats, config, rows, away, REPORTS / "october-signal-split.png")
    table = mask_table(pairs, faint_by_pair, masks, distance, away, cover, cell_m2)
    summary = summarize(table)
    logged = total_bytes_logged() - logged_before
    out = {"note": "PROVISIONAL thresholds. Analysis only: no filter, mask or threshold was chosen.",
           "bytes_downloaded": logged, "assumed": {"noise_db": NOISE_DB, "incidence_degrees": ASSUMED_INCIDENCE_DEGREES},
           "danger_zone_geometry": geometry, "danger_zone_split": splits, "masks_by_pair": table, "masks_summary": summary}
    (REPORTS / "reach-zone-study.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("bytes downloaded", logged)
    print(json.dumps(geometry))
    print(json.dumps(splits, ensure_ascii=False))
    for name, row in summary.items():
        print(name, {key: row[key] for key in ("quiet_mean_km2", "quiet_max_km2", "quiet_removed_percent", "quiet_cropland_share", "july_total_km2", "july_flanks_km2", "july_flanks_kept_percent", "quiet_flanks_max_km2", "october_total_km2", "october_kept_percent")})


if __name__ == "__main__":
    main()

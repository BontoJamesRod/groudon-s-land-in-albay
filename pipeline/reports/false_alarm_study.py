"""False-alarm study (adds to T-016): where do the detections on quiet pairs fall, and what
would each optional filter remove?

Run from the project folder:
    python pipeline/reports/false_alarm_study.py

It reads the published grids in site/data, which are all from before 2026-10-30. Land cover
(ESA WorldCover) and elevation (Copernicus DEM) are read once as small windows and cached in
raw/. They are context only: nothing here changes a default, a threshold or a published file.
Thresholds in the grids are the PROVISIONAL values from the site config.
"""
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from scipy import ndimage

REPORTS = Path(__file__).resolve().parent
REPO = REPORTS.parents[1]
sys.path.insert(0, str(REPORTS.parent))
sys.path.insert(0, str(REPORTS))

from july_gully_check import GULLIES

from mrw.classify import HIGH, LOW
from mrw.config import load_site
from mrw.filters import apply_filters

DATA = REPO / "site" / "data" / "sites" / "mayon"
CACHE = REPO / "raw" / "context_download" / "false_alarm"
WORLDCOVER_URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N12E123_Map.tif"
DEM_URL = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N13_00_E123_00_DEM/Copernicus_DSM_COG_10_N13_00_E123_00_DEM.tif"
JULY_PAIR = "mayon_A111F008_20260703_20260715"
SEA_CODE = 254
CROPLAND, BUILT_UP = 40, 50  # ESA WorldCover class codes
STEEP_DEGREES = 20
FACING_WITHIN_DEGREES = 60
COAST_METRES = 500
DANGER_ZONE_KM = 6
PLACES = ["Steep, facing the radar", "Coast", "Built-up", "Cropland", "Other"]
PLACE_COLORS = ["#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#009E73"]
FILTER_OPTIONS = {
    "No filter": {},
    "Clusters from 1,000 m²": {"min_cluster_m2": 1000},
    "Clusters from 2,000 m²": {"min_cluster_m2": 2000},
    "Clusters from 5,000 m²": {"min_cluster_m2": 5000},
    "Clusters from 10,000 m²": {"min_cluster_m2": 10000},
    "High confidence only": {"high_confidence_only": True},
    "Persists into next pair": {"persist_across_pairs": True},
    "Persists + clusters from 1,000 m²": {"persist_across_pairs": True, "min_cluster_m2": 1000},
    "Persists + clusters from 2,000 m²": {"persist_across_pairs": True, "min_cluster_m2": 2000},
    "High only + clusters from 1,000 m²": {"high_confidence_only": True, "min_cluster_m2": 1000},
}


def read_json_data(path):
    return json.loads(path.read_text(encoding="utf-8"))["data"]


def load_pairs():
    """Read every published pair's class grid, oldest first."""
    pairs = []
    for row in read_json_data(DATA / "pairs.json"):
        folder = DATA / "pairs" / row["id"]
        record = read_json_data(folder / "pair.json")
        layer = next(item for item in record["layers"] if item["kind"] == "new_material")
        cells = np.frombuffer((folder / layer["grid_path"]).read_bytes(), dtype="uint8")
        pairs.append({"id": row["id"], "record": record, "layer": layer,
                      "classes": cells.reshape(layer["grid_height"], layer["grid_width"])})
    return pairs


def read_window(url, name, bounds, shape, resampling):
    """Read one source onto the site's grid, once, and keep it in raw/."""
    path = CACHE / f"{name}.npy"
    if path.is_file():
        return np.load(path)
    CACHE.mkdir(parents=True, exist_ok=True)
    with rasterio.open(url) as source:
        window = from_bounds(*bounds, source.transform)
        values = source.read(1, window=window, out_shape=shape, resampling=resampling, boundless=True)
    np.save(path, values)
    return values


def grid_axes(layer):
    """Return each column's longitude and each row's latitude. Row 0 is the north edge."""
    width, height = layer["grid_width"], layer["grid_height"]
    west, east, south, north = (layer[f"bounds_{side}"] for side in ("west", "east", "south", "north"))
    lons = west + (np.arange(width) + 0.5) * (east - west) / width
    lats = north - (np.arange(height) + 0.5) * (north - south) / height
    return lons, lats


def cell_sizes_m(layer):
    """Return one cell's (east-west, north-south) size in metres at the site's latitude."""
    width, height = layer["grid_width"], layer["grid_height"]
    middle = (layer["bounds_north"] + layer["bounds_south"]) / 2
    north_south = (layer["bounds_north"] - layer["bounds_south"]) / height * 111_320
    east_west = (layer["bounds_east"] - layer["bounds_west"]) / width * 111_320 * math.cos(math.radians(middle))
    return east_west, north_south


def slope_and_aspect(dem, cell_x, cell_y):
    """Work out each cell's steepness and the compass direction it faces."""
    rise_south, rise_east = np.gradient(dem.astype("float64"), cell_y, cell_x)
    slope = np.degrees(np.arctan(np.hypot(rise_east, rise_south)))
    # A slope faces downhill. Rows run north to south, so rise_south > 0 means it faces north.
    aspect = np.degrees(np.arctan2(-rise_east, rise_south)) % 360
    return slope, aspect


def angle_apart(a, b):
    return np.abs((a - b + 180) % 360 - 180)


def radar_bearing_from_brightness(slope, aspect, before_gray, land):
    """Find which way slopes look brightest: the empirical direction towards the radar.

    Reads the published "before" image, in which brighter gray means a stronger return.
    """
    steep = (slope >= STEEP_DEGREES) & land
    sectors = {}
    for middle in range(0, 360, 30):
        inside = steep & (angle_apart(aspect, middle) <= 15)
        sectors[middle] = round(float(before_gray[inside].mean()), 1)
    return sectors


def place_grid(cover, slope, aspect, classes, cell_x, cell_y, toward_radar):
    """Give each cell one place, first match wins, in the order of PLACES."""
    sea = classes == SEA_CODE
    from_sea_m = ndimage.distance_transform_edt(~sea, sampling=(cell_y, cell_x))
    steep = slope >= STEEP_DEGREES
    facing = steep & (angle_apart(aspect, toward_radar) <= FACING_WITHIN_DEGREES)
    conditions = [facing, from_sea_m <= COAST_METRES, cover == BUILT_UP, cover == CROPLAND]
    places = np.full(classes.shape, len(conditions), dtype="uint8")
    for number in reversed(range(len(conditions))):
        places[conditions[number]] = number
    return places, steep & ~facing


def areas_by_place(classes, places, cell_km2):
    """Return the area of low and high cells in each place."""
    rows = {}
    for number, name in enumerate(PLACES):
        inside = places == number
        rows[name] = {"low_km2": round(float(np.count_nonzero(inside & (classes == LOW))) * cell_km2, 3),
                      "high_km2": round(float(np.count_nonzero(inside & (classes == HIGH))) * cell_km2, 3)}
    return rows


def gully_masks(lons, lats, config):
    """Build the flank wedges from the July check, the same shapes it used."""
    east = (lons - config["summit_lon"]) * 111_320 * math.cos(math.radians(config["summit_lat"]))
    north = (lats - config["summit_lat"]) * 111_320
    east_grid, north_grid = np.meshgrid(east, north)
    bearing = np.degrees(np.arctan2(east_grid, north_grid)) % 360
    distance = np.hypot(east_grid, north_grid) / 1000
    masks = {name: (angle_apart(bearing, middle) <= half) & (distance <= reach)
             for name, (middle, half, reach) in GULLIES.items()}
    return masks, distance, bearing


def flagged_km2(classes, cell_km2, mask=None):
    flagged = np.isin(classes, (LOW, HIGH))
    if mask is not None:
        flagged = flagged & mask
    return float(np.count_nonzero(flagged)) * cell_km2


def try_filter(pair, next_pair, filters, cell_m2):
    """Apply one filter option, or return None if the next pair it needs doesn't exist."""
    if filters.get("persist_across_pairs") and next_pair is None:
        return None
    return apply_filters(pair["classes"], filters, cell_m2, next_pair["classes"] if next_pair else None)


def filter_table(pairs, masks, cell_m2):
    """Measure every filter option on every pair, overall and in the July flank wedges."""
    cell_km2 = cell_m2 / 1_000_000
    table = {}
    for name, filters in FILTER_OPTIONS.items():
        rows = {}
        for number, pair in enumerate(pairs):
            next_pair = pairs[number + 1] if number + 1 < len(pairs) else None
            result = try_filter(pair, next_pair, filters, cell_m2)
            if result is None:
                rows[pair["id"]] = None
                continue
            rows[pair["id"]] = {"total_km2": round(flagged_km2(result, cell_km2), 3),
                                "gullies_km2": {gully: round(flagged_km2(result, cell_km2, mask), 3)
                                                for gully, mask in masks.items()}}
        table[name] = rows
    return table


def mixed_option(table, pairs):
    """Measure: high confidence only where a pair has coherence, else clusters from 10,000 m².

    The site config can't say this yet, because it picks a filter per pair, not per site.
    """
    rows = {}
    for pair in pairs:
        name = "High confidence only" if pair["record"]["coherence_used"] else "Clusters from 10,000 m²"
        rows[pair["id"]] = table[name][pair["id"]]
    return rows


def short_name(pair_id):
    parts = pair_id.split("_")
    return f"{parts[2][4:6]}-{parts[2][6:]} → {parts[3][4:6]}-{parts[3][6:]}"


def figure_places(results, path):
    """Stacked bars: where each pair's detections fall."""
    names = [row["pair"] for row in results]
    figure, axis = plt.subplots(figsize=(9, 4.6))
    left = np.zeros(len(names))
    for place, color in zip(PLACES, PLACE_COLORS):
        values = np.array([row["places"][place]["low_km2"] + row["places"][place]["high_km2"] for row in results])
        axis.barh(names, values, left=left, color=color, label=place, height=0.62, edgecolor="white", linewidth=2)
        left += values
    for y_position, total in enumerate(left):
        axis.text(total + 0.15, y_position, f"{total:.2f}", va="center", fontsize=9, color="#1f2328")
    axis.invert_yaxis()
    axis.set_xlabel("Detected area, km² (PROVISIONAL thresholds)")
    axis.set_title("Where the detections fall, pair by pair", loc="left")
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.grid(axis="x", color="#e6e8eb")
    axis.set_axisbelow(True)
    axis.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.14))
    figure.tight_layout()
    figure.savefig(path, dpi=130)
    plt.close(figure)


def figure_filters(summary, path):
    """Dots: how much each filter leaves on quiet pairs, and in the July flank wedges."""
    names = list(summary)
    figure, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharey=True)
    positions = np.arange(len(names))
    panels = [("quiet_mean_km2", "Quiet pairs: mean area left, km²", "#6E7781"),
              ("july_gullies_km2", "July pair: area left in the 3 named flanks, km²", "#D55E00")]
    for axis, (key, title, color) in zip(axes, panels):
        values = [summary[name][key] for name in names]
        axis.hlines(positions, 0, values, color="#d0d7de", linewidth=2)
        axis.plot(values, positions, "o", color=color, markersize=8)
        for y_position, value in zip(positions, values):
            axis.annotate(f"{value:.3f}", (value, y_position), xytext=(6, 0), textcoords="offset points", va="center", fontsize=8)
        axis.set_title(title, loc="left", fontsize=10)
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.set_xlim(0, max(values) * 1.2)
    axes[0].set_yticks(positions, names)
    axes[0].invert_yaxis()
    figure.tight_layout()
    figure.savefig(path, dpi=130)
    plt.close(figure)


def main():
    pairs = load_pairs()
    config = load_site("mayon")
    layer = pairs[0]["layer"]
    shape = (layer["grid_height"], layer["grid_width"])
    bounds = (layer["bounds_west"], layer["bounds_south"], layer["bounds_east"], layer["bounds_north"])
    cover = read_window(WORLDCOVER_URL, "worldcover", bounds, shape, Resampling.mode)
    dem = read_window(DEM_URL, "dem", bounds, shape, Resampling.bilinear)
    cell_x, cell_y = cell_sizes_m(layer)
    cell_m2 = cell_x * cell_y
    cell_km2 = cell_m2 / 1_000_000
    slope, aspect = slope_and_aspect(dem, cell_x, cell_y)
    land = pairs[0]["classes"] != SEA_CODE
    from PIL import Image
    before_image = np.asarray(Image.open(DATA / "pairs" / JULY_PAIR / "before_db.png").convert("L"), dtype="float64")
    sectors = radar_bearing_from_brightness(slope, aspect, before_image, land)
    # The product says lookDirection Left and orbitPassDirection Ascending. Flying a little
    # west of north and looking left, the satellite sits to the east-northeast of the ground.
    toward_radar = 77
    places, steep_away = place_grid(cover, slope, aspect, pairs[0]["classes"], cell_x, cell_y, toward_radar)
    lons, lats = grid_axes(layer)
    masks, distance, bearing = gully_masks(lons, lats, config)
    northwest = (bearing >= 270) & (bearing < 360)

    land_share = {name: round(float(np.count_nonzero((places == number) & land)) / np.count_nonzero(land), 4)
                  for number, name in enumerate(PLACES)}
    results = []
    for pair in pairs:
        classes = pair["classes"]
        total = flagged_km2(classes, cell_km2)
        results.append({
            "pair": short_name(pair["id"]), "id": pair["id"], "coherence_used": pair["record"]["coherence_used"],
            "published_total_km2": pair["record"]["new_material_area_km2"], "measured_total_km2": round(total, 2),
            "places": areas_by_place(classes, places, cell_km2),
            "steep_facing_away_km2": round(flagged_km2(classes, cell_km2, steep_away & (places == len(PLACES) - 1)), 3),
            "inside_danger_zone_km2": round(flagged_km2(classes, cell_km2, distance <= DANGER_ZONE_KM), 3),
            "northwest_of_summit_in_zone_km2": round(flagged_km2(classes, cell_km2, northwest & (distance <= DANGER_ZONE_KM)), 3),
        })
    table = filter_table(pairs, masks, cell_m2)
    table["Mixed: high only with coherence, else clusters from 10,000 m²"] = mixed_option(table, pairs)
    summary = {}
    for name, rows in table.items():
        quiet = [row["total_km2"] for pair_id, row in rows.items() if pair_id != JULY_PAIR and row]
        flanks = [sum(row["gullies_km2"].values()) for pair_id, row in rows.items() if pair_id != JULY_PAIR and row]
        july = rows[JULY_PAIR]
        summary[name] = {"quiet_mean_km2": round(float(np.mean(quiet)), 3), "quiet_max_km2": round(float(max(quiet)), 3),
                         "quiet_removed_percent": None, "quiet_flanks_max_km2": round(max(flanks), 3),
                         "quiet_pairs_counted": len(quiet), "july_total_km2": july["total_km2"],
                         "july_gullies_km2": round(sum(july["gullies_km2"].values()), 3), "july_gullies": july["gullies_km2"]}
    for row in summary.values():
        row["quiet_removed_percent"] = round(100 * (1 - row["quiet_mean_km2"] / summary["No filter"]["quiet_mean_km2"]))
    out = {"note": "PROVISIONAL thresholds. Context only: nothing here is a chosen value.",
           "cell_m2": round(cell_m2, 1), "toward_radar_degrees": toward_radar, "brightness_by_facing_direction": sectors,
           "land_share": land_share, "pairs": results, "filters_by_pair": table, "filters_summary": summary}
    (REPORTS / "false-alarm-study.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    figure_places(results, REPORTS / "false-alarm-places.png")
    figure_filters(summary, REPORTS / "false-alarm-filters.png")
    print(json.dumps({key: out[key] for key in ("cell_m2", "brightness_by_facing_direction", "land_share", "filters_summary")}, indent=1, ensure_ascii=False))
    for row in results:
        print(row["pair"], row["coherence_used"], row["published_total_km2"], row["measured_total_km2"],
              {name: round(values["low_km2"] + values["high_km2"], 2) for name, values in row["places"].items()},
              "away", row["steep_facing_away_km2"], "zone", row["inside_danger_zone_km2"])
    for name, rows in table.items():
        print(name, {short_name(k): (v["total_km2"] if v else None) for k, v in rows.items()})
    print("cache MB", round(sum(p.stat().st_size for p in CACHE.glob("*")) / 1e6, 1))


if __name__ == "__main__":
    main()

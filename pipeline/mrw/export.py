"""Task T-018: process one pair from ASF and write its files to pipeline/out/.

Run from the project folder:
    python pipeline/mrw/export.py mayon <before GCOV granule> <after GCOV granule>

Writes 5 layer images, new_material.bin and pair.json with status "ready", then
prints a summary. Nothing here reaches the public site: that is the publish step.
"""
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
from PIL import Image
from pyproj import Transformer
from shapely.geometry import shape

# Lets this file run as a script from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mrw import __version__
from mrw.classify import EITHER_SIGNAL, HIGH, LOW, areas_km2, classify
from mrw.coherence import GUNW_DATASETS, GUNW_GROUP, compute_coherence_loss
from mrw.config import load_site, thresholds_are_provisional, utc_now_text
from mrw.contract_check import check_data_dir
from mrw.context import DATA_FOLDER, write_json
from mrw.download import read_crop
from mrw.filters import apply_filters
from mrw.gcov import GCOV_DATASETS, GCOV_GROUP, HAS_VALUE, MASKED_BY_PRODUCT, OUTSIDE_COVERAGE, SEA, process_gcov
from mrw.pairs import check_consecutive, check_same_track, find_gunw, same_gap, pair_id, pass_id, require_product
from mrw.search import search_gcov, search_gunw, vertex_url

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_FOLDER = REPO_ROOT / "pipeline" / "out"
LOG_FOLDER = REPO_ROOT / "pipeline" / "logs"
SEARCH_START = "2026-06-01"
# About 20 m at this latitude: sharp enough for the map, and small enough to load fast.
WEB_CELL_DEG = 0.000185
NO_DATA_CODES = {str(MASKED_BY_PRODUCT): "masked_by_product", str(SEA): "sea",
                 str(OUTSIDE_COVERAGE): "outside_coverage"}
CLASS_COLORS = {LOW: "#E69F00", HIGH: "#D55E00"}  # orange and vermillion: color-blind safe
CLASS_LEGEND = [
    {"value": LOW, "label": "Possible new material (brightness only)", "color": CLASS_COLORS[LOW], "confidence": "low"},
    {"value": HIGH, "label": "Likely new material (brightness and coherence agree)", "color": CLASS_COLORS[HIGH], "confidence": "high"},
]
# kind: (title, units, color map, lowest value, highest value)
CONTINUOUS_LAYERS = {
    "before_db": ("Radar brightness before", "dB", "gray", -25.0, 5.0),
    "after_db": ("Radar brightness after", "dB", "gray", -25.0, 5.0),
    "change_db": ("Brightness change", "dB", "RdBu_r", -6.0, 6.0),
    "coherence_loss": ("Coherence loss", "coherence loss (0–1)", "viridis", 0.0, 1.0),
}
POLARIZATIONS = {"DHDH": ["HHHH", "HVHV"], "SHNA": ["HHHH"]}


def site_bounds(config):
    """Return the site's (west, south, east, north)."""
    return tuple(config[k] for k in ("bounds_west", "bounds_south", "bounds_east", "bounds_north"))


def web_grid_size(bounds):
    """Return the (width, height) of the web images for these bounds."""
    west, south, east, north = bounds
    return round((east - west) / WEB_CELL_DEG), round((north - south) / WEB_CELL_DEG)


def lookup_web_cells(x_values, y_values, epsg, bounds):
    """Find which radar pixel each web cell shows.

    Radar pixels are on a UTM grid (metres), while web maps need latitude and
    longitude, so each web cell's centre is converted to UTM and the nearest
    radar pixel taken. Returns rows, columns, and which cells are inside the data.
    """
    width, height = web_grid_size(bounds)
    west, south, east, north = bounds
    lons = west + (np.arange(width) + 0.5) * (east - west) / width
    lats = north - (np.arange(height) + 0.5) * (north - south) / height
    xs, ys = Transformer.from_crs(4326, epsg, always_xy=True).transform(*np.meshgrid(lons, lats))
    columns = np.rint((xs - x_values[0]) / (x_values[1] - x_values[0])).astype(int)
    rows = np.rint((ys - y_values[0]) / (y_values[1] - y_values[0])).astype(int)
    inside = (columns >= 0) & (columns < len(x_values)) & (rows >= 0) & (rows < len(y_values))
    return np.clip(rows, 0, len(y_values) - 1), np.clip(columns, 0, len(x_values) - 1), inside


def _hex_to_rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def colorize_values(values, color_map, low, high):
    """Turn values into a color image, transparent wherever there is no value."""
    scaled = np.clip((values - low) / (high - low), 0, 1)
    rgba = matplotlib.colormaps[color_map](np.nan_to_num(scaled), bytes=True)
    rgba[..., 3] = np.where(np.isfinite(values), 255, 0)
    return rgba


def colorize_classes(classes):
    """Turn the class grid into an image: only detected cells have a color."""
    rgba = np.zeros(classes.shape + (4,), dtype="uint8")
    for value, color in CLASS_COLORS.items():
        rgba[classes == value] = (*_hex_to_rgb(color), 230)
    return rgba


def save_png(rgba, path):
    """Save an image as PNG. Row 0 is the northern edge, as the map expects."""
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)


def continuous_legend(color_map, low, high, units):
    """Make the legend's two end points for a continuous color scale."""
    colors = matplotlib.colormaps[color_map]([0.0, 1.0], bytes=True)
    return [{"value": value, "label": f"{value:g} {units}",
             "color": "#{:02X}{:02X}{:02X}".format(*color[:3]), "confidence": None}
            for value, color in zip((low, high), colors)]


def layer_record(pair_key, kind, title, units, bounds, size, granules, legend, now, scale=(None, None)):
    """Build one `layers` row (docs/05 TBL-06) for an image without a value grid."""
    west, south, east, north = bounds
    return {
        "id": f"{pair_key}_{kind}", "pair_id": pair_key, "kind": kind, "title": title, "units": units,
        "image_path": f"{kind}.png", "image_format": "png",
        "bounds_west": west, "bounds_south": south, "bounds_east": east, "bounds_north": north,
        "image_width": size[0], "image_height": size[1],
        "grid_path": None, "grid_dtype": None, "grid_scale": None, "grid_nodata": None,
        "no_data_codes": None, "grid_width": None, "grid_height": None,
        "color_scale_min": scale[0], "color_scale_max": scale[1],
        "legend": legend, "source_granule_ids": granules, "created_at": now, "updated_at": now,
    }


def pass_record(one_pass, site_id, spacing_m, now):
    """Build one `passes` row (docs/05 TBL-04)."""
    mode = one_pass["granule_id"].split("_")[9]
    return {
        "id": pass_id(one_pass), "site_id": site_id, "mission": "NISAR", "product_type": "GCOV",
        "granule_id": one_pass["granule_id"], "track": one_pass["track"], "frame": one_pass["frame"],
        "orbit_direction": one_pass["orbit_direction"], "cycle": one_pass["cycle"],
        "acquired_start": one_pass["acquired_start"], "acquired_end": one_pass["acquired_end"],
        "polarizations": POLARIZATIONS.get(mode, ["HHHH"]), "pixel_spacing_m": spacing_m,
        "maturity": one_pass["maturity"], "vertex_url": vertex_url(one_pass["granule_id"]),
        "created_at": now, "updated_at": now,
    }


def class_legend(config):
    """The legend for the class layer. A site can word it in its own config."""
    wording = config.get("layer_wording")
    if not wording:
        return CLASS_LEGEND
    labels = {LOW: wording["low_label"], HIGH: wording["high_label"]}
    return [{**item, "label": labels[item["value"]]} for item in CLASS_LEGEND]


def new_material_title(config, pair_key=None):
    """Say on the layer itself when its thresholds aren't final."""
    wording = config.get("layer_wording")
    if wording:
        return wording.get("pair_titles", {}).get(pair_key, wording["title"])
    title = "New material (PROVISIONAL thresholds)" if thresholds_are_provisional(config) else "New material"
    reach = (config.get("filters") or {}).get("max_distance_km")
    return f"{title}, within {reach:g} km of the summit" if reach else title


def write_layers(folder, gcov_result, loss, classes, config, pair_key, granules, now):
    """Write every image and the value grid. Return the `layers` rows."""
    bounds = site_bounds(config)
    size = web_grid_size(bounds)
    rows, columns, inside = lookup_web_cells(gcov_result["x"], gcov_result["y"], gcov_result["epsg"], bounds)
    layers = []
    values_by_kind = {kind: gcov_result[kind] for kind in ("before_db", "after_db", "change_db")}
    if loss is not None:
        # Coherence loss is only meaningful where there is ground with a value.
        values_by_kind["coherence_loss"] = np.where(gcov_result["reasons"] == HAS_VALUE, loss, np.nan)
    for kind, values in values_by_kind.items():
        title, units, color_map, low, high = CONTINUOUS_LAYERS[kind]
        web_values = values[rows, columns].astype("float64")
        web_values[~inside] = np.nan
        save_png(colorize_values(web_values, color_map, low, high), folder / f"{kind}.png")
        layers.append(layer_record(pair_key, kind, title, units, bounds, size, granules[kind],
                                   continuous_legend(color_map, low, high, units), now, (low, high)))
    web_classes = classes[rows, columns]
    web_classes[~inside] = OUTSIDE_COVERAGE
    save_png(colorize_classes(web_classes), folder / "new_material.png")
    (folder / "new_material.bin").write_bytes(web_classes.astype("uint8").tobytes())
    record = layer_record(pair_key, "new_material", new_material_title(config, pair_key), "class", bounds, size,
                          granules["new_material"], class_legend(config), now)
    record.update(grid_path="new_material.bin", grid_dtype="uint8", grid_scale=1,
                  no_data_codes=NO_DATA_CODES, grid_width=size[0], grid_height=size[1])
    layers.append(record)
    return layers


def layer_granules(before, after, gunw, previous_gunw):
    """List which products each layer was made from (FR-039)."""
    gcovs = [before["granule_id"], after["granule_id"]]
    gunws = [g["granule_id"] for g in (gunw, previous_gunw) if g] if gunw and previous_gunw else []
    return {"before_db": gcovs[:1], "after_db": gcovs[1:], "change_db": gcovs,
            "coherence_loss": gunws, "new_material": gcovs + gunws}


def build_pair_record(config, before, after, gunw, previous_id, used_coherence, areas, now):
    """Build the `pairs` row (docs/05 TBL-05) with status 'ready' (FR-029)."""
    thresholds = config["thresholds"]
    key = pair_id(config["id"], before, after)
    return {
        "id": key, "site_id": config["id"], "status": "ready",
        "track": before["track"], "frame": before["frame"], "orbit_direction": before["orbit_direction"],
        "before_pass_id": pass_id(before), "after_pass_id": pass_id(after),
        "before_acquired_start": before["acquired_start"], "after_acquired_start": after["acquired_start"],
        "previous_pair_id": previous_id,
        "gunw_granule_id": gunw["granule_id"] if gunw else None,
        "gunw_vertex_url": vertex_url(gunw["granule_id"]) if gunw else None,
        "coherence_used": used_coherence,
        "brightness_threshold_db": thresholds["brightness_threshold_db"],
        "coherence_loss_threshold": thresholds["coherence_loss_threshold"] if used_coherence else None,
        **areas,
        "pipeline_version": __version__, "error_message": None, "published_at": None,
        "check_note": (config.get("layer_wording") or {}).get("pair_check_notes", {}).get(key),
        "created_at": now, "updated_at": now,
    }


def distance_from_summit(gcov_result, config):
    """Work out each radar pixel's distance from the summit in km, if the site's filter needs it."""
    if not (config.get("filters") or {}).get("max_distance_km"):
        return None
    to_utm = Transformer.from_crs(4326, gcov_result["epsg"], always_xy=True)
    x0, y0 = to_utm.transform(config["summit_lon"], config["summit_lat"])
    xs, ys = np.meshgrid(gcov_result["x"], gcov_result["y"])
    return np.hypot(xs - x0, ys - y0) / 1000


def write_pair(gcov_result, loss, before, after, gunw, previous_gunw, previous_id, config, out_folder):
    """Classify a processed pair and write all its files. Returns the pair record."""
    thresholds = config["thresholds"]
    classes = classify(gcov_result["change_db"], loss, gcov_result["reasons"],
                       thresholds["brightness_threshold_db"], thresholds["coherence_loss_threshold"],
                       rule=thresholds.get("rule", EITHER_SIGNAL))
    # Filters are off unless the owner turns them on in the site config.
    classes = apply_filters(classes, config.get("filters"), gcov_result["spacing_x_m"] * gcov_result["spacing_y_m"],
                            distance_km=distance_from_summit(gcov_result, config))
    areas = areas_km2(classes, gcov_result["spacing_x_m"], gcov_result["spacing_y_m"])
    now = utc_now_text()
    pair = build_pair_record(config, before, after, gunw, previous_id, loss is not None, areas, now)
    folder = Path(out_folder) / "sites" / config["id"] / "pairs" / pair["id"]
    folder.mkdir(parents=True, exist_ok=True)
    granules = layer_granules(before, after, gunw, previous_gunw)
    layers = write_layers(folder, gcov_result, loss, classes, config, pair["id"], granules, now)
    passes = [pass_record(p, config["id"], gcov_result["spacing_x_m"], now) for p in (before, after)]
    write_json(folder / "pair.json", {**pair, "passes": passes, "layers": layers}, now)
    return {**pair, "layers": layers}


def _previous_pass(passes, before):
    """Find the pass just before `before` on the same track, or None."""
    same = [p for p in passes
            if (p["track"], p["frame"], p["orbit_direction"]) == (before["track"], before["frame"], before["orbit_direction"])
            and p["acquired_start"] < before["acquired_start"]]
    return max(same, key=lambda p: p["acquired_start"]) if same else None


def _read_gunw(gunw, bounds):
    """Read one GUNW's coherence, cropped to the site. None if there is no GUNW."""
    if gunw is None:
        return None
    return read_crop(gunw["granule_id"], gunw["url"], GUNW_GROUP, GUNW_DATASETS, bounds)


def load_land(site_id, data_folder=DATA_FOLDER):
    """Read the site's land shape."""
    path = Path(data_folder) / "sites" / site_id / "land.geojson"
    return shape(json.loads(path.read_text(encoding="utf-8"))["features"][0]["geometry"])


def run_pair(site_id, before_granule, after_granule, out_folder=OUT_FOLDER,
             search_passes=search_gcov, search_products=search_gunw):
    """Process one pair from start to finish. Any stop happens before files are written."""
    config = load_site(site_id)
    passes = search_passes(config, SEARCH_START)
    by_name = {p["granule_id"]: p for p in passes}
    require_product(before_granule, by_name)
    require_product(after_granule, by_name)
    before, after = by_name[before_granule], by_name[after_granule]
    check_same_track(before, after)
    check_consecutive(before, after, passes)
    products = search_products(config, SEARCH_START)
    gunw = find_gunw(before, after, products)
    previous = _previous_pass(passes, before)
    # With unequal gaps there is no fair baseline, so the pair uses brightness only (FR-030).
    previous_gunw = find_gunw(previous, before, products) if previous and same_gap(previous, before, after) else None
    bounds = site_bounds(config)
    crops = [read_crop(p["granule_id"], p["url"], GCOV_GROUP, GCOV_DATASETS, bounds) for p in (before, after)]
    gcov_result = process_gcov(crops[0], crops[1], load_land(site_id))
    loss = compute_coherence_loss(_read_gunw(previous_gunw, bounds), _read_gunw(gunw, bounds),
                                  gcov_result["x"], gcov_result["y"], gcov_result["epsg"])
    previous_id = pair_id(site_id, previous, before) if previous else None
    return write_pair(gcov_result, loss, before, after, gunw, previous_gunw, previous_id, config, out_folder)


def print_summary(pair, config):
    """Print the summary from SCR-12: pair, status, granules and areas."""
    print(f"Pair: {pair['id']}")
    print(f"Status: {pair['status']}")
    new_material = next(layer for layer in pair["layers"] if layer["kind"] == "new_material")
    for granule in new_material["source_granule_ids"]:
        print(f"Granule: {granule}")
    print(f"Coherence used: {pair['coherence_used']}")
    print(f"High confidence: {pair['high_confidence_area_km2']:.2f} km2")
    print(f"Low confidence: {pair['low_confidence_area_km2']:.2f} km2")
    print(f"Total new material: {pair['new_material_area_km2']:.2f} km2")
    if thresholds_are_provisional(config):
        print(f"Thresholds are PROVISIONAL: {pair['brightness_threshold_db']} dB, "
              f"coherence loss {pair['coherence_loss_threshold']}")


def write_run_log(pair, errors, folder=LOG_FOLDER):
    """Keep one small log file per run (docs/04 section 9). This folder isn't committed."""
    folder.mkdir(parents=True, exist_ok=True)
    stamp = utc_now_text().replace(":", "").replace("-", "")
    record = {"pair_id": pair["id"], "status": pair["status"], "pipeline_version": pair["pipeline_version"],
              "areas_km2": pair["new_material_area_km2"], "contract_errors": errors}
    (folder / f"{stamp}_{pair['id']}.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")


def main(argv):
    """Command-line entry point. Prints the stop message and returns 1 on failure."""
    site_id, before_granule, after_granule = argv
    try:
        pair = run_pair(site_id, before_granule, after_granule)
    except Exception as problem:
        print(problem)
        return 1
    print_summary(pair, load_site(site_id))
    errors = check_data_dir(OUT_FOLDER, published=False)
    print(f"Contract check on {OUT_FOLDER}: {len(errors)} error(s)")
    for error in errors:
        print(error)
    write_run_log(pair, errors)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Second-site trial: run the full method on the Azuero Peninsula landslides, Panama.

Run from the project folder:
    python pipeline/reports/panama_trial.py

Output goes to pipeline/out/ only, never site/data/. The config lives here, not in
pipeline/sites/, so the publish step can't list this site. It measures the pair spanning the
2026-10-09 earthquake and the quiet pair before it. The rule and thresholds are read from
Mayon's config when this runs: nothing is tuned for this site.
"""
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
from shapely import make_valid
from shapely.geometry import box, mapping, shape
from shapely.ops import unary_union

REPORTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPORTS.parent))

from mrw.classify import HIGH, LOW, classify
from mrw.coherence import GUNW_DATASETS, GUNW_GROUP, compute_coherence_loss
from mrw.config import load_site, load_site_config
from mrw.contract_check import check_data_dir
from mrw.download import read_crop, total_bytes_logged
from mrw.export import OUT_FOLDER, site_bounds, write_pair
from mrw.gcov import GCOV_DATASETS, GCOV_GROUP, HAS_VALUE, process_gcov
from mrw.pairs import build_track_pairs, same_gap
from mrw.search import search_gcov, search_gunw

CONFIG_PATH = REPORTS / "panama_trial_config.json"
LAND_PATH = REPORTS / "panama_trial_land.geojson"
CACHE = REPORTS.parents[1] / "raw" / "context_download" / "panama"
BOUNDARY_URL = "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/PAN/ADM2/geoBoundaries-PAN-ADM2.geojson"
EVENT_PAIR = "panama_D141F085_20260927_20261009"
QUIET_PAIR = "panama_D141F085_20260915_20260927"
SEARCH_START = "2026-06-01"
# The landslide cluster reported by the Eos Landslide Blog.
CLUSTER_BOX_KM = 5.5
CLUSTER = (7.477, -80.865)


def make_land(bounds):
    """Clip the country's districts to the site and join them into one land shape."""
    CACHE.mkdir(parents=True, exist_ok=True)
    source = CACHE / "geoBoundaries-PAN-ADM2.geojson"
    if not source.is_file():
        urllib.request.urlretrieve(BOUNDARY_URL, source)
    features = json.loads(source.read_text(encoding="utf-8"))["features"]
    site = box(*bounds)
    land = unary_union([make_valid(shape(f["geometry"])).intersection(site) for f in features])
    LAND_PATH.write_text(json.dumps({"type": "Feature", "properties": {
        "source": "geoBoundaries gbOpen PAN ADM2 (Smithsonian Tropical Research Institute, 2012)",
        "license": "CC BY-SA 4.0"}, "geometry": mapping(land)}) + "\n", encoding="utf-8")
    return land


def process(pair, bounds, land):
    """Read one pair and apply the same rules as export.run_pair."""
    crops = [read_crop(p["granule_id"], p["url"], GCOV_GROUP, GCOV_DATASETS, bounds) for p in (pair["before"], pair["after"])]
    result = process_gcov(crops[0], crops[1], land)
    previous = pair["previous"]
    # With unequal gaps there is no fair baseline, so the pair uses brightness only (FR-030).
    fair = previous is not None and same_gap(previous["before"], pair["before"], pair["after"])
    baseline = previous["gunw"] if fair else None
    gunws = [read_crop(g["granule_id"], g["url"], GUNW_GROUP, GUNW_DATASETS, bounds) if g else None for g in (baseline, pair["gunw"])]
    loss = compute_coherence_loss(gunws[0], gunws[1], result["x"], result["y"], result["epsg"])
    return result, loss, baseline


def cluster_mask(result):
    """Mark the pixels in a box around the reported landslide cluster."""
    from pyproj import Transformer
    x0, y0 = Transformer.from_crs(4326, result["epsg"], always_xy=True).transform(CLUSTER[1], CLUSTER[0])
    xs, ys = np.meshgrid(result["x"], result["y"])
    return (np.abs(xs - x0) <= CLUSTER_BOX_KM * 1000) & (np.abs(ys - y0) <= CLUSTER_BOX_KM * 1000)


def measure(result, loss, config):
    """Report each signal's area, over the whole site and in the cluster box."""
    thresholds = config["thresholds"]
    classes = classify(result["change_db"], loss, result["reasons"], thresholds["brightness_threshold_db"], thresholds["coherence_loss_threshold"], rule=thresholds["rule"])
    cell_km2 = result["spacing_x_m"] * result["spacing_y_m"] / 1e6
    has_value = result["reasons"] == HAS_VALUE
    near = cluster_mask(result)
    with np.errstate(invalid="ignore"):
        bright = has_value & (np.abs(result["change_db"]) >= thresholds["brightness_threshold_db"])

    def km2(cells):
        return round(float(np.count_nonzero(cells)) * cell_km2, 3)
    flagged = np.isin(classes, (LOW, HIGH))
    return {"coherence_used": loss is not None, "flagged_share_of_land": round(km2(flagged) / km2(has_value), 3), "land_km2": km2(has_value), "valid_share": round(float(has_value.mean()), 3),
            "low_km2": km2(classes == LOW), "high_km2": km2(classes == HIGH), "total_km2": km2(flagged),
            "brightness_km2": km2(bright), "cluster_land_km2": km2(has_value & near), "cluster_total_km2": km2(flagged & near),
            "cluster_high_km2": km2((classes == HIGH) & near), "cluster_brightness_km2": km2(bright & near),
            "median_change_db": round(float(np.nanmedian(result["change_db"][has_value])), 2)}


def main():
    config = load_site_config(CONFIG_PATH)
    # The same final rule and values as Mayon, whatever the trial config file still holds.
    config["thresholds"] = load_site("mayon")["thresholds"]
    bounds = site_bounds(config)
    land = make_land(bounds)
    start_bytes = total_bytes_logged()
    pairs = {p["id"]: p for p in build_track_pairs("panama", search_gcov(config, SEARCH_START), search_gunw(config, SEARCH_START))}
    results = {}
    for name, pair_id in (("quiet_pair_before", QUIET_PAIR), ("earthquake_pair", EVENT_PAIR)):
        pair = pairs[pair_id]
        result, loss, baseline = process(pair, bounds, land)
        results[name] = {"id": pair_id, "granules": [pair["before"]["granule_id"], pair["after"]["granule_id"]],
                         "gunw": pair["gunw"]["granule_id"] if pair["gunw"] else None, **measure(result, loss, config)}
        previous_id = pair["previous"]["id"] if pair["previous"] else None
        record = write_pair(result, loss, pair["before"], pair["after"], pair["gunw"], baseline, previous_id, config, OUT_FOLDER)
        results[name]["published_style_areas"] = {key: record[key] for key in ("high_confidence_area_km2", "low_confidence_area_km2", "new_material_area_km2")}
        print(name, json.dumps(results[name]), flush=True)
    results["after_pass_start_utc"] = pairs[EVENT_PAIR]["after"]["acquired_start"]
    results["gb_fetched"] = round((total_bytes_logged() - start_bytes) / 1e9, 3)
    results["contract_errors_pipeline_out"] = len(check_data_dir(OUT_FOLDER, published=False))
    (OUT_FOLDER / "panama-trial-final-rule.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    print("GB fetched", results["gb_fetched"], "contract errors", results["contract_errors_pipeline_out"], "after pass", results["after_pass_start_utc"])


if __name__ == "__main__":
    main()

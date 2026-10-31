"""Evening run, analysis only: test the rule "brightness leads, coherence confirms".

Run from the project folder:
    python pipeline/reports/evening_calibration.py

The rule, at a brightness threshold T:
- Brightness change of T or more counts as new material (low confidence).
- It is high confidence only if coherence loss is also 0.4 or more.
- Coherence loss alone counts as nothing.

This differs from mrw/classify.py, where coherence loss alone gives low confidence. The rule
lives only in this study: no default changes, and the site keeps its PROVISIONAL values.
It uses pre-eruption pairs only, within 10 km of the summit, and reads cached crops only, so
it can't download anything. Pairs whose crops aren't cached are listed as left out.
"""
import json
import sys
from pathlib import Path

import numpy as np

REPORTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPORTS.parent))
sys.path.insert(0, str(REPORTS))

from july_gully_check import ALL_PAIRS, GULLIES, bearings_and_distances

from mrw.classify import LOW, classify
from mrw.coherence import GUNW_DATASETS, GUNW_GROUP, compute_coherence_loss
from mrw.config import load_site
from mrw.download import RAW_FOLDER, cache_path, read_crop
from mrw.export import SEARCH_START, load_land, site_bounds
from mrw.gcov import GCOV_DATASETS, GCOV_GROUP, process_gcov
from mrw.pairs import build_track_pairs, same_gap
from mrw.search import search_gcov, search_gunw

BRIGHTNESS_CANDIDATES = (3.0, 4.0, 5.0)
CONFIRMING_LOSS = 0.4
REACH_KM = 10
# The night 2 table's groups, plus the two track 104 pairs published this evening.
GROUPS = {**ALL_PAIRS, "mayon_D104F082_20260925_20261007": "quiet", "mayon_D104F082_20261007_20261019": "quiet"}


def is_cached(product, group, datasets, bounds):
    """Is this product's crop already on disk? Reading it then needs no download."""
    return product is not None and cache_path(RAW_FOLDER, product["granule_id"], group, datasets, bounds).is_file()


def read_loss(pair, result, bounds):
    """Return coherence loss, or None without a fair baseline: both GUNWs, and equal time gaps."""
    previous = pair["previous"]
    if not previous or not same_gap(previous["before"], pair["before"], pair["after"]):
        return None
    products = (previous["gunw"], pair["gunw"])
    if not all(is_cached(g, GUNW_GROUP, GUNW_DATASETS, bounds) for g in products):
        return None
    crops = [read_crop(g["granule_id"], g["url"], GUNW_GROUP, GUNW_DATASETS, bounds) for g in products]
    return compute_coherence_loss(crops[0], crops[1], result["x"], result["y"], result["epsg"])


def measure(result, loss, threshold, bearing, distance, danger_km, cell_km2):
    """Apply the rule at one threshold and add up the areas, all within the reach."""
    # With no loss given, classify flags brightness alone, which is what this rule leads with.
    bright = classify(result["change_db"], None, result["reasons"], threshold, CONFIRMING_LOSS) == LOW
    bright &= distance <= REACH_KM
    with np.errstate(invalid="ignore"):
        high = bright & (loss >= CONFIRMING_LOSS) if loss is not None else np.zeros(bright.shape, dtype=bool)
    low = bright & ~high

    def km2(cells):
        return round(float(np.count_nonzero(cells)) * cell_km2, 3)

    in_zone = distance <= danger_km
    wedges = {}
    for name, (middle, half_width, reach) in GULLIES.items():
        inside = (np.abs((bearing - middle + 180) % 360 - 180) <= half_width) & (distance <= reach)
        wedges[name] = {"total_km2": km2(bright & inside), "high_km2": km2(high & inside)}
    return {"threshold_db": threshold, "low_km2": km2(low), "high_km2": km2(high), "total_km2": km2(bright),
            "zone_low_km2": km2(low & in_zone), "zone_high_km2": km2(high & in_zone),
            "zone_total_km2": km2(bright & in_zone), "wedges": wedges}


def study_pair(pair, bounds, land, config):
    """Measure one pair at every threshold."""
    crops = [read_crop(p["granule_id"], p["url"], GCOV_GROUP, GCOV_DATASETS, bounds) for p in (pair["before"], pair["after"])]
    result = process_gcov(crops[0], crops[1], land)
    loss = read_loss(pair, result, bounds)
    bearing, distance = bearings_and_distances(result, config)
    cell_km2 = result["spacing_x_m"] * result["spacing_y_m"] / 1e6
    return {"id": pair["id"], "kind": GROUPS.get(pair["id"], "other"), "track": pair["before"]["track"],
            "coherence_used": loss is not None,
            "by_threshold": [measure(result, loss, t, bearing, distance, config["danger_zone_radius_km"], cell_km2)
                             for t in BRIGHTNESS_CANDIDATES]}


def check_against_night_2(records):
    """At 3.0 dB the wedge totals must equal the night 2 brightness-only numbers."""
    saved = {row["id"]: row["brightness_only"] for row in json.loads((REPORTS / "july-gully-check.json").read_text(encoding="utf-8"))}
    differences = [(r["id"], name) for r in records if r["id"] in saved for name in GULLIES
                   if abs(r["by_threshold"][0]["wedges"][name]["total_km2"] - saved[r["id"]][name]) > 0.0011]
    print("Differences from night 2 at 3.0 dB:", differences or "none")
    return differences


def short_name(pair_key):
    """Turn mayon_A111F008_20260703_20260715 into A111 07-03 → 07-15."""
    _, track, first, second = pair_key.split("_")
    return f"{track[:4]} {first[4:6]}-{first[6:]} → {second[4:6]}-{second[6:]}"


def print_pair_table(records, index):
    """One table per threshold: each pair's areas by class, zone and wedge."""
    print(f"\n#### T = {BRIGHTNESS_CANDIDATES[index]} dB\n")
    print("| Pair | Group | Coherence | High | Low | Total | In danger zone (high) | Basud | Bonga | Mi-isi |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for record in sorted(records, key=lambda r: (-r["track"], r["id"])):
        row = record["by_threshold"][index]
        wedges = " | ".join(f"{row['wedges'][name]['total_km2']:.3f}" for name in GULLIES)
        print(f"| {short_name(record['id'])} | {record['kind']} | {'Yes' if record['coherence_used'] else 'No'} | {row['high_km2']:.3f} | "
              f"{row['low_km2']:.3f} | {row['total_km2']:.3f} | {row['zone_total_km2']:.3f} ({row['zone_high_km2']:.3f}) | {wedges} |")


def value_range(values):
    """Write a list of numbers as a range."""
    return f"{min(values):.3f}" if min(values) == max(values) else f"{min(values):.3f}–{max(values):.3f}"


def print_wedge_table(records, index):
    """The night 2 table's form: quiet range against the pair spanning the event, per track."""
    print(f"\n#### Flank wedges, T = {BRIGHTNESS_CANDIDATES[index]} dB (km²)\n")
    print("| Track | Group | Basud (E) | Bonga (SE) | Mi-isi (S) |\n| --- | --- | --- | --- | --- |")
    for track in (111, 39, 104):
        for kind in ("quiet", "july"):
            rows = [r["by_threshold"][index]["wedges"] for r in records if r["track"] == track and r["kind"] == kind]
            label = f"{len(rows)} quiet pair{'s' if len(rows) > 1 else ''}" if kind == "quiet" else "**Spans the event**"
            cells = " | ".join(value_range([row[name]["total_km2"] for row in rows]) for name in GULLIES)
            print(f"| {track} | {label} | {cells} |")


def main():
    config = load_site("mayon")
    bounds, land = site_bounds(config), load_land("mayon")
    pairs = build_track_pairs("mayon", search_gcov(config, SEARCH_START), search_gunw(config, SEARCH_START))
    records, left_out = [], []
    for pair in pairs:
        if all(is_cached(p, GCOV_GROUP, GCOV_DATASETS, bounds) for p in (pair["before"], pair["after"])):
            records.append(study_pair(pair, bounds, land, config))
            print("Studied", pair["id"], flush=True)
        else:
            left_out.append(pair["id"])
    differences = check_against_night_2(records)
    output = {"status": "analysis only; no thresholds chosen, no defaults changed", "rule": "brightness leads, coherence confirms",
              "confirming_coherence_loss": CONFIRMING_LOSS, "reach_km": REACH_KM, "pairs": records, "left_out_not_cached": left_out,
              "differences_from_night_2": differences}
    (REPORTS / "evening-calibration.json").write_text(json.dumps(output, indent=1) + "\n", encoding="utf-8")
    print("Left out, not cached:", [short_name(key) for key in left_out])
    for index in range(len(BRIGHTNESS_CANDIDATES)):
        print_pair_table(records, index)
    for index in range(len(BRIGHTNESS_CANDIDATES)):
        print_wedge_table(records, index)


if __name__ == "__main__":
    main()

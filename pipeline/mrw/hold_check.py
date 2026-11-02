"""Tasks T-126 and T-129: the numbers behind the owner's rule for holding a pair (docs/04, ADR-014).

A pair is measured here and compared with the published pairs, whose numbers were saved
before any post-eruption product was opened. This never downloads: it reads the crops
already cached in raw/, and the pair's own files.

The rule, in short. Hold a pair automatically if:
  (a) a product isn't PROVISIONAL or better,
  (d) large no-data gaps cover the volcano,
  (e) the map shows stripe or edge patterns (only a person can see this).
Look closer, without holding, if:
  (b) the median coherence change far from the summit is outside the published range,
  (c) the flagged area far from the summit is above the highest published 12-day pair.
To look closer, compare where the flagged change is with the quiet pairs. Concentrated near
the volcano and its channels: publish. Spread evenly across the whole scene: hold.
A large area alone is not a reason to hold, and track agreement never blocks a decision.
"""
import functools
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from pyproj import Transformer

from mrw.channel_areas import cell_area_km2, read_grid, strip_cells, utm_epsg
from mrw.classify import HIGH, LOW, NONE
from mrw.coherence import GUNW_DATASETS, GUNW_GROUP, compute_coherence_loss
from mrw.download import read_crop
from mrw.gcov import GCOV_DATASETS, GCOV_GROUP, HAS_VALUE, MASKED_BY_PRODUCT, OUTSIDE_COVERAGE, SEA, process_gcov

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = REPO_ROOT / "pipeline" / "reports" / "hold-check-baseline.json"
# An eruption shouldn't reach this far from the summit, so a big change out here is more likely
# to come from the weather or the radar than from the volcano. The owner set this on 2026-11-03.
OUTER_KM = 8
USUAL_GAP_DAYS = 12  # a longer gap shows more change, so it can't set the limit for the usual gap
GOOD_MATURITY = ("PROVISIONAL", "VALIDATED")
# Reason (d) says "large": this share of the volcano's land. The owner confirmed 5% on 2026-11-03.
LARGE_GAP_SHARE = 0.05
# Flagged cells within about 200 m count as the same place: 10 cells of about 20 m. The two tracks
# look at the volcano from opposite sides, so the same deposit rarely lands on the very same cells.
NEARBY_CELLS = 10


def refuse_download(url, raw_folder=None):
    """Stand in for the downloader, so a missing crop stops the check instead of fetching data."""
    raise FileNotFoundError(f"This crop isn't in raw/, and this step doesn't download: {url}")


cached_crop = functools.partial(read_crop, opener=refuse_download)


def read_pair(pair_folder):
    """Return a pair's record, its class layer and its grid of cells."""
    pair = json.loads((Path(pair_folder) / "pair.json").read_text(encoding="utf-8"))["data"]
    layer = next(item for item in pair["layers"] if item["kind"] == "new_material")
    return pair, layer, read_grid(Path(pair_folder), layer)


def distances_km(layer, summit_lat, summit_lon):
    """Return how far each grid cell's centre is from the summit, in km."""
    width, height = layer["grid_width"], layer["grid_height"]
    lons = layer["bounds_west"] + (np.arange(width) + 0.5) * (layer["bounds_east"] - layer["bounds_west"]) / width
    lats = layer["bounds_north"] - (np.arange(height) + 0.5) * (layer["bounds_north"] - layer["bounds_south"]) / height
    to_metres = Transformer.from_crs(4326, utm_epsg(summit_lon, summit_lat), always_xy=True)
    x_summit, y_summit = to_metres.transform(summit_lon, summit_lat)
    xs, ys = to_metres.transform(*np.meshgrid(lons, lats))
    return np.hypot(xs - x_summit, ys - y_summit) / 1000


def flagged(cells):
    return (cells == LOW) | (cells == HIGH)


def gap_days(pair):
    """How many days apart the two passes are. Passes on a track come at about the same time of day."""
    before, after = (datetime.fromisoformat(pair[name].replace("Z", "+00:00")) for name in ("before_acquired_start", "after_acquired_start"))
    return round((after - before).total_seconds() / 86400)


def outer_flagged_km2(cells, distance, one_cell_km2, outer_km=OUTER_KM):
    """Check (c): the flagged area further than `outer_km` from the summit."""
    return float(np.count_nonzero(flagged(cells) & (distance > outer_km)) * one_cell_km2)


def volcano_no_data_share(cells, distance, radius_km):
    """Reason (d): the share of the volcano's land that has no radar data. The sea doesn't count."""
    volcano = (distance <= radius_km) & (cells != SEA)
    if not volcano.any():
        return 0.0
    return float(np.count_nonzero(volcano & np.isin(cells, (MASKED_BY_PRODUCT, OUTSIDE_COVERAGE))) / np.count_nonzero(volcano))


def where_change_is(cells, distance, near_km, reach_km, channel_cells, outer_km=OUTER_KM):
    """For "look closer": the share of flagged cells near the volcano, far from it, and in the channels.

    `even` is the same shares of the ground the radar checked, which is what change spread
    evenly across the scene would give. Change near the volcano beats `even` by a long way.
    """
    checked = np.isin(cells, (NONE, LOW, HIGH)) & (distance <= reach_km)
    places = {"near": distance <= near_km, "far": distance > outer_km, "channels": channel_cells}

    def shares(mask):
        total = np.count_nonzero(mask)
        return {name: float(np.count_nonzero(mask & place) / total) if total else None for name, place in places.items()}
    return {"flagged": shares(flagged(cells)), "even": shares(checked)}


def far_median_coherence_change(layer, pair, config, land, read=cached_crop, outer_km=OUTER_KM):
    """Check (b): the median coherence loss on land further than `outer_km` from the summit.

    Coherence loss is the baseline pair's coherence minus this pair's, as in mrw/coherence.py. Far
    from the summit, an eruption shouldn't change it, so a shift there points to the whole scene.
    Returns None for a pair that used no coherence, which has nothing to measure.
    """
    if not pair["coherence_used"]:
        return None
    bounds = tuple(config[name] for name in ("bounds_west", "bounds_south", "bounds_east", "bounds_north"))
    before, after, gunw, previous = layer["source_granule_ids"]
    result = process_gcov(read(before, None, GCOV_GROUP, GCOV_DATASETS, bounds),
                          read(after, None, GCOV_GROUP, GCOV_DATASETS, bounds), land)
    loss = compute_coherence_loss(read(previous, None, GUNW_GROUP, GUNW_DATASETS, bounds),
                                  read(gunw, None, GUNW_GROUP, GUNW_DATASETS, bounds),
                                  result["x"], result["y"], result["epsg"])
    to_metres = Transformer.from_crs(4326, result["epsg"], always_xy=True)
    x_summit, y_summit = to_metres.transform(config["summit_lon"], config["summit_lat"])
    xs, ys = np.meshgrid(result["x"], result["y"])
    far = np.hypot(xs - x_summit, ys - y_summit) / 1000 > outer_km
    return float(np.nanmedian(loss[(result["reasons"] == HAS_VALUE) & far]))


def channel_cells_of(channels, layer):
    """Mark the grid cells inside any channel's strip."""
    inside = np.zeros((layer["grid_height"], layer["grid_width"]), dtype=bool)
    for channel in channels:
        inside |= strip_cells(channel["properties"]["strip_geometry"], layer)
    return inside


def measure_pair(pair_folder, config, land, channels, read=cached_crop):
    """Measure one pair for the hold rule."""
    pair, layer, cells = read_pair(pair_folder)
    distance = distances_km(layer, config["summit_lat"], config["summit_lon"])
    return {
        "pair_id": pair["id"], "track": pair["track"], "after": pair["after_acquired_start"], "gap_days": gap_days(pair),
        "total_km2": pair["new_material_area_km2"],
        "far_median_coherence_change": far_median_coherence_change(layer, pair, config, land, read),
        "outer_flagged_km2": outer_flagged_km2(cells, distance, cell_area_km2(layer)),
        "volcano_no_data_share": volcano_no_data_share(cells, distance, config["danger_zone_radius_km"]),
        "where": where_change_is(cells, distance, config["danger_zone_radius_km"], config["filters"]["max_distance_km"],
                                 channel_cells_of(channels, layer)),
        "granules": layer["source_granule_ids"],
    }


def _shrink(mask, size=NEARBY_CELLS):
    """Mark each block of size x size cells that has any flagged cell in it."""
    rows, columns = mask.shape[0] // size, mask.shape[1] // size
    return mask[:rows * size, :columns * size].reshape(rows, size, columns, size).any(axis=(1, 3))


def _share_in_both(first, second):
    either = np.count_nonzero(first | second)
    return float(np.count_nonzero(first & second) / either) if either else None


def track_agreement(cells_a, cells_b):
    """Report how much two tracks agree: of everything either flagged, the share both flagged."""
    a, b = flagged(cells_a), flagged(cells_b)
    return {"same_cell": _share_in_both(a, b), "within_about_200_m": _share_in_both(_shrink(a), _shrink(b))}


def limits_from(pairs):
    """Work out what the far-field checks compare against."""
    medians = [row["far_median_coherence_change"] for row in pairs if row["far_median_coherence_change"] is not None]
    usual = [row for row in pairs if row["gap_days"] == USUAL_GAP_DAYS]
    return {
        "pair_count": len(pairs), "pairs_with_coherence": len(medians), "usual_gap_pairs": len(usual),
        "far_median_coherence_change_low": min(medians), "far_median_coherence_change_high": max(medians),
        "outer_flagged_km2_high": max(row["outer_flagged_km2"] for row in usual),
        "volcano_no_data_share_high": max(row["volcano_no_data_share"] for row in pairs),
    }


def build_baseline(data_folder, config, land, channels, read=cached_crop):
    """Measure the published pairs of a site, and work out the limits the rule compares against."""
    pair_root = Path(data_folder) / "sites" / config["id"] / "pairs"
    pairs = [measure_pair(folder, config, land, channels, read) for folder in sorted(pair_root.iterdir()) if folder.is_dir()]
    agreements = []
    for row in pairs:
        for other in pairs:
            if row["track"] < other["track"] and row["pair_id"].split("_")[-2:] == other["pair_id"].split("_")[-2:]:
                agreement = track_agreement(read_pair(pair_root / row["pair_id"])[2], read_pair(pair_root / other["pair_id"])[2])
                agreements.append({"pairs": [row["pair_id"], other["pair_id"]], **agreement})
    return {
        "site_id": config["id"], "outer_km": OUTER_KM, "near_km": config["danger_zone_radius_km"],
        "note": "Saved before any post-eruption product was opened (ADR-014). Don't rebuild it after that.",
        **limits_from(pairs), "track_agreement": agreements,
        "pairs": [{name: value for name, value in row.items() if name != "granules"} for row in pairs],
    }


def hold_reasons(measured, maturities):
    """Return why this pair must be held, or an empty list. Reason (e) is for a person to judge."""
    reasons = []
    for granule in measured["granules"]:
        maturity = maturities.get(granule, "not found on ASF")
        if maturity not in GOOD_MATURITY:
            reasons.append(f"(a) product isn't PROVISIONAL or better ({maturity}): {granule}")
    if measured["volcano_no_data_share"] > LARGE_GAP_SHARE:
        reasons.append(f"(d) {measured['volcano_no_data_share']:.1%} of the volcano has no data, "
                       f"above the {LARGE_GAP_SHARE:.0%} that counts as a large gap")
    return reasons


def look_closer_reasons(measured, baseline):
    """Return the far-field checks that came out of range. These never hold a pair by themselves."""
    reasons = []
    median = measured["far_median_coherence_change"]
    low, high = baseline["far_median_coherence_change_low"], baseline["far_median_coherence_change_high"]
    if median is not None and not low <= median <= high:
        reasons.append(f"(b) median coherence change beyond {baseline['outer_km']} km is {median:.3f}, "
                       f"outside the published range {low:.3f} to {high:.3f}")
    if measured["outer_flagged_km2"] > baseline["outer_flagged_km2_high"]:
        reasons.append(f"(c) flagged area beyond {baseline['outer_km']} km is {measured['outer_flagged_km2']:.3f} km², "
                       f"above the highest 12-day pair's {baseline['outer_flagged_km2_high']:.3f} km²")
    return reasons


def _percent(share):
    return "none flagged" if share is None else f"{share:.1%}"


def print_where(measured, baseline):
    """Print where the flagged change is, next to the published pairs, for the "look closer" judgement."""
    print(f"  Where the flagged change is: share inside {baseline['near_km']:g} km, beyond {baseline['outer_km']} km, in the channels' strips")

    def line(label, where):
        print(f"    {label}: {_percent(where['near'])}, {_percent(where['far'])}, {_percent(where['channels'])}")
    line("This pair", measured["where"]["flagged"])
    line("Spread evenly would be", measured["where"]["even"])
    for row in baseline["pairs"]:
        note = "" if row["gap_days"] == USUAL_GAP_DAYS else f" ({row['gap_days']}-day gap)"
        line(row["pair_id"] + note, row["where"]["flagged"])
    print("  Concentrated near the volcano and channels compared with the quiet pairs: publish.")
    print("  Spread evenly across the whole scene: hold.")


def print_review(measured, holds, closer, baseline):
    """Print one pair's numbers next to the published pairs, and what the rule says."""
    median = measured["far_median_coherence_change"]
    print(f"Pair: {measured['pair_id']}")
    print(f"  Total flagged: {measured['total_km2']:.2f} km² (a large area alone is not a reason to hold)")
    print(f"  Median coherence change beyond {baseline['outer_km']} km: "
          f"{'none, this pair used no coherence' if median is None else format(median, '.3f')}"
          f"  (published range {baseline['far_median_coherence_change_low']:.3f} to {baseline['far_median_coherence_change_high']:.3f},"
          f" from the {baseline['pairs_with_coherence']} of {baseline['pair_count']} pairs with coherence)")
    print(f"  Flagged beyond {baseline['outer_km']} km: {measured['outer_flagged_km2']:.3f} km²"
          f"  (highest of the {baseline['usual_gap_pairs']} published 12-day pairs: {baseline['outer_flagged_km2_high']:.3f} km²)")
    print(f"  Volcano with no data: {measured['volcano_no_data_share']:.2%}"
          f"  (published highest {baseline['volcano_no_data_share_high']:.2%}, large is above {LARGE_GAP_SHARE:.0%})")
    for reason in holds:
        print(f"  HOLD {reason}")
    for reason in closer:
        print(f"  LOOK CLOSER {reason}")
    if not holds and not closer:
        print("  Nothing to hold or look closer at from the numbers.")
    print_where(measured, baseline)
    print("  Still to check by eye, in the preview: (d) no-data gaps over the volcano, (e) stripe or edge patterns. Either one holds the pair.")

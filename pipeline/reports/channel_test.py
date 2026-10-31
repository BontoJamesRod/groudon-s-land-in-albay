"""Night 4: do Mayon's channels, and the quarry stretches in them, change more than the land around them?

Run from the project folder (after channel_test_inputs.py):
    python pipeline/reports/channel_test.py

This is a test, not a feature. It finds NISAR products by listing the folders already in raw/
and reads their cached crops. It never searches ASF, and if a crop were missing it would stop
rather than download. Nothing on the site changes.

Radar steps:
1. Brightness change is the pipeline's own: speckle-filtered HH, in dB, after minus before.
   The 10 km limit is a later step, so it isn't applied here: channels run past 10 km.
2. A pixel is "flagged" when brightness changed by 3.0 dB or more in either direction.
   Coherence is ignored for the verdict.
3. Flagged fraction = flagged pixels / pixels in the area that have a radar value. Sea, and pixels
   the radar can't see (for example, behind a steep slope), can't be flagged, so they aren't counted.

How the two comparisons are made fair, both chosen before looking at any result:
- Part A: each quarry gets its own quiet stretches, at about its own distance from the summit.
  The quiet fraction is the average over the quarries, weighted by quarry size.
- Part C: channel strips and land are compared band by band. Each band's weight is its share of
  the channel strip, so a pair's one ratio isn't skewed by where most land happens to lie.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pyproj import Transformer
from rasterio.features import rasterize, shapes as raster_shapes
from rasterio.transform import from_origin
from scipy import ndimage
from shapely import transform as transform_points
from shapely.geometry import LineString, Point, mapping, shape
from shapely.ops import unary_union

REPORTS = Path(__file__).resolve().parent
REPO = REPORTS.parents[1]
sys.path.insert(0, str(REPORTS.parent))

from mrw.classify import HIGH, LOW, classify
from mrw.coherence import GUNW_DATASETS, GUNW_GROUP, compute_coherence_loss
from mrw.config import load_site
from mrw.download import RAW_FOLDER, read_crop
from mrw.export import load_land, site_bounds
from mrw.gcov import GCOV_DATASETS, GCOV_GROUP, HAS_VALUE, land_mask, process_gcov
from mrw.pairs import same_gap
from mrw.search import parse_gcov, parse_gunw

CONTEXT = REPO / "pipeline" / "context"
WATERWAY_FILE = CONTEXT / "mayon_waterways_osm_candidate.geojson"
QUARRY_FILE = CONTEXT / "osm_quarries_candidate.geojson"
PLACE_FILE = CONTEXT / "osm_places_candidate.geojson"
SITES_FILE = CONTEXT / "channel_test_sites"
RAIN_FILE = RAW_FOLDER / "imerg" / "mayon_daily.json"
COVER_FILE = RAW_FOLDER / "context_download" / "false_alarm" / "worldcover.npy"
CROPLAND = 40  # ESA WorldCover class code
RAIN_DAYS = 120  # 2026-06-22 to 2026-10-19

# The nine track 111 pairs, and the two published track 104 pairs as a cross-check only (UTC).
TRACK_111_DATES = ["20260621", "20260703", "20260715", "20260727", "20260820", "20260901", "20260913", "20260925", "20261007", "20261019"]
TRACK_104_PAIRS = [("20260913", "20260925"), ("20261007", "20261019")]

# The fixed rules from docs/NIGHT_PLAN_4.md
FLAG_DB = 3.0
SENSITIVITY_DB = (4.0, 5.0)
MIN_QUARRY_PIXELS = 50
QUARRY_NEAR_CHANNEL_M = 300
STRIP_M = 200
QUIET_FROM_QUARRY_M = 500
MATCH_KM = 1
LAND_FROM_CHANNEL_M = 500
BANDS_KM = [(2, 4), (4, 6), (6, 8), (8, 10), (10, 14)]
CIRCLE_KM = 10
GO_RATIO, WEAK_RATIO, PAIRS_NEEDED = 2.0, 1.5, 5
# For the extra checks only, not the verdict
NEAR_LINE_M = 50
SAME_FLANK_DEGREES = 45
COVER_NAMES = {10: "Trees", 20: "Shrubs", 30: "Grass", 40: "Cropland", 50: "Built-up", 60: "Bare", 80: "Water", 90: "Wetland"}


def refuse_download(*args):
    """Passed to read_crop in place of the real download, so a missing crop stops the run."""
    raise RuntimeError("A crop isn't cached. Tonight nothing may be downloaded from ASF.")


def local_products():
    """List GCOV and GUNW names from the folders in raw/. This is not a search."""
    names = [path.name for path in RAW_FOLDER.iterdir() if path.is_dir()]
    gcov = [g for g in map(parse_gcov, names) if g]
    gunw = [g for g in map(parse_gunw, names) if g]
    return gcov, gunw


def find_pass(gcov, track, day):
    return next(p for p in gcov if p["track"] == track and p["acquired_start"][:10].replace("-", "") == day)


def find_gunw(gunw, track, first, second):
    """Find the GUNW between two passes, or None if there isn't one in raw/."""
    wanted = (first["acquired_start"][:10], second["acquired_start"][:10])
    for product in gunw:
        if product["track"] == track and (product["before_acquired_start"][:10], product["after_acquired_start"][:10]) == wanted:
            return product
    return None


def read_change(first, second, bounds, land):
    """Step 1: brightness change, from cached crops only."""
    crops = [read_crop(p["granule_id"], None, GCOV_GROUP, GCOV_DATASETS, bounds, opener=refuse_download) for p in (first, second)]
    return process_gcov(crops[0], crops[1], land)


def read_loss(result, track, previous, first, second, gunw, bounds):
    """Coherence loss for the site's rule, or None without a fair baseline (equal time gaps)."""
    if previous is None or not same_gap(previous, first, second):
        return None
    products = (find_gunw(gunw, track, previous, first), find_gunw(gunw, track, first, second))
    if None in products:
        return None
    crops = [read_crop(p["granule_id"], None, GUNW_GROUP, GUNW_DATASETS, bounds, opener=refuse_download) for p in products]
    return compute_coherence_loss(crops[0], crops[1], result["x"], result["y"], result["epsg"])


def to_utm_shape(geometry, epsg):
    """Move a shape from longitude and latitude onto the radar's map projection, in metres."""
    return move_points(geometry, Transformer.from_crs(4326, epsg, always_xy=True))


def move_points(geometry, transformer):
    """Run every point of a shape through a map-projection conversion."""
    def convert(points):
        xs, ys = transformer.transform(points[:, 0], points[:, 1])
        return np.column_stack([xs, ys])
    return transform_points(geometry, convert)


def burn(shapes, result, all_touched=False):
    """Mark the pixels of the radar grid that a list of UTM shapes covers."""
    corner = from_origin(result["x"][0] - result["spacing_x_m"] / 2, result["y"][0] + result["spacing_y_m"] / 2,
                         result["spacing_x_m"], result["spacing_y_m"])
    burned = rasterize([(item, 1) for item in shapes], out_shape=result["change_db"].shape, transform=corner,
                       fill=0, dtype="uint8", all_touched=all_touched)
    return burned.astype(bool)


def metres_from(mask, result):
    """Give each pixel its distance in metres to the nearest marked pixel."""
    return ndimage.distance_transform_edt(~mask, sampling=(result["spacing_y_m"], result["spacing_x_m"]))


def summit_km(result, config):
    """Give each pixel its distance from the summit in km."""
    x0, y0 = Transformer.from_crs(4326, result["epsg"], always_xy=True).transform(config["summit_lon"], config["summit_lat"])
    xs, ys = np.meshgrid(result["x"], result["y"])
    return np.hypot(xs - x0, ys - y0) / 1000


def nearest_place(point_utm, places):
    """Return the nearest OSM place's name and its distance in km."""
    place = min(places, key=lambda item: point_utm.distance(item["point"]))
    return place["name"], round(point_utm.distance(place["point"]) / 1000, 1)


def load_quarries(result, config, channel_lines, places):
    """Measure every OSM quarry and decide which are kept. Returns the table's rows, with shapes."""
    features = json.loads(QUARRY_FILE.read_text(encoding="utf-8"))["features"]
    channels = unary_union(channel_lines)
    distance = summit_km(result, config)
    rows = []
    for feature in features:
        polygon = to_utm_shape(shape(feature["geometry"]), result["epsg"]).buffer(0)
        pixels = burn([polygon], result)
        centre = polygon.representative_point()
        place, place_km = nearest_place(centre, places)
        row = {"osm_id": feature["properties"]["osm_id"], "name": feature["properties"].get("name"),
               "area_ha": round(polygon.area / 10_000, 2), "radar_pixels": int(pixels.sum()),
               "summit_km": round(float(np.median(distance[pixels])), 2) if pixels.any() else None,
               "channel_m": round(polygon.distance(channels)), "nearest_place": place, "nearest_place_km": place_km,
               "polygon": polygon, "pixels": pixels, "lonlat": shape(feature["geometry"])}
        reasons = []
        if row["radar_pixels"] < MIN_QUARRY_PIXELS:
            reasons.append(f"under {MIN_QUARRY_PIXELS} pixels")
        if row["channel_m"] > QUARRY_NEAR_CHANNEL_M:
            reasons.append(f"over {QUARRY_NEAR_CHANNEL_M} m from a channel line")
        row["kept"], row["dropped_because"] = not reasons, "; ".join(reasons) or None
        rows.append(row)
    return rows


def quiet_masks(kept, all_quarries, strip, distance, result):
    """For each kept quarry: channel-strip pixels far from every quarry, at about its distance.

    Dropped quarries count too: their ground may have changed, so they can't be quiet.
    """
    any_quarry = np.zeros(strip.shape, dtype=bool)
    for row in all_quarries:
        any_quarry |= row["pixels"]
    far = metres_from(any_quarry, result) > QUIET_FROM_QUARRY_M if any_quarry.any() else np.ones(strip.shape, dtype=bool)
    return [strip & far & (np.abs(distance - row["summit_km"]) <= MATCH_KM) for row in kept]


def fraction(flagged, area, has_value):
    """Flagged pixels / pixels with a radar value in an area. None if the area has none."""
    count = np.count_nonzero(area & has_value)
    return float(np.count_nonzero(flagged & area)) / count if count else None


def ratio(top, bottom):
    """Divide two fractions. Quarry flags over zero quiet flags counts as infinite, written None + a note."""
    if top is None or bottom is None:
        return None
    if bottom == 0:
        return float("inf") if top > 0 else None
    return top / bottom


def part_a_pair(flags, has_value, kept, quiet):
    """Fractions for quarries and for their matched quiet stretches, weighted by quarry size."""
    usable = [(row, area) for row, area in zip(kept, quiet) if np.count_nonzero(row["pixels"] & has_value)]
    weights = np.array([np.count_nonzero(row["pixels"] & has_value) for row, _ in usable], dtype=float)
    weights /= weights.sum()
    all_quarries = np.zeros(has_value.shape, dtype=bool)
    for row, _ in usable:
        all_quarries |= row["pixels"]
    out = {}
    for name, flagged in flags.items():
        quarry = fraction(flagged, all_quarries, has_value)
        matched = [fraction(flagged, area, has_value) for _, area in usable]
        quiet_value = float(sum(w * m for w, m in zip(weights, matched)))
        out[name] = {"quarry": quarry, "quiet": quiet_value, "ratio": ratio(quarry, quiet_value)}
    return out


def part_c_pair(flagged, has_value, strip, land_far, distance):
    """Compare channel strips with land away from channels, band by band and as one number."""
    bands, top, bottom, weight_total = [], 0.0, 0.0, 0
    for low, high in BANDS_KM:
        band = (distance >= low) & (distance < high)
        in_strip = fraction(flagged, strip & band, has_value)
        on_land = fraction(flagged, land_far & band, has_value)
        weight = int(np.count_nonzero(strip & band & has_value))
        bands.append({"band_km": f"{low}-{high}", "strip": in_strip, "land": on_land, "ratio": ratio(in_strip, on_land), "strip_pixels": weight})
        if in_strip is not None and on_land is not None:
            top += weight * in_strip
            bottom += weight * on_land
            weight_total += weight
    return {"strip": top / weight_total, "land": bottom / weight_total, "ratio": ratio(top, bottom), "bands": bands}


def site_rule_flags(result, loss, config):
    """The site's current provisional rule: either signal passing its threshold."""
    thresholds = config["thresholds"]
    classes = classify(result["change_db"], loss, result["reasons"], thresholds["brightness_threshold_db"],
                       thresholds["coherence_loss_threshold"])
    return np.isin(classes, (LOW, HIGH))


def flag_sets(change, site_flags):
    """Every way of flagging a pixel that the report needs. The verdict uses only combined_3."""
    with np.errstate(invalid="ignore"):
        sets = {"combined_3": np.abs(change) >= FLAG_DB, "brighter_3": change >= FLAG_DB, "darker_3": change <= -FLAG_DB}
        for value in SENSITIVITY_DB:
            sets[f"combined_{value:.0f}"] = np.abs(change) >= value
    sets["site_rule"] = site_flags
    return sets


def circle_share(flagged, strip, distance):
    """Of what the 10 km circle flags, what share would a channel-strip mask keep?"""
    circle = distance <= CIRCLE_KM
    return float(np.count_nonzero(flagged & circle & strip)) / max(int(np.count_nonzero(flagged & circle)), 1)


def cover_on_grid(result, bounds):
    """Look up the false-alarm study's WorldCover grid at each radar pixel (nearest cell)."""
    cover = np.load(COVER_FILE)
    to_lonlat = Transformer.from_crs(result["epsg"], 4326, always_xy=True)
    xs, ys = np.meshgrid(result["x"], result["y"])
    lons, lats = to_lonlat.transform(xs, ys)
    rows = np.clip(((bounds[3] - lats) / (bounds[3] - bounds[1]) * cover.shape[0]).astype(int), 0, cover.shape[0] - 1)
    columns = np.clip(((lons - bounds[0]) / (bounds[2] - bounds[0]) * cover.shape[1]).astype(int), 0, cover.shape[1] - 1)
    return cover[rows, columns]


def pair_rain(first, second, rain, strip, result):
    """Rain between two passes: days after the first pass, up to and including the second pass's day.

    IMERG days run midnight to midnight UTC, and these passes are at about 21:13 UTC, so a first
    pass's day had under 3 hours left. Each 0.1-degree cell is weighted by the strip pixels inside it.
    """
    to_lonlat = Transformer.from_crs(result["epsg"], 4326, always_xy=True)
    xs, ys = np.meshgrid(result["x"], result["y"])
    lons, lats = to_lonlat.transform(xs[strip], ys[strip])
    cell_lons, cell_lats = np.array(rain["lons"]), np.array(rain["lats"])
    columns = np.abs(lons[:, None] - cell_lons).argmin(axis=1)
    rows = np.abs(lats[:, None] - cell_lats).argmin(axis=1)
    weights = np.zeros((len(cell_lons), len(cell_lats)))
    np.add.at(weights, (columns, rows), 1)
    weights /= weights.sum()
    days = [day for day in sorted(rain["days"]) if first["acquired_start"][:10] < day <= second["acquired_start"][:10]]
    totals = {day: float((np.array(rain["days"][day]["rain_mm"], dtype=float) * weights).sum()) for day in days}
    wettest = max(totals, key=totals.get)
    return {"days": len(days), "total_mm": round(sum(totals.values()), 1), "wettest_day": wettest,
            "wettest_mm": round(totals[wettest], 1), "mm_per_day": round(sum(totals.values()) / len(days), 1)}


def rain_thirds(rows):
    """Label each pair's total as low, middle or high: for the report only, not a heavy-rain limit."""
    ordered = sorted(rows, key=lambda row: row["rain"]["total_mm"])
    for position, row in enumerate(ordered):
        row["rain"]["third"] = ("low", "middle", "high")[position // 3]


def pair_label(first, second):
    return f"{first[4:6]}-{first[6:]} → {second[4:6]}-{second[6:]}"


def save_sites(kept, dropped, quiet_union, result):
    """Save the test areas as geojson and as KML, so the owner can open them in Google Earth."""
    to_lonlat = Transformer.from_crs(result["epsg"], 4326, always_xy=True)
    corner = from_origin(result["x"][0] - result["spacing_x_m"] / 2, result["y"][0] + result["spacing_y_m"] / 2,
                         result["spacing_x_m"], result["spacing_y_m"])
    # Quiet stretches are pixels, so merge them into outlines. Simplifying by 10 m keeps the files small.
    pieces = [shape(geometry) for geometry, value in raster_shapes(quiet_union.astype("uint8"), mask=quiet_union, transform=corner) if value]
    quiet_outline = move_points(unary_union(pieces).simplify(10), to_lonlat)
    features = [{"type": "Feature", "properties": {"kind": "quarry mapped in OpenStreetMap, kept", "osm_id": row["osm_id"], "name": row["name"], "area_ha": row["area_ha"]},
                 "geometry": mapping(row["lonlat"])} for row in kept]
    features += [{"type": "Feature", "properties": {"kind": "quarry mapped in OpenStreetMap, dropped", "osm_id": row["osm_id"], "name": row["name"], "area_ha": row["area_ha"], "why": row["dropped_because"]},
                  "geometry": mapping(row["lonlat"])} for row in dropped]
    features.append({"type": "Feature", "properties": {"kind": "quiet stretches (control)"}, "geometry": mapping(quiet_outline)})
    collection = {"type": "FeatureCollection", "note": "Test areas for the night 4 channel test. Quarries (c) OpenStreetMap contributors, ODbL.", "features": features}
    SITES_FILE.with_suffix(".geojson").write_text(json.dumps(collection, ensure_ascii=False) + "\n", encoding="utf-8")
    SITES_FILE.with_suffix(".kml").write_text(to_kml(features), encoding="utf-8")


def kml_polygon(polygon):
    def ring(points):
        return " ".join(f"{x:.6f},{y:.6f},0" for x, y in points)
    holes = "".join(f"<innerBoundaryIs><LinearRing><coordinates>{ring(r.coords)}</coordinates></LinearRing></innerBoundaryIs>" for r in polygon.interiors)
    return f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{ring(polygon.exterior.coords)}</coordinates></LinearRing></outerBoundaryIs>{holes}</Polygon>"


def to_kml(features):
    """Write a small KML by hand: quarries kept in red, dropped in orange, quiet stretches in blue."""
    colors = {"kept": "990000ff", "dropped": "9900a5ff", "quiet": "99ff7f00"}
    styles = "".join(f'<Style id="{name}"><LineStyle><color>ff{code[2:]}</color><width>2</width></LineStyle><PolyStyle><color>{code}</color></PolyStyle></Style>' for name, code in colors.items())
    marks = []
    for feature in features:
        kind = feature["properties"]["kind"]
        style = "quiet" if kind.startswith("quiet") else "dropped" if "dropped" in kind else "kept"
        title = feature["properties"].get("name") or feature["properties"].get("osm_id") or kind
        geometry = shape(feature["geometry"])
        parts = list(getattr(geometry, "geoms", [geometry]))
        body = "".join(kml_polygon(part) for part in parts)
        marks.append(f"<Placemark><name>{escape_text(title)}</name><description>{escape_text(kind)}</description><styleUrl>#{style}</styleUrl><MultiGeometry>{body}</MultiGeometry></Placemark>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Mayon channel test sites</name>'
            f"<description>Quarries (c) OpenStreetMap contributors, ODbL.</description>{styles}{''.join(marks)}</Document></kml>\n")


def escape_text(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def count_at_least(rows, limit):
    return sum(1 for value in rows if value is not None and value >= limit)


def decide(quarry_ratios, channel_ratios, has_quarries):
    """The fixed verdict rules from docs/NIGHT_PLAN_4.md."""
    if not has_quarries:
        return "NOT TESTED"
    if count_at_least(quarry_ratios, GO_RATIO) >= PAIRS_NEEDED:
        return "GO"
    if count_at_least(channel_ratios, WEAK_RATIO) >= PAIRS_NEEDED:
        return "WEAK"
    return "NO-GO"


def draw_figure(output, kept, dropped, quiet_union, channel_lines, result, config):
    """Left: the test sites on a map. Right: quarry against quiet for each pair, with rain marked."""
    figure, (left, right) = plt.subplots(1, 2, figsize=(14, 6.2), gridspec_kw={"width_ratios": [1, 1.35]})
    extent = [result["x"][0] / 1000, result["x"][-1] / 1000, result["y"][-1] / 1000, result["y"][0] / 1000]
    for line in channel_lines:
        xs, ys = line.xy
        left.plot(np.array(xs) / 1000, np.array(ys) / 1000, color="#9db7c9", linewidth=0.5, zorder=1)
    left.imshow(np.ma.masked_where(~quiet_union, quiet_union), extent=extent, cmap="Blues", vmin=0, vmax=1.2, interpolation="nearest", zorder=2)
    for rows, color in ((kept, "#D55E00"), (dropped, "#E69F00")):
        for row in rows:
            for part in getattr(row["polygon"], "geoms", [row["polygon"]]):
                xs, ys = part.exterior.xy
                left.fill(np.array(xs) / 1000, np.array(ys) / 1000, color=color, zorder=3)
    x0, y0 = Transformer.from_crs(4326, result["epsg"], always_xy=True).transform(config["summit_lon"], config["summit_lat"])
    left.plot(x0 / 1000, y0 / 1000, marker="^", color="black", zorder=4)
    left.annotate("Summit", (x0 / 1000, y0 / 1000), textcoords="offset points", xytext=(6, 4))
    left.set(xlabel="UTM 51N east (km)", ylabel="UTM 51N north (km)", title="Test sites: quarries mapped in OpenStreetMap (orange), quiet stretches (blue)", aspect="equal",
             xlim=extent[:2], ylim=extent[2:])
    left.title.set_fontsize(10)
    rows = output["part_a"]["pairs"]
    positions = np.arange(len(rows))
    right.bar(positions - 0.2, [100 * r["combined_3"]["quarry"] for r in rows], 0.38, color="#D55E00", label="Quarries")
    right.bar(positions + 0.2, [100 * r["combined_3"]["quiet"] for r in rows], 0.38, color="#0072B2", label="Quiet stretches")
    right.set_xticks(positions, [f"{r['label']}\n{output['rain_by_pair'][r['label']]['total_mm']:.0f} mm, {output['rain_by_pair'][r['label']]['third']}" if output["rain_by_pair"] else r["label"] for r in rows], rotation=60, fontsize=7.5, ha="right")
    rain_note = "with rain between passes" if output["rain_by_pair"] else "no rain marked: IMERG access failed"
    right.set(ylabel="Flagged pixels, ±3.0 dB (%)", title=f"Quarry against quiet, track 111 ({rain_note})")
    right.title.set_fontsize(10)
    right.legend(frameon=False)
    right.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    figure.savefig(REPORTS / "channel-test.png", dpi=130)
    plt.close(figure)


def study_pair(first, second, previous, gunw, track, bounds, land, config, masks):
    """Measure one pair everywhere."""
    result = read_change(first, second, bounds, land)
    has_value = result["reasons"] == HAS_VALUE
    loss = read_loss(result, track, previous, first, second, gunw, bounds)
    flags = flag_sets(result["change_db"], site_rule_flags(result, loss, config))
    row = {"label": pair_label(first["acquired_start"][:10].replace("-", ""), second["acquired_start"][:10].replace("-", "")),
           "coherence_in_site_rule": loss is not None, "share_with_radar_value": float(has_value[masks["land"]].mean())}
    if masks["kept"]:
        by_flag = part_a_pair(flags, has_value, masks["kept"], masks["quiet"])
        row.update(by_flag)
        # A check on the method: the same ratio pooled, and with no-value pixels counted as "all pixels".
        any_quarry = np.logical_or.reduce([q["pixels"] for q in masks["kept"]])
        quiet_union = np.logical_or.reduce(masks["quiet"])
        every = np.ones(has_value.shape, dtype=bool)
        row["check_pooled_ratio"] = ratio(fraction(flags["combined_3"], any_quarry, has_value), fraction(flags["combined_3"], quiet_union, has_value))
        row["check_all_pixels_ratio"] = ratio(fraction(flags["combined_3"], any_quarry, every), fraction(flags["combined_3"], quiet_union, every))
        row["quarry_value_share"] = float(has_value[any_quarry].mean())
        row["quarry_flagged_pixels"] = int(np.count_nonzero(flags["combined_3"] & any_quarry))
        row["per_quarry"] = {q["osm_id"]: fraction(flags["combined_3"], q["pixels"], has_value) for q in masks["kept"]}
        # Extra checks, added after seeing the verdict. They can't change it: they ask how much it leans on one choice.
        only_3 = {"combined_3": flags["combined_3"]}
        row["check_quiet_near_line"] = part_a_pair(only_3, has_value, masks["kept"], masks["quiet_near_line"])["combined_3"]["ratio"]
        row["check_quiet_same_flank"] = part_a_pair(only_3, has_value, masks["kept"], masks["quiet_same_flank"])["combined_3"]["ratio"]
        row["check_leave_one_out"] = {
            q["osm_id"]: part_a_pair(only_3, has_value, masks["kept"][:i] + masks["kept"][i + 1:], masks["quiet"][:i] + masks["quiet"][i + 1:])["combined_3"]["ratio"]
            for i, q in enumerate(masks["kept"])}
    row["part_c"] = {name: part_c_pair(flagged, has_value, masks["strip"], masks["land_far"], masks["distance"]) for name, flagged in flags.items()}
    row["circle_share"] = {name: circle_share(flags[name], masks["strip"], masks["distance"]) for name in ("combined_3", "site_rule")}
    return row, result


def build_masks(result, config, bounds, land, channel_lines, places):
    """Work out the test areas once. Both tracks share one radar grid, which is checked in main."""
    distance = summit_km(result, config)
    near_line = burn(channel_lines, result, all_touched=True)
    from_line = metres_from(near_line, result)
    is_land = land_mask(land, result["x"], result["y"], result["epsg"])
    strip = (from_line <= STRIP_M) & is_land
    land_far = (from_line > LAND_FROM_CHANNEL_M) & is_land
    rows = load_quarries(result, config, channel_lines, places)
    kept = [row for row in rows if row["kept"]]
    quiet = quiet_masks(kept, rows, strip, distance, result) if kept else []
    # For the extra checks: quiet cells closest to the line, or on the same side of the volcano,
    # where the radar looks at the ground from about the same angle.
    x0, y0 = Transformer.from_crs(4326, result["epsg"], always_xy=True).transform(config["summit_lon"], config["summit_lat"])
    xs, ys = np.meshgrid(result["x"], result["y"])
    bearing = np.degrees(np.arctan2(xs - x0, ys - y0)) % 360
    same_flank = []
    for row, area in zip(kept, quiet):
        centre = row["polygon"].representative_point()
        middle = np.degrees(np.arctan2(centre.x - x0, centre.y - y0)) % 360
        same_flank.append(area & (np.abs((bearing - middle + 180) % 360 - 180) <= SAME_FLANK_DEGREES))
    return {"distance": distance, "strip": strip, "land_far": land_far, "land": is_land, "rows": rows, "kept": kept, "quiet": quiet,
            "quiet_near_line": [area & (from_line <= NEAR_LINE_M) for area in quiet], "quiet_same_flank": same_flank}


def clean_number(value):
    """JSON has no infinity, so write it as text."""
    return "infinite" if value == float("inf") else value


def clean(data):
    if isinstance(data, dict):
        return {key: clean(value) for key, value in data.items()}
    if isinstance(data, list):
        return [clean(value) for value in data]
    return clean_number(data) if isinstance(data, float) else data


def cover_shares(cover, area):
    """What share of an area each WorldCover class takes up."""
    return {name: round(float((cover[area] == code).mean()), 3) for code, name in COVER_NAMES.items()}


def named_place_check(kept, places):
    """How far is each named place from the nearest kept quarry?"""
    result = {}
    for wanted in ("Budiao", "Maninila"):
        place = next((p for p in places if p["name"] == wanted), None)
        if place and kept:
            nearest = min(kept, key=lambda q: q["polygon"].distance(place["point"]))
            result[wanted] = {"nearest_quarry": nearest["osm_id"], "km": round(nearest["polygon"].distance(place["point"]) / 1000, 1)}
        else:
            result[wanted] = None
    return result


def load_rain():
    """Return the rain record only if every day was read, because a partial total would mislead."""
    if not RAIN_FILE.is_file():
        return None
    rain = json.loads(RAIN_FILE.read_text(encoding="utf-8"))
    return rain if len(rain["days"]) == RAIN_DAYS else None


def main():
    config = load_site("mayon")
    bounds, land = site_bounds(config), load_land("mayon")
    gcov, gunw = local_products()
    rain = load_rain()
    passes_111 = [find_pass(gcov, 111, day) for day in TRACK_111_DATES]
    first_result = read_change(passes_111[0], passes_111[1], bounds, land)
    to_metres = lambda g: to_utm_shape(g, first_result["epsg"])
    channel_lines = [to_metres(LineString(f["geometry"]["coordinates"])) for f in json.loads(WATERWAY_FILE.read_text(encoding="utf-8"))["features"]]
    places = [{"name": f["properties"]["name"], "kind": f["properties"]["place"], "point": to_metres(Point(f["geometry"]["coordinates"]))}
              for f in json.loads(PLACE_FILE.read_text(encoding="utf-8"))["features"]]
    masks = build_masks(first_result, config, bounds, land, channel_lines, places)
    has_quarries = bool(masks["kept"])
    quiet_union = np.logical_or.reduce(masks["quiet"]) if has_quarries else np.zeros(masks["strip"].shape, dtype=bool)
    cover = cover_on_grid(first_result, bounds)

    rows = []
    for index in range(9):
        previous = passes_111[index - 1] if index else None
        row, _ = study_pair(passes_111[index], passes_111[index + 1], previous, gunw, 111, bounds, land, config, masks)
        if rain:
            row["rain"] = pair_rain(passes_111[index], passes_111[index + 1], rain, masks["strip"], first_result)
        rows.append(row)
        print("Measured", row["label"], flush=True)
    if rain:
        rain_thirds(rows)

    cross = []
    for first_day, second_day in TRACK_104_PAIRS:
        first, second = find_pass(gcov, 104, first_day), find_pass(gcov, 104, second_day)
        row, result = study_pair(first, second, None, gunw, 104, bounds, land, config, masks)
        # The masks were made on track 111's grid, so the grids must be the same to reuse them.
        if not (np.array_equal(result["x"], first_result["x"]) and np.array_equal(result["y"], first_result["y"])):
            raise ValueError("Track 104 is on a different grid from track 111")
        cross.append(row)
        print("Measured track 104", row["label"], flush=True)

    quarry_ratios = [row["combined_3"]["ratio"] for row in rows] if has_quarries else []
    channel_ratios = [row["part_c"]["combined_3"]["ratio"] for row in rows]
    verdict = decide(quarry_ratios, channel_ratios, has_quarries)
    in_strip = masks["strip"] & (masks["distance"] >= BANDS_KM[0][0]) & (masks["distance"] < BANDS_KM[-1][1])
    circle = masks["distance"] <= CIRCLE_KM
    output = {
        "status": "a test, not a feature; nothing on the site changed; no NISAR product was searched or opened except cached crops from before the cutoff",
        "verdict": verdict,
        "pairs_quarry_ratio_at_least_2": count_at_least(quarry_ratios, GO_RATIO),
        "pairs_channel_ratio_at_least_1_5": count_at_least(channel_ratios, WEAK_RATIO),
        "quarries": [{key: value for key, value in row.items() if key not in ("polygon", "pixels", "lonlat")} for row in masks["rows"]],
        "areas_ha": {"quarries_kept": float(sum(np.count_nonzero(q["pixels"]) for q in masks["kept"])) / 100,
                     "quiet_stretches": float(np.count_nonzero(quiet_union)) / 100,
                     "smallest_match_for_a_quarry": float(min((np.count_nonzero(q) for q in masks["quiet"]), default=0)) / 100},
        "farmland_share_of_strip": float((cover[in_strip] == CROPLAND).mean()),
        "farmland_share_of_quiet": float((cover[quiet_union] == CROPLAND).mean()) if has_quarries else None,
        "farmland_share_of_land_far": float((cover[masks["land_far"] & (masks["distance"] < BANDS_KM[-1][1])] == CROPLAND).mean()),
        "named_places": named_place_check(masks["kept"], places),
        "land_cover_shares": {"quarries": cover_shares(cover, np.logical_or.reduce([q["pixels"] for q in masks["kept"]])) if has_quarries else None,
                              "quiet": cover_shares(cover, quiet_union) if has_quarries else None,
                              "strip": cover_shares(cover, in_strip),
                              "land_far": cover_shares(cover, masks["land_far"] & (masks["distance"] < BANDS_KM[-1][1]))},
        "strip_share_of_circle_land": float(np.count_nonzero(masks["strip"] & circle)) / max(int(np.count_nonzero(masks["land"] & circle)), 1),
        "rain_source": {key: rain[key] for key in ("short_name", "version", "bytes_fetched", "units")} | {"days": len(rain["days"])} if rain else None,
        "rain_by_pair": {row["label"]: row["rain"] for row in rows} if rain else {},
        "part_a": {"pairs": rows if has_quarries else []},
        "pairs": rows,
        "track_104_cross_check": cross,
    }
    if has_quarries:
        save_sites(masks["kept"], [r for r in masks["rows"] if not r["kept"]], quiet_union, first_result)
        draw_figure(output, masks["kept"], [r for r in masks["rows"] if not r["kept"]], quiet_union, channel_lines, first_result, config)
    output.pop("part_a")
    (REPORTS / "channel-test.json").write_text(json.dumps(clean(output), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Verdict:", verdict, quarry_ratios, channel_ratios)


if __name__ == "__main__":
    main()

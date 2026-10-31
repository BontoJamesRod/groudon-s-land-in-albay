"""Match the lahar channels PHIVOLCS names to OpenStreetMap waterway lines. Candidates only.

Run from the project folder:
    python pipeline/reports/channel_names.py

OSM has almost no names for these channels, so most matches are reasoned from geography:
1. Start from a hand-picked top segment for each channel, chosen by looking at which lines
   pass the channel's barangay on the right side of the volcano. CHANNELS lists every choice.
2. Follow the lines downhill. OSM draws waterways in the direction they flow, so each
   segment's last point leads to the next segment.
3. Stop at the last point inside the town PHIVOLCS gives for that channel.
4. Give a confidence by the fixed rules in confidence() below.

It reads OSM files already in pipeline/context and the site's town outlines, and uses no radar
data and no network. Waterways and places are (c) OpenStreetMap contributors, ODbL.
"""
import json
import math
from pathlib import Path

from pyproj import Transformer
from shapely import transform as transform_points
from shapely.geometry import LineString, Point, mapping, shape
from shapely.ops import substring

REPO = Path(__file__).resolve().parents[2]
CONTEXT = REPO / "pipeline" / "context"
WATERWAY_FILE = CONTEXT / "mayon_waterways_osm_candidate.geojson"
PLACE_FILE = CONTEXT / "osm_places_candidate.geojson"
TOWN_FILE = REPO / "site" / "data" / "sites" / "mayon" / "towns.geojson"
SITE_FILE = REPO / "pipeline" / "sites" / "mayon.json"
OUT_FILE = CONTEXT / "channel_name_candidates"
REPORT_FILE = REPO / "pipeline" / "reports" / "channel-names.md"
UTM_51N = 32651

# The fixed confidence rules
NEAR_PLACE_M = 400
UPPER_SLOPE_KM = 5
SHARED_M = 100

# name: the top OSM segment, the barangay that anchors it, the town PHIVOLCS gives,
# whether an OSM name tag supports it, and what to check by eye.
CHANNELS = [
    {"name": "Mi-isi", "head": 553506874, "place": "Mi-isi", "town": "Daraga", "tag": None,
     "check": "Two Yawa River branches pass Mi-isi about equally closely (the other starts at OSM way 554777832). Which one is the gully on the south flank?"},
    {"name": "Bonga", "head": 553506868, "place": "Bogña", "town": "Legazpi City", "tag": None,
     "check": "Is OSM's Bogña the Bonga PHIVOLCS means? OSM's village spelled Bonga is on the east-northeast flank and doesn't fit Legazpi. Does this line follow the southeast gully?"},
    {"name": "Basud", "head": 554777833, "place": None, "town": "Santo Domingo", "tag": "Basud River",
     "check": "Confirm the top joins correctly. OSM also has a separate 'Basud RIver' tributary (way 555279291), left out here. The villages called Basud in OSM are on other rivers."},
    {"name": "Lidong", "head": 554777823, "place": "Lidong", "town": "Santo Domingo", "tag": None,
     "check": "Is this river separate from Basud, or does PHIVOLCS treat them as one system (older lists say Basud-Lidong)?"},
    {"name": "Mabinit", "head": 86384638, "place": "Mabinit", "town": "Legazpi City", "tag": None,
     "check": "This line and Bonga's join, so they can't both be certain. Which branch really passes Mabinit? The line is 650 m away, which is far for a village named after its channel."},
    {"name": "Matanag", "head": 554777826, "place": "Matanag", "town": "Legazpi City", "tag": None,
     "check": "OSM's line only starts 6 km from the summit. Is there a channel higher up that OSM hasn't drawn?"},
    {"name": "Buyuan", "head": 553528103, "place": "Padang", "town": "Legazpi City", "tag": None,
     "check": "Weakest guess: OSM has no place called Buyuan, so Padang stands in for it. It's chosen only as the other long line near Padang. Find the real Buyuan river first."},
    {"name": "Padang", "head": 553670459, "place": "Padang", "town": "Legazpi City", "tag": None,
     "check": "Does it reach Padang's river, and might Padang and Buyuan be the wrong way round? PHIVOLCS has also written them as one channel, Buyuan-Padang."},
    {"name": "Masarawag", "head": 1385620645, "place": "Masarawag", "town": "Guinobatan", "tag": None,
     "check": "This line passes closer to Maninila than to Masarawag. Look for the true channel beside Masarawag; OSM's lines closest to it start only about 8 km out."},
    {"name": "Maninila", "head": 1385620639, "place": "Maninila", "town": "Guinobatan", "tag": None,
     "check": "Does it run through Maninila? It later joins the San Francisco River, so check that this name and that one are the same river further down."},
]


def confidence(tag_matches, place_m, start_km, reaches_town, shared_with):
    """The fixed rules, so that every match is judged the same way.

    high: an OSM name tag says so, and the line reaches the right town.
    medium: no name, but it passes the barangay, starts on the upper slope, reaches the town,
    and is not also used by another channel.
    low: anything else.
    """
    if tag_matches and reaches_town:
        return "high"
    clear = place_m is not None and place_m <= NEAR_PLACE_M and start_km <= UPPER_SLOPE_KM
    return "medium" if clear and reaches_town and not shared_with else "low"


def follow_downhill(head, segments):
    """Join segments from `head` down. Returns the ids used and the joined points.

    A segment's last point is a shared point of the next one, which may be partway along it,
    so only the part of the next segment below that point is added.
    """
    points_at = {}
    for segment_id, points in segments.items():
        for index, point in enumerate(points):
            points_at.setdefault(point, []).append((segment_id, index))
    ids, joined = [head], list(segments[head])
    while True:
        options = [(s, i) for s, i in points_at[joined[-1]] if s not in ids and i < len(segments[s]) - 1]
        if not options:
            return ids, joined
        # Prefer a segment that starts here over one this line only touches partway.
        next_id, index = min(options, key=lambda option: (option[1], option[0]))
        ids.append(next_id)
        joined += segments[next_id][index + 1:]


def cut_at_town(line, town):
    """Keep the line down to its last point inside the town. Returns the line and if it got there."""
    inside = line.intersection(town)
    if inside.is_empty:
        return line, False
    last_point = max(line.project(Point(xy)) for part in getattr(inside, "geoms", [inside]) for xy in part.coords)
    return substring(line, 0, last_point), True


def bearing(x, y, summit):
    """Compass bearing from the summit, in degrees."""
    return round(math.degrees(math.atan2(x - summit[0], y - summit[1])) % 360)


def nearest_town(line, towns):
    """Name the town that the line's lowest point is in."""
    end = Point(line.coords[-1])
    return min(towns, key=lambda name: towns[name].distance(end))


def reason_text(item, row):
    """Say in words why the match got its confidence."""
    if item["tag"]:
        parts = [f"OSM name tag '{item['tag']}'"]
    elif row["other_names"]:
        parts = [f"no matching OSM name tag (parts are tagged {', '.join(row['other_names'])})"]
    else:
        parts = ["no OSM name tag"]
    if row["place_m"] is not None:
        parts.append(f"passes {row['place_m']} m from {item['place']}")
    parts.append(f"on the {row['bearing']}° flank")
    parts.append(f"{'reaches' if row['reaches_town'] else 'does not reach'} {item['town']}")
    if row["shared_with"]:
        parts.append(f"shares its line with {', '.join(row['shared_with'])}")
    return "; ".join(parts)


def load_inputs():
    """Read the OSM lines, places and town outlines, all moved onto UTM metres."""
    to_utm = Transformer.from_crs(4326, UTM_51N, always_xy=True)

    def utm_shape(geometry):
        def convert(points):
            xs, ys = to_utm.transform(points[:, 0], points[:, 1])
            return [[x, y] for x, y in zip(xs, ys)]
        return transform_points(shape(geometry), convert)

    features = json.loads(WATERWAY_FILE.read_text(encoding="utf-8"))["features"]
    # Rounding to 1 m lets the same OSM point match itself in every segment.
    segments = {f["properties"]["osm_id"]: [(round(a), round(b)) for a, b in (to_utm.transform(*c) for c in f["geometry"]["coordinates"])] for f in features}
    tags = {f["properties"]["osm_id"]: f["properties"]["name"] for f in features}
    places = {}
    for feature in json.loads(PLACE_FILE.read_text(encoding="utf-8"))["features"]:
        places.setdefault(feature["properties"]["name"], []).append(Point(to_utm.transform(*feature["geometry"]["coordinates"])))
    towns = {f["properties"]["name"]: utm_shape(f["geometry"]).buffer(0) for f in json.loads(TOWN_FILE.read_text(encoding="utf-8"))["features"]}
    site = json.loads(SITE_FILE.read_text(encoding="utf-8"))
    return segments, tags, places, towns, to_utm.transform(site["summit_lon"], site["summit_lat"])


def measure_all():
    """Build each channel's line and work out everything except the shared-line check."""
    segments, tags, places, towns, summit = load_inputs()
    rows = []
    for item in CHANNELS:
        ids, points = follow_downhill(item["head"], segments)
        line, reaches = cut_at_town(LineString(points), towns[item["town"]])
        place = places[item["place"]] if item["place"] else []
        place_m = round(min(line.distance(p) for p in place)) if place else None
        middle = line.interpolate(0.5, normalized=True)
        kept = [i for i in ids if line.buffer(2).intersection(LineString(segments[i])).length > 1]
        rows.append({"channel": item["name"], "osm_ids": kept, "line": line, "length_km": round(line.length / 1000, 1),
                     "start_km": round(Point(line.coords[0]).distance(Point(summit)) / 1000, 1), "reaches_town": reaches,
                     # A line cut at a town's edge touches the next town too, so name the one it was cut for.
                     "town_at_end": item["town"] if reaches else nearest_town(line, towns),
                     "other_names": sorted({tags[i] for i in kept if tags[i]}),
                     "place_m": place_m, "bearing": bearing(middle.x, middle.y, summit),
                     "tag_matches": bool(item["tag"]) and all(tags[i] and tags[i].lower() == item["tag"].lower() for i in kept)})
    for row in rows:
        row["shared_with"] = [other["channel"] for other in rows if other is not row
                              and row["line"].intersection(other["line"].buffer(5)).length > SHARED_M]
        row["confidence"] = confidence(row["tag_matches"], row["place_m"], row["start_km"], row["reaches_town"], row["shared_with"])
    return rows


def to_lonlat(line):
    """Move a line back to longitude and latitude."""
    back = Transformer.from_crs(UTM_51N, 4326, always_xy=True)
    return [[round(x, 7), round(y, 7)] for x, y in (back.transform(*xy) for xy in line.coords)]


def save_geojson(rows):
    features = [{"type": "Feature", "properties": {key: row[key] for key in ("channel", "osm_ids", "length_km", "start_km", "town_at_end", "confidence", "reason")},
                 "geometry": {"type": "LineString", "coordinates": to_lonlat(row["line"])}} for row in rows]
    collection = {"type": "FeatureCollection", "note": "CANDIDATES only, not checked by eye. Data (c) OpenStreetMap contributors, ODbL.", "features": features}
    OUT_FILE.with_suffix(".geojson").write_text(json.dumps(collection, ensure_ascii=False) + "\n", encoding="utf-8")


def save_kml(rows):
    """Write a small KML by hand: high in green, medium in yellow, low in red. KML colours are aabbggrr."""
    colors = {"high": "ff00c800", "medium": "ff00d7ff", "low": "ff0000ff"}
    styles = "".join(f'<Style id="{name}"><LineStyle><color>{code}</color><width>4</width></LineStyle></Style>' for name, code in colors.items())
    marks = []
    for row in rows:
        points = " ".join(f"{x},{y},0" for x, y in to_lonlat(row["line"]))
        marks.append(f"<Placemark><name>{row['channel']} ({row['confidence']})</name><description>{row['reason']}</description>"
                     f"<styleUrl>#{row['confidence']}</styleUrl><LineString><tessellate>1</tessellate><coordinates>{points}</coordinates></LineString></Placemark>")
    OUT_FILE.with_suffix(".kml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Mayon channel name candidates</name>'
        f"<description>Candidates only. Data (c) OpenStreetMap contributors, ODbL.</description>{styles}{''.join(marks)}</Document></kml>\n", encoding="utf-8")


def save_report(rows):
    counts = {level: sum(1 for row in rows if row["confidence"] == level) for level in ("high", "medium", "low")}
    table = ["| Channel | OSM ids | Length (km) | Start from summit (km) | Town reached | Confidence | Reason | Check by eye |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row, item in zip(rows, CHANNELS):
        town = row["town_at_end"] if row["reaches_town"] else f"Not {item['town']}: ends in {row['town_at_end']}"
        table.append(f"| {row['channel']} | {', '.join(map(str, row['osm_ids']))} | {row['length_km']} | {row['start_km']} | {town} | {row['confidence']} | {row['reason']} | {item['check']} |")
    text = f"""# Channel names: PHIVOLCS channels matched to OpenStreetMap lines

**These are candidates, not a channel map: {counts['high']} high, {counts['medium']} medium and {counts['low']} low confidence.** Nothing has been checked by eye or against a hazard map. Open `pipeline/context/channel_name_candidates.kml` in Google Earth: green is high, yellow medium, red low.

{chr(10).join(table)}

## How confidence is set

- **High:** an OSM name tag says so, and the line reaches the town PHIVOLCS gives.
- **Medium:** no name, but it passes within {NEAR_PLACE_M} m of the barangay, starts within {UPPER_SLOPE_KM} km of the summit, reaches the town, and shares no more than {SHARED_M} m with another channel.
- **Low:** anything else.

## Limits

- I chose each line's top segment by hand from the lines near its barangay, so the rules grade that choice but don't make it. The choices are in `CHANNELS` in `channel_names.py`.
- Each line stops at the last point inside its town, so it can't show a channel's course beyond that.
- A village's name doesn't prove that a channel runs through it, and OSM place points are approximate.
- Where branches meet, only one route is followed, and the OSM lines themselves haven't been checked.
- Flow direction is taken from how OSM drew each line, which isn't always right.

## Sources

- Waterways and places: © OpenStreetMap contributors, ODbL. Using these lines in the app means attribution, and ODbL's share-alike terms should be read first.
- Which town each channel belongs to: search summaries of the [January 2026 PHIVOLCS advisory as reported by Rappler](https://www.rappler.com/philippines/phivolcs-mayon-kanlaon-volcano-lahar-update-advisory-january-16-2026/) and [GMA News](https://www.gmanetwork.com/news/topstories/regions/973047/phivolcs-issues-lahar-warning-for-mayon-volcano-amid-ada/story/). I didn't read the PHIVOLCS bulletin itself, and I found no newer full list.
- Town outlines: the site's `towns.geojson`.

To repeat: `python pipeline/reports/channel_names.py`
"""
    REPORT_FILE.write_text(text, encoding="utf-8")


def main():
    rows = measure_all()
    for row in rows:
        row["reason"] = reason_text(next(i for i in CHANNELS if i["name"] == row["channel"]), row)
        print(row["channel"], row["confidence"], row["length_km"], row["start_km"], row["town_at_end"], row["osm_ids"], row["reason"])
    save_geojson(rows)
    save_kml(rows)
    save_report(rows)


if __name__ == "__main__":
    main()

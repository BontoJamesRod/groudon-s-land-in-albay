"""Second try at matching channel names to OpenStreetMap lines. Candidates only: nothing is published.

Run from the project folder:
    python pipeline/reports/channel_names_v2.py

What's different from channel_names.py:
1. Each name is judged only by its own barangay, so one name can't borrow another place's evidence.
2. Where two named lines join, each stops at the join. Below it is the river they become, which is
   written as its own line and isn't given to either name.
3. Colours say how sure the match is. They say nothing about hazard.

It reads OSM files already in pipeline/context and the site's town outlines. It uses no radar data
and no network. Waterways and places are (c) OpenStreetMap contributors, ODbL.
"""
import json
import sys
from html import escape
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import LineString, Point

sys.path.insert(0, str(Path(__file__).resolve().parent))

from channel_names import (CONTEXT, SHARED_M, UTM_51N, WATERWAY_FILE, bearing, confidence,
                           cut_at_town, load_inputs, to_lonlat)

PLACE_FILE = CONTEXT / "osm_channel_places.geojson"
RECORD_FILE = CONTEXT / "mayon_channels.json"
OLD_CANDIDATES = CONTEXT / "channel_name_candidates.geojson"
OUT_FILE = CONTEXT / "channel_name_candidates_v2"
REPORT_FILE = Path(__file__).resolve().parent / "channel-names-v2.md"

# Ditches, canals and drains aren't channels off the volcano, so the network leaves them out.
CHANNEL_KINDS = ("river", "stream")
# A branch is a real alternative only if it starts this close to the summit and passes this close to the barangay.
OTHER_BRANCH_HEAD_KM = 6.5
OTHER_BRANCH_M = 1200
# Two branches this close to the barangay can't be told apart by distance.
TIE_M = 100

# name: the place node that is its own evidence, the top OSM segment, the segments to prefer where the
# line forks, the town the source gives, and any OSM name tag that supports it. These are hand choices,
# made by looking at the network; the rules below only grade them.
CHANNELS = [
    {"name": "Bonga", "name_from": "PHIVOLCS 2026 reports", "place": 5345040663, "head": 86384638, "via": [553885144], "town": "Legazpi City", "tag": None,
     "check": "OSM spells this barangay Bogña, and treating it as PHIVOLCS's Bonga is my reading. Its place is east of this branch. PHIVOLCS names a Bonga Gully with new deposits, yet this branch starts lower than Mabinit's: are the two the wrong way round?"},
    {"name": "Mabinit", "name_from": "PHIVOLCS list in docs/05 section 8", "place": 5345040664, "head": 553506868, "via": [259704468], "town": "Legazpi City", "tag": None,
     "check": "The barangay lies below the join, nearly the same distance from both branches. Which branch does its gully follow?"},
    {"name": "Matanag", "name_from": "PHIVOLCS advisory of 16 January 2026", "place": 7260028626, "head": 554777826, "via": [92649866], "town": "Legazpi City", "tag": None,
     "check": "OSM's line starts only about 6 km from the summit. Does the gully run higher than OSM has drawn it?"},
    {"name": "Buyuan", "name_from": "PHIVOLCS list in docs/05 section 8 (as Buyuan-Padang)", "place": 7260028627, "head": 553668366, "via": [], "town": "Legazpi City", "tag": None,
     "check": "OSM spells this barangay Buyoan, with Buyuan as an alternate name. Two rivers join just above it, and this one is only a little closer. The other starts higher (way 553528103, the line the first try used). Which is it? PHIVOLCS has also written Buyuan-Padang as one channel."},
    {"name": "Masarawag", "name_from": "the first candidate list; not in docs/05 section 8", "place": 5345040682, "head": 1385620645, "via": [258418500], "town": "Guinobatan", "tag": None,
     "check": "This is the northern of three parallel rivers. It's far from the barangay, and small streams lie closer but start 8 km out. Is this the gully?"},
    {"name": "Maninila", "name_from": "PHIVOLCS list in docs/05 section 8", "place": 5345040680, "head": 1385620639, "via": [], "town": "Guinobatan", "tag": None,
     "check": "This is the southern of three parallel rivers. The middle one is tagged San Francisco River and also passes nearby. Which one is Maninila's?"},
    {"name": "Anoling", "name_from": "PHIVOLCS list in docs/05 section 8", "place": 5345041451, "head": 1385620641, "via": [553667497], "town": "Camalig", "tag": None,
     "check": "OSM's Anoling Elementary School is about 12 km out, far from this barangay point. Is the point in the right place?"},
    {"name": "Salugan", "name_from": "the owner's unverified hint list only", "place": 5345041455, "head": 553524865, "via": [554775454], "town": "Camalig", "tag": None,
     "check": "An unverified hint gave this name. Is it a named channel, and is it separate from Quirangay's?"},
    {"name": "Quirangay", "name_from": "PHIVOLCS list in docs/05 section 8", "place": 5345041456, "head": 553128085, "via": [], "town": "Camalig", "tag": None,
     "check": "OSM's line starts 5.7 km out. Way 555329754 starts higher but is farther from the barangay. Which one is the gully?"},
    {"name": "Tumpa", "name_from": "PHIVOLCS list in docs/05 section 8", "place": 5345041473, "head": 86384637, "via": [], "town": "Camalig", "tag": None,
     "check": "OSM's line starts 5.2 km out. Does the gully run higher than OSM has drawn it?"},
    {"name": "Busay", "name_from": "the owner's unverified hint list only", "place": 5345041426, "head": 554777832, "via": [250416508], "town": "Daraga", "tag": None,
     "check": "An unverified hint gave this name. It's the branch beside Mi-isi. OSM has other places called Busay, in Ligao and Malilipot; this is the one near Cagsawa."},
    {"name": "Bulawan", "name_from": "PHIVOLCS list in docs/05 section 8", "place": None, "head": 84641302, "via": [], "town": "Malilipot", "tag": "Bulawan River",
     "check": "OSM names it. A second Bulawan River branch (way 84641358) joins partway. Is this the main one?"},
    {"name": "Buang", "name_from": "PHIVOLCS list in docs/05 section 8", "place": 5345040370, "head": 84641344, "via": [], "town": "Tabaco City", "tag": None,
     "check": "OSM draws it as a stream. OSM's Buang Bridge is nearby: does it cross this line?"},
    {"name": "San Vicente", "name_from": "PHIVOLCS list in docs/05 section 8", "place": 5345040348, "head": 84641275, "via": [84641374], "town": "Tabaco City", "tag": None,
     "check": "The barangay is far from this line, and the streams beside it start about 11 km out. OSM also has a San Vicente road in Santo Domingo. Is this the right river?"},
    {"name": "Upper Nasisi", "name_from": "PHIVOLCS list in docs/05 section 8", "place": 5345040630, "head": 553506833, "via": [86384269], "town": "Ligao City", "tag": None,
     "check": "OSM calls the lower part Tobgon River. Does the name Upper Nasisi mean this river's upper part?"},
    {"name": "Upper Nabonton", "name_from": "PHIVOLCS list in docs/05 section 8", "place": 5345040629, "head": 553468069, "via": [553718200], "town": "Ligao City", "tag": None,
     "check": "Does the name Upper Nabonton mean this river's upper part?"},
]


def network_segments(segments):
    """Keep only rivers and streams from the OSM lines."""
    features = json.loads(WATERWAY_FILE.read_text(encoding="utf-8"))["features"]
    kinds = {f["properties"]["osm_id"]: f["properties"]["waterway"] for f in features}
    return {key: points for key, points in segments.items() if kinds[key] in CHANNEL_KINDS}


def follow_with_choices(head, segments, via=()):
    """Follow a line downhill from `head`, the way OSM drew it. Returns its points.

    OSM draws waterways in the direction they flow. `via` names a segment the line must reach, for
    a fork that distance alone would get wrong. Below that, the line stays on its segment, and at
    the end of one it takes the next, preferring one that starts there.
    """
    edges = {}
    for segment_id, points in segments.items():
        for index, (first, second) in enumerate(zip(points, points[1:])):
            edges.setdefault(first, []).append((segment_id, index, second))
    path = [segments[head][0]]
    if via:
        path = path_to_segment(path[0], segments[via[0]], edges)
    current = via[0] if via else head
    seen = set(path)
    while True:
        options = [edge for edge in edges.get(path[-1], ()) if edge[2] not in seen]
        if not options:
            return path
        current, _, step = min(options, key=lambda edge: (edge[0] != current, edge[1], edge[0]))
        path.append(step)
        seen.add(step)


def path_to_segment(start, segment, edges):
    """Find the shortest way downhill to a segment, entering it as near its top as possible.

    Entering at its far end would mean the line only touches the segment.
    """
    came_from = {start: None}
    queue = [start]
    for point in queue:
        for _, _, step in edges.get(point, ()):
            if step not in came_from:
                came_from[step] = point
                queue.append(step)
    for target in segment:
        if target in came_from:
            point, path = target, []
            while point is not None:
                path.append(point)
                point = came_from[point]
            return path[::-1]
    raise ValueError("That segment can't be reached by going downhill from the top segment")


def split_at_joins(paths, confirmed):
    """Cut each name's path at its first join with another named line, and say what it joined.

    Two lines that share their first point have the same top, so that isn't a join.
    """
    results = {}
    everything = {**paths, **confirmed}
    for name, points in paths.items():
        others = {key: (value[0], set(value)) for key, value in everything.items() if key != name}
        results[name] = (points, [])
        for index, point in enumerate(points[1:], start=1):
            hits = sorted(key for key, (first, members) in others.items() if point in members and first != point and first != points[0])
            if hits:
                results[name] = (points[: index + 1], hits)
                break
    return results


def read_places():
    """Read the barangay points, on UTM metres."""
    to_utm = Transformer.from_crs(4326, UTM_51N, always_xy=True)
    return {f["properties"]["osm_id"]: {**f["properties"], "point": Point(to_utm.transform(*f["geometry"]["coordinates"]))}
            for f in json.loads(PLACE_FILE.read_text(encoding="utf-8"))["features"]}


def confirmed_lines():
    """Read the lines the owner has confirmed, as points that match the network's."""
    to_utm = Transformer.from_crs(4326, UTM_51N, always_xy=True)
    record = json.loads(RECORD_FILE.read_text(encoding="utf-8"))
    names = {check["channel"] for check in record["checks"] if check["verdict"] == "confirmed"}
    lines = {}
    for feature in json.loads(OLD_CANDIDATES.read_text(encoding="utf-8"))["features"]:
        if feature["properties"]["channel"] in names:
            lines[feature["properties"]["channel"]] = [tuple(round(v) for v in to_utm.transform(*c)) for c in feature["geometry"]["coordinates"]]
    return lines


def other_branches(place, own_ways, segments, summit):
    """List other branches near the barangay that start high enough to be the real channel.

    A line's own ways, including the river below it, don't count against it.
    """
    ups = {}
    for points in segments.values():
        for first, second in zip(points, points[1:]):
            ups.setdefault(second, set()).add(first)
    rows = []
    for segment_id, points in segments.items():
        line = LineString(points)
        distance = line.distance(place)
        if distance > OTHER_BRANCH_M or segment_id in own_ways:
            continue
        near = min(points, key=lambda p: Point(p).distance(place))
        seen, stack = {near}, [near]
        while stack:
            for up in ups.get(stack.pop(), ()):
                if up not in seen:
                    seen.add(up)
                    stack.append(up)
        top = min(Point(p).distance(Point(summit)) for p in seen) / 1000
        if top <= OTHER_BRANCH_HEAD_KM:
            rows.append({"way": segment_id, "distance_m": round(distance), "top_km": round(top, 1)})
    return sorted(rows, key=lambda row: row["distance_m"])[:3]


def nearest_barangay(line, all_places):
    """Find the closest OSM place of any name, leaving out numbered zones, which say nothing about a channel."""
    named = [(line.distance(point), name) for name, points in all_places.items() for point in points
             if not any(mark in name for mark in ("Purok", "Zone", "Barangay"))]
    distance, name = min(named)
    return name, round(distance)


def ways_on(line, segments):
    """List the OSM ways a line runs along."""
    return [key for key, points in segments.items() if line.buffer(2).intersection(LineString(points)).length > 20]


def build_rows():
    """Build each name's line and measure the evidence for it."""
    segments, tags, all_places, towns, summit = load_inputs()
    segments = network_segments(segments)
    places = read_places()
    confirmed = confirmed_lines()
    paths = {item["name"]: follow_with_choices(item["head"], segments, item["via"]) for item in CHANNELS}
    split = split_at_joins(paths, confirmed)
    rows = []
    for item in CHANNELS:
        points, joins = split[item["name"]]
        line, reaches = cut_at_town(LineString(points), towns[item["town"]])
        kept = ways_on(line, segments)
        names = sorted({tags[i] for i in kept if tags[i]})
        place = places.get(item["place"])
        place_m = round(line.distance(place["point"])) if place else None
        middle = line.interpolate(0.5, normalized=True)
        rows.append({
            "channel": item["name"], "role": "name", "osm_ids": kept, "line": line, "joins": joins, "reaches_town": reaches,
            # The town's edge can come first, and then the line ends above the join.
            "stops_at_join": bool(joins) and Point(points[-1]).distance(Point(line.coords[-1])) < 1,
            "town": item["town"], "other_tags": names, "place": place, "place_m": place_m, "check": item["check"],
            "length_km": round(line.length / 1000, 1), "start_km": round(Point(line.coords[0]).distance(Point(summit)) / 1000, 1),
            "end_km": round(Point(line.coords[-1]).distance(Point(summit)) / 1000, 1), "bearing": bearing(middle.x, middle.y, summit),
            "tag_matches": bool(item["tag"]) and bool(kept) and all(tags[i] and tags[i].lower() == item["tag"].lower() for i in kept),
            "tag": item["tag"], "name_from": item["name_from"],
            "branches": other_branches(place["point"], ways_on(LineString(paths[item["name"]]), segments), segments, summit) if place else [],
        })
    grade(rows, places, confirmed)
    lowers = lower_rivers(rows, paths, segments, tags, towns, summit, set(confirmed))
    for row in rows + lowers:
        row["nearest_any"] = nearest_barangay(row["line"], all_places)
    for row in lowers:
        row["confirmed_overlap"] = [name for name, points in confirmed.items()
                                    if row["line"].intersection(LineString(points).buffer(5)).length > SHARED_M]
    return rows + lowers


def grade(rows, places, confirmed):
    """Apply the fixed rules, then the two that keep a name to its own evidence."""
    for row in rows:
        others = [o for o in rows if o is not row]
        row["shared_with"] = [o["channel"] for o in others if row["line"].intersection(o["line"].buffer(5)).length > SHARED_M]
        row["shared_with"] += [name for name, points in confirmed.items()
                               if row["line"].intersection(LineString(points).buffer(5)).length > SHARED_M]
        row["closer_place"] = None
        if row["place"]:
            closer = [(round(row["line"].distance(p["point"])), p["name"]) for key, p in places.items()
                      if key != row["place"]["osm_id"] and row["line"].distance(p["point"]) < row["place_m"]]
            row["closer_place"] = min(closer) if closer else None
        row["tied_branch"] = next((b for b in row["branches"] if abs(b["distance_m"] - (row["place_m"] or 0)) <= TIE_M
                                   or b["distance_m"] < (row["place_m"] or 0)), None)
        level = confidence(row["tag_matches"], row["place_m"], row["start_km"], row["reaches_town"], row["shared_with"])
        if level == "medium" and (row["closer_place"] or row["tied_branch"]):
            level = "low"
        row["confidence"] = level


def lower_rivers(rows, paths, segments, tags, towns, summit, confirmed_names):
    """Write the part below a join between two candidate names as the river it becomes, for neither name.

    Rivers keep joining further down, so each is written only as far as the next one already written.
    """
    lowers = {}
    for row in rows:
        partners = [name for name in row["joins"] if name not in confirmed_names]
        points = paths[row["channel"]]
        end = tuple(round(v) for v in row["line"].coords[-1])
        if partners and end in points:
            lowers.setdefault(end, {"names": set(), "points": points[points.index(end):], "town": row["town"]})["names"] |= {row["channel"], *partners}
    results, written = [], set()
    for lower in sorted(lowers.values(), key=lambda item: -len(item["points"])):
        kept_points = []
        for point in lower["points"]:
            kept_points.append(point)
            if point in written:
                break
        if len(kept_points) < 2:
            continue
        line, _ = cut_at_town(LineString(kept_points), towns[lower["town"]])
        if line.length < 1:
            continue
        written |= {point for point in kept_points if line.distance(Point(point)) < 1}
        kept = ways_on(line, segments)
        names = sorted({tags[i] for i in kept if tags[i]})
        joined = sorted(lower["names"])
        title = " / ".join(names) if names else "Unnamed river"
        results.append({"channel": f"{title} (below {', '.join(joined)})", "role": "shared lower river", "name_from": "OSM", "osm_ids": kept, "line": line, "joins": joined,
                        "reaches_town": True, "town": lower["town"], "other_tags": names, "place": None, "place_m": None, "tag": None,
                        "check": "This isn't a channel candidate. It's the river the named branches become, shown so that neither name has to claim it.",
                        "length_km": round(line.length / 1000, 1), "start_km": round(Point(line.coords[0]).distance(Point(summit)) / 1000, 1),
                        "end_km": round(Point(line.coords[-1]).distance(Point(summit)) / 1000, 1), "bearing": None, "tag_matches": False,
                        "branches": [], "shared_with": joined, "closer_place": None, "tied_branch": None, "confidence": "not a candidate"})
    return results


def evidence_lines(row):
    """Say the evidence for one line, the same words in the popup and the report."""
    lines = [f"Name comes from: {row['name_from']}"]
    if row["role"] != "name":
        lines.append("Role: the river below the join, not a channel candidate")
    if row["tag_matches"]:
        lines.append(f"OSM name tag: '{row['tag']}' on every part")
    elif row["other_tags"]:
        lines.append(f"OSM name tag: none for this name; parts are tagged {', '.join(row['other_tags'])}")
    else:
        lines.append("OSM name tag: none")
    if row["place"]:
        alt = f", also {row['place']['alt_name']}" if row["place"]["alt_name"] else ""
        lines.append(f"Nearest own barangay: {row['place']['name']}{alt}, {row['place_m']} m from the line")
    elif row["role"] == "name":
        lines.append("Nearest own barangay: none used, the name tag is the evidence")
    lines.append(f"Nearest barangay of any name: {row['nearest_any'][0]}, {row['nearest_any'][1]} m")
    if row.get("confirmed_overlap"):
        lines.append(f"Runs along the confirmed line of: {', '.join(row['confirmed_overlap'])}")
    if row["bearing"] is not None:
        lines.append(f"Flank: {row['bearing']}° from the summit; the line runs from {row['start_km']} to {row['end_km']} km out")
    lines.append(f"Town reached: {row['town']}" if row["reaches_town"] else f"Town reached: does not reach {row['town']}")
    if row["role"] == "name":
        joined = ", ".join(row["joins"])
        if row["stops_at_join"]:
            lines.append(f"Shared segment: none kept; the line stops where it joins {joined}")
        elif row["joins"]:
            lines.append(f"Shared segment: none; the line stops at the edge of {row['town']}, and further down it joins {joined}")
        else:
            lines.append("Shared segment: none")
        if row["shared_with"]:
            lines.append(f"Still overlaps: {', '.join(row['shared_with'])}")
    if row["closer_place"]:
        lines.append(f"Doubt: {row['closer_place'][1]} is closer to this line ({row['closer_place'][0]} m) than its own barangay")
    if row["tied_branch"]:
        branch = row["tied_branch"]
        lines.append(f"Doubt: way {branch['way']} is {branch['distance_m']} m from the barangay and starts {branch['top_km']} km out, so distance doesn't settle it")
    lines.append(f"OSM ways: {', '.join(map(str, row['osm_ids']))}")
    lines.append(f"Check by eye: {row['check']}")
    return lines


def save_geojson(rows):
    features = [{"type": "Feature",
                 "properties": {"channel": row["channel"], "role": row["role"], "confidence": row["confidence"], "evidence": evidence_lines(row),
                                "osm_ids": row["osm_ids"], "own_place": row["place"]["name"] if row["place"] else None, "place_m": row["place_m"],
                                "length_km": row["length_km"], "start_km": row["start_km"], "town": row["town"], "joins": row["joins"]},
                 "geometry": {"type": "LineString", "coordinates": to_lonlat(row["line"])}} for row in rows]
    collection = {"type": "FeatureCollection",
                  "note": "CANDIDATES only, not confirmed and not published. Confidence is how sure the match is, NOT hazard level. Data (c) OpenStreetMap contributors, ODbL.",
                  "features": features}
    OUT_FILE.with_suffix(".geojson").write_text(json.dumps(collection, ensure_ascii=False) + "\n", encoding="utf-8")


# KML colours are aabbggrr. These avoid green, yellow and red, which read as safe and dangerous.
KML_STYLES = {"high": ("ffffff00", "cyan"), "medium": ("ffff00ff", "magenta"), "low": ("ff00a5ff", "orange"), "not a candidate": ("ffc8c8c8", "grey")}
LEGEND = "The colours are match confidence, NOT hazard level. They say how sure this name-to-line match is, and nothing about danger."


def save_kml(rows):
    """Write the KML by hand. The folders are the legend, because Google Earth always shows their names."""
    styles = "".join(f'<Style id="{key.replace(" ", "-")}"><LineStyle><color>{code}</color><width>4</width></LineStyle></Style>' for key, (code, _) in KML_STYLES.items())
    folders = []
    for level, (_, colour) in KML_STYLES.items():
        marks = []
        for row in (r for r in rows if r["confidence"] == level):
            body = "".join(f"<li>{escape(line)}</li>" for line in evidence_lines(row))
            points = " ".join(f"{x},{y},0" for x, y in to_lonlat(row["line"]))
            marks.append(f"<Placemark><name>{escape(row['channel'])}</name><description><![CDATA[<b>Match confidence: {escape(level)}</b>, not hazard level<ul>{body}</ul>]]></description>"
                         f'<styleUrl>#{level.replace(" ", "-")}</styleUrl><LineString><tessellate>1</tessellate><coordinates>{points}</coordinates></LineString></Placemark>')
        title = f"{colour.capitalize()}: {level} match confidence" if level != "not a candidate" else "Grey: shared lower river, not a candidate"
        folders.append(f"<Folder><name>{escape(title)} ({len(marks)})</name><open>1</open>{''.join(marks)}</Folder>")
    OUT_FILE.with_suffix(".kml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Mayon channel name candidates v2</name><open>1</open>'
        f"<description>{escape(LEGEND)} Candidates only, not published. Data (c) OpenStreetMap contributors, ODbL.</description>{styles}"
        f"<Folder><name>LEGEND: colours are match confidence, NOT hazard level</name><description>{escape(LEGEND)}</description></Folder>"
        f"{''.join(folders)}</Document></kml>\n", encoding="utf-8")


def save_report(rows):
    names = [row for row in rows if row["role"] == "name"]
    counts = {level: sum(1 for row in names if row["confidence"] == level) for level in ("high", "medium", "low")}
    names.sort(key=lambda row: ("high", "medium", "low").index(row["confidence"]))
    table = ["| Name | Confidence | Own barangay, distance | Flank | Start, length (km) | Town | Stops at | Doubts |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in names:
        place = f"{row['place']['name']}, {row['place_m']} m" if row["place"] else "None: name tag"
        doubts = [line.replace("Doubt: ", "") for line in evidence_lines(row) if line.startswith("Doubt")]
        table.append(f"| {row['channel']} | {row['confidence']} | {place} | {row['bearing']}° | {row['start_km']}, {row['length_km']} | "
                     f"{row['town'] if row['reaches_town'] else 'Not ' + row['town']} | {'join with ' + ', '.join(row['joins']) if row['stops_at_join'] else 'edge of its town'} | {'; '.join(doubts) or '—'} |")
    lowers = "\n".join(f"- {row['channel']}: {row['length_km']} km." for row in rows if row["role"] != "name")
    REPORT_FILE.write_text(f"""# Channel names, second try: one line per name

**Nothing here is confirmed or published: {counts['high']} high, {counts['medium']} medium and {counts['low']} low match confidence.** Open `pipeline/context/channel_name_candidates_v2.kml` in Google Earth. The colours are match confidence, NOT hazard level.

{chr(10).join(table)}

## Shared lower rivers

These are written as their own grey lines, and given to neither name.

{lowers or 'None.'}

## The hints, checked against OSM place names

| Hint | What OSM says |
| --- | --- |
| Matanag, Legazpi Bgy 52? | Yes: Matanag has the alternate name Barangay 52 |
| Buyuan, Bgy 49 or 51? | Bgy 51: OSM's Buyoan has the alternate names Barangay 51 and Buyuan. The first try missed it because of the spelling |
| Padang, Bgy 50 or 60? | Bgy 50: Padang has the alternate name Barangay 50 |
| Anoling and Salugan, Camalig | Both are villages in Camalig. OSM's Anoling Elementary School is about 12 km out, far from the Anoling point |
| Busay near Cagsawa, Daraga | Yes: a Busay village is in Daraga, close to the Cagsawa Ruins. OSM has other places called Busay |
| Tumpa and Quirangay, Camalig | Both are villages in Camalig |

Bonga has no Legazpi place under that spelling. OSM's Bogña has the alternate name Barangay 53, and treating it as Bonga is my reading. OSM's places spelled Bonga are in Bacacay and out to the west, which don't fit Legazpi. Mabinit has the alternate name Barangay 54.

**Not resolved:** Binaan, which reports of the 2026 advisory name in Daraga, has no place or waterway in OSM, so it has no line. It isn't in docs/05 section 8.

## How confidence is set

The rules from `channel_names.py` stay: high needs an OSM name tag on every part and the right town. Medium needs the name's own barangay within 400 m, a start within 5 km of the summit, the right town, and no shared line. Two rules are new, and either makes a match low:

- Another listed barangay is closer to the line than the name's own.
- Another branch starting within {OTHER_BRANCH_HEAD_KM} km of the summit is closer to the barangay, or within {TIE_M} m of the same distance.

## Limits

- I chose each top segment and fork by hand; the rules grade those choices but don't make them. The choices are in `CHANNELS` in `channel_names_v2.py`.
- A village's name doesn't prove a channel runs through it, and OSM place points are approximate.
- Flow direction is as OSM drew it. I didn't bridge gaps in OSM's lines, so a line can start lower than the real gully.
- The waterway extract is the one saved in `pipeline/context`. The barangay points were read from OSM on 2026-11-01.

To repeat: `python pipeline/reports/channel_names_v2.py`
""", encoding="utf-8")


def main():
    rows = build_rows()
    for row in rows:
        print(row["channel"], "|", row["confidence"], "|", row["place_m"], "| start", row["start_km"], "end", row["end_km"], "len", row["length_km"], "| reach", row["reaches_town"], "| joins", row["joins"],
              "| closer", row["closer_place"], "| tied", row["tied_branch"], "| shared", row["shared_with"], "| tags", row["other_tags"], "|", row["osm_ids"])
    save_geojson(rows)
    save_kml(rows)
    save_report(rows)


if __name__ == "__main__":
    main()

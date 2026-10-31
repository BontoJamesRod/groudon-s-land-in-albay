"""Decision prep for T-010: which PHIVOLCS channels can OpenStreetMap supply lines for?

Run from the project folder:
    python pipeline/reports/channel_candidates.py

Saves OSM waterways inside the Mayon bounds to pipeline/context/, and compares them
with the channel names in docs/05 section 8. It doesn't build channels.geojson:
choosing the channel source is the owner's decision.
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

from pyproj import Geod
from shapely.geometry import LineString, Point, mapping, shape
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "pipeline"))

from mrw.config import load_site

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CANDIDATE_FILE = REPO_ROOT / "pipeline" / "context" / "mayon_waterways_osm_candidate.geojson"
RESULT_FILE = REPO_ROOT / "pipeline" / "reports" / "channel-candidates.json"
# Names and towns from docs/05 section 8. Town is None where 05 gives none.
PHIVOLCS_CHANNELS = [
    ("Mabinit", "Legazpi City"), ("Buyuan-Padang", "Legazpi City"), ("Miisi", "Daraga"),
    ("Tumpa", "Camalig"), ("Anoling", "Camalig"), ("Quirangay", "Camalig"), ("Maninila", "Guinobatan"),
    ("Basud-Lidong", "Santo Domingo"), ("Bulawan", "Malilipot"), ("San Vicente", "Tabaco City"),
    ("Buang", "Tabaco City"), ("Upper Nasisi", "Ligao City"), ("Upper Nabonton", "Ligao City"),
    ("Mi-isi", None), ("Bonga", None), ("Basud", None),
]
GENERIC_WORDS = re.compile(r"\b(river|creek|gully|channel|ilog|sapa|upper|lower)\b")
FUZZY_MATCH = 0.8


def fetch_waterways(config):
    """Ask OSM's Overpass service for every waterway line inside the site bounds."""
    box = f"{config['bounds_south']},{config['bounds_west']},{config['bounds_north']},{config['bounds_east']}"
    query = f'[out:json][timeout:120];way["waterway"]({box});out geom tags;'
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(OVERPASS_URL, data=data, headers={"User-Agent": "mayon-radar-watch/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)["elements"]


def to_feature(way):
    """Turn one OSM way into a GeoJSON Feature, keeping the tags that identify it."""
    coordinates = [[point["lon"], point["lat"]] for point in way["geometry"]]
    tags = way.get("tags", {})
    return {"type": "Feature", "id": f"way/{way['id']}",
            "properties": {"osm_id": way["id"], "waterway": tags.get("waterway"), "name": tags.get("name"),
                           "alt_name": tags.get("alt_name")},
            "geometry": {"type": "LineString", "coordinates": coordinates}}


def normalize(name):
    """Compare names without case, punctuation, or words like 'River'."""
    text = re.sub(r"[^a-z ]", "", (name or "").lower().replace("-", ""))
    return " ".join(GENERIC_WORDS.sub(" ", text).split())


def length_km(line):
    geod = Geod(ellps="WGS84")
    return geod.geometry_length(line) / 1000


def distance_to_summit_km(line, summit):
    """How close the line comes to the summit, along the ground."""
    geod = Geod(ellps="WGS84")
    return min(geod.inv(summit[0], summit[1], x, y)[2] for x, y in line.coords) / 1000


def towns_crossed(line, towns):
    return sorted(t["properties"]["name"] for t in towns if shape(t["geometry"]).intersects(line))


def match_channel(name, town, features, towns, summit):
    """Find named waterways that match one channel, and describe how good the match is."""
    wanted = normalize(name)
    matches = {}
    for feature in features:
        for candidate in (feature["properties"]["name"], feature["properties"]["alt_name"]):
            found = normalize(candidate)
            if not found:
                continue
            score = SequenceMatcher(None, wanted, found).ratio()
            if score >= FUZZY_MATCH or wanted in found.split():
                matches.setdefault(candidate, {"score": score, "features": []})["features"].append(feature)
    results = []
    for candidate, match in matches.items():
        line = unary_union([LineString(f["geometry"]["coordinates"]) for f in match["features"]])
        parts = list(getattr(line, "geoms", [line]))
        crossed = sorted({t for part in parts for t in towns_crossed(part, towns)})
        results.append({
            "osm_name": candidate, "name_score": round(match["score"], 2),
            "segments": len(match["features"]), "osm_ids": [f["properties"]["osm_id"] for f in match["features"]],
            "length_km": round(sum(length_km(part) for part in parts), 1),
            "closest_to_summit_km": round(min(distance_to_summit_km(part, summit) for part in parts), 1),
            "towns_crossed": crossed, "expected_town_crossed": town in crossed if town else None,
        })
    return {"channel": name, "expected_town": town, "matches": results}


def main():
    config = load_site("mayon")
    summit = (config["summit_lon"], config["summit_lat"])
    if CANDIDATE_FILE.is_file():
        features = json.loads(CANDIDATE_FILE.read_text(encoding="utf-8"))["features"]
    else:
        features = [to_feature(way) for way in fetch_waterways(config)]
        CANDIDATE_FILE.write_text(json.dumps({
            "type": "FeatureCollection",
            "note": "CANDIDATE only, not checked by hand. Data (c) OpenStreetMap contributors, ODbL.",
            "features": features}, ensure_ascii=False) + "\n", encoding="utf-8")
    towns = json.loads((REPO_ROOT / "site/data/sites/mayon/towns.geojson").read_text(encoding="utf-8"))["features"]
    channels = [match_channel(name, town, features, towns, summit) for name, town in PHIVOLCS_CHANNELS]
    named = [f for f in features if f["properties"]["name"]]
    lines = [LineString(f["geometry"]["coordinates"]) for f in features]
    near = sum(1 for line in lines if distance_to_summit_km(line, summit) <= 8)
    summary = {"waterway_segments": len(features), "named_segments": len(named),
               "distinct_names": sorted({f["properties"]["name"] for f in named}),
               "segments_within_8_km_of_summit": near, "channels": channels}
    RESULT_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

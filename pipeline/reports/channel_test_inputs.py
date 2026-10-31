"""Night 4 inputs: OpenStreetMap quarries and places, and IMERG rain. No NISAR product is touched.

Run from the project folder:
    python pipeline/reports/channel_test_inputs.py osm
    python pipeline/reports/channel_test_inputs.py rain

`osm` saves quarries to pipeline/context/osm_quarries_candidate.geojson. Data (c) OpenStreetMap
contributors, ODbL. Place names are saved beside them, because the table in the report needs them.

`rain` reads only the Mayon part of each daily IMERG file, by asking the server for pieces of
the file (ranged reads), and keeps the small result in raw/. Every byte is counted, and it stops
before going over the plan's 1.5 GB limit.
"""
import json
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import h5py
import numpy as np
from shapely.geometry import LineString, Polygon, mapping
from shapely.ops import polygonize, unary_union

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "pipeline"))

from mrw.config import load_site
from mrw.download import RangedFile

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CONTEXT = REPO / "pipeline" / "context"
QUARRY_FILE = CONTEXT / "osm_quarries_candidate.geojson"
PLACE_FILE = CONTEXT / "osm_places_candidate.geojson"
RAIN_FOLDER = REPO / "raw" / "imerg"
RAIN_FILE = RAIN_FOLDER / "mayon_daily.json"
RAIN_SHORT_NAME = "GPM_3IMERGDL"
# Rain between the first pass (06-21, about 21:13 UTC) and the last (10-19). IMERG days run
# midnight to midnight UTC, so the day of a first pass is left out: it was nearly over.
FIRST_RAIN_DAY = date(2026, 6, 22)
LAST_RAIN_DAY = date(2026, 10, 19)
RAIN_BYTE_LIMIT = 1_500_000_000
OSM_NOTE = "CANDIDATE only, not checked by hand. Data (c) OpenStreetMap contributors, ODbL."


def overpass(query):
    """Ask OSM's Overpass service a question and return the elements."""
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(OVERPASS_URL, data=data, headers={"User-Agent": "mayon-radar-watch/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)["elements"]


def quarry_shape(element):
    """Build an OSM way's or relation's polygon. A relation's holes are cut out of its outer rings."""
    if element["type"] == "way":
        return Polygon([(p["lon"], p["lat"]) for p in element["geometry"]])
    rings = {"outer": [], "inner": []}
    for member in element.get("members", []):
        if member.get("type") == "way" and member.get("geometry"):
            line = LineString([(p["lon"], p["lat"]) for p in member["geometry"]])
            rings["inner" if member.get("role") == "inner" else "outer"].append(line)
    outer = unary_union(list(polygonize(rings["outer"])))
    return outer.difference(unary_union(list(polygonize(rings["inner"]))))


def quarry_feature(element):
    """Turn one OSM quarry into a GeoJSON feature, keeping the tags that identify it."""
    tags = element.get("tags", {})
    return {"type": "Feature", "id": f"{element['type']}/{element['id']}",
            "properties": {"osm_id": f"{element['type']}/{element['id']}", "name": tags.get("name"),
                           "resource": tags.get("resource"), "operator": tags.get("operator")},
            "geometry": mapping(quarry_shape(element))}


def fetch_osm():
    """Save every landuse=quarry way and relation, and every named place, in the radar extent."""
    config = load_site("mayon")
    box = f"{config['bounds_south']},{config['bounds_west']},{config['bounds_north']},{config['bounds_east']}"
    quarries = overpass(f'[out:json][timeout:120];(way["landuse"="quarry"]({box});relation["landuse"="quarry"]({box}););out geom tags;')
    places = overpass(f'[out:json][timeout:120];node["place"~"city|town|village|hamlet|suburb|neighbourhood|quarter|locality"]["name"]({box});out body;')
    CONTEXT.mkdir(exist_ok=True)
    QUARRY_FILE.write_text(json.dumps({"type": "FeatureCollection", "note": OSM_NOTE,
                                       "features": [quarry_feature(e) for e in quarries]}, ensure_ascii=False) + "\n", encoding="utf-8")
    PLACE_FILE.write_text(json.dumps({"type": "FeatureCollection", "note": OSM_NOTE, "features": [
        {"type": "Feature", "properties": {"osm_id": e["id"], "name": e["tags"]["name"], "place": e["tags"]["place"]},
         "geometry": {"type": "Point", "coordinates": [e["lon"], e["lat"]]}} for e in places]}, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Quarries: {len(quarries)}. Places: {len(places)}.")


def spent_bytes():
    """Add up what earlier runs fetched."""
    if not RAIN_FILE.is_file():
        return 0
    return json.loads(RAIN_FILE.read_text(encoding="utf-8"))["bytes_fetched"]


def save_rain(record):
    RAIN_FOLDER.mkdir(parents=True, exist_ok=True)
    RAIN_FILE.write_text(json.dumps(record, indent=0) + "\n", encoding="utf-8")


def read_mayon_rain(fileobj, bounds):
    """Read one day's rain (mm) for the grid cells around Mayon. IMERG cells are 0.1 degrees."""
    with h5py.File(fileobj, "r") as product:
        lons, lats = product["lon"][()], product["lat"][()]
        columns = np.flatnonzero((lons >= bounds[0] - 0.05) & (lons <= bounds[2] + 0.05))
        rows = np.flatnonzero((lats >= bounds[1] - 0.05) & (lats <= bounds[3] + 0.05))
        # The file's order is (time, lon, lat).
        data = product["precipitation"]
        values = data[0, columns[0]:columns[-1] + 1, rows[0]:rows[-1] + 1]
        fill = data.attrs.get("_FillValue")
        units = data.attrs.get("units")
    units = units.decode() if isinstance(units, bytes) else str(units)
    values = values.astype("float64")
    if fill is not None:
        values[values == np.ravel(fill)[0]] = np.nan
    return lons[columns], lats[rows], values, units


def fetch_rain():
    """Read every day in the pair windows, keeping what earlier runs already fetched."""
    import earthaccess
    config = load_site("mayon")
    bounds = [config["bounds_west"], config["bounds_south"], config["bounds_east"], config["bounds_north"]]
    if not earthaccess.login(strategy="netrc").authenticated:
        raise RuntimeError("Earthdata login failed")
    results = earthaccess.search_data(short_name=RAIN_SHORT_NAME, temporal=(str(FIRST_RAIN_DAY), str(LAST_RAIN_DAY)),
                                      bounding_box=tuple(bounds))
    by_day = {}
    for granule in results:
        day = granule["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"][:10]
        by_day[day] = granule
    version = results[0]["umm"]["CollectionReference"].get("Version") if results else None
    print(f"Search: {RAIN_SHORT_NAME} version {version}, {len(results)} files.")
    record = json.loads(RAIN_FILE.read_text(encoding="utf-8")) if RAIN_FILE.is_file() else {
        "short_name": RAIN_SHORT_NAME, "version": version, "bytes_fetched": 0, "days": {}}
    system = earthaccess.get_fsspec_https_session()
    day = FIRST_RAIN_DAY
    while day <= LAST_RAIN_DAY:
        key = str(day)
        day += timedelta(days=1)
        if key in record["days"]:
            continue
        if key not in by_day:
            print("Not listed:", key)
            continue
        url = next(link for link in by_day[key].data_links() if link.endswith((".nc4", ".HDF5", ".h5")))
        size = system.info(url)["size"]
        ranged = RangedFile(lambda start, end, u=url: system.cat_file(u, start=start, end=end), size,
                            spent_before=record["bytes_fetched"], budget=RAIN_BYTE_LIMIT)
        try:
            lons, lats, values, units = read_mayon_rain(ranged, bounds)
        finally:
            record["bytes_fetched"] += ranged.bytes_fetched
            save_rain(record)
        record["lons"], record["lats"], record["units"] = lons.tolist(), lats.tolist(), units
        record["days"][key] = {"file": url.rsplit("/", 1)[-1], "rain_mm": values.tolist()}
        save_rain(record)
        print(key, f"{record['bytes_fetched'] / 1e6:.0f} MB so far", flush=True)
    print(f"Days: {len(record['days'])}. Fetched: {record['bytes_fetched'] / 1e9:.3f} GB.")


if __name__ == "__main__":
    {"osm": fetch_osm, "rain": fetch_rain}[sys.argv[1]]()

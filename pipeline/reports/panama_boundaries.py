"""Make pipeline/context/panama_boundaries.json from the geoBoundaries file (T-036).

Run from the project folder, after the Panama trial has downloaded its source file:
    python pipeline/reports/panama_boundaries.py

Keeps the districts that touch the site and gives them the field names context.py reads.
The owner accepted CC BY-SA 4.0 as the real terms: the upstream record states it, while
geoBoundaries' own record says CC BY 4.0 with the note "need to update".
"""
import json
from pathlib import Path

from shapely import make_valid
from shapely.geometry import box, shape

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "raw" / "context_download" / "panama" / "geoBoundaries-PAN-ADM2.geojson"
TARGET = ROOT / "pipeline" / "context" / "panama_boundaries.json"
CONFIG = ROOT / "pipeline" / "sites" / "panama.json"


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    site = box(config["bounds_west"], config["bounds_south"], config["bounds_east"], config["bounds_north"])
    features = []
    for feature in json.loads(SOURCE.read_text(encoding="utf-8"))["features"]:
        if make_valid(shape(feature["geometry"])).intersects(site):
            props = feature["properties"]
            features.append({"type": "Feature", "geometry": feature["geometry"], "properties": {
                "adm3_en": props["shapeName"], "adm3_psgc": props["shapeID"], "geo_level": "District"}})
    TARGET.write_text(json.dumps({"source_id": "pa_admin_boundaries", "license": "CC BY-SA 4.0", "features": features}) + "\n", encoding="utf-8")
    print("Districts:", [f["properties"]["adm3_en"] for f in features])


if __name__ == "__main__":
    main()

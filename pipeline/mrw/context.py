"""Tasks T-009 and T-011: prepare the context files for a site.

Run from the project folder:
    python pipeline/mrw/context.py mayon

Makes these files under site/data/ from the source files in pipeline/context/:
- sources.json: where the context data comes from, and its license
- sites/<id>/towns.geojson: town borders, clipped to the site bounds
- sites/<id>/land.geojson: land, the union of the towns; everything else is "sea"
- sites/<id>/events.json: recorded events for the timeline
"""
import json
import sys
from pathlib import Path

from shapely import make_valid, set_precision
from shapely.geometry import Point, box, mapping, shape
from shapely.ops import unary_union

# Lets this file run as a script from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mrw.config import load_site, utc_now_text

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_FOLDER = REPO_ROOT / "pipeline" / "context"
DATA_FOLDER = REPO_ROOT / "site" / "data"
SCHEMA_VERSION = "1.0"
BOUNDARY_SOURCE_ID = "ph_admin_boundaries"
# 0.00001 degree is about 1 m: finer than the 20 m map grid, and it keeps files small.
COORDINATE_GRID_DEG = 0.00001
# Pieces under about 0.01 km2 are slivers left by clipping, not useful map shapes.
MIN_TOWN_AREA_DEG2 = 1e-6


def write_json(path, data, now):
    """Save data inside the standard file envelope from docs/05."""
    save_text(path, {"data": data, "meta": {"generated_at": now, "schema_version": SCHEMA_VERSION}})


def write_geojson(path, features, now, license_name=None):
    """Save Features as a FeatureCollection with the docs/05 members, and its license if it must carry one."""
    content = {"type": "FeatureCollection", "generated_at": now, "schema_version": SCHEMA_VERSION}
    if license_name:
        content["license"] = license_name
    save_text(path, {**content, "features": features})


def save_text(path, content):
    """Write JSON as UTF-8, creating the folder if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def town_display_name(source_name):
    """Turn the source's 'City of Tabaco' into the 'Tabaco City' people use."""
    if source_name.startswith("City of "):
        return source_name.removeprefix("City of ") + " City"
    return source_name


def town_id(site_id, name):
    """Make an id such as mayon_tabaco_city from a site and town name."""
    slug = "".join(c if c.isalnum() else "_" for c in name.lower())
    return f"{site_id}_{slug}"


def town_kind(geo_level):
    """Translate the source's level into the town_kind enum."""
    return {"City": "city", "Mun": "municipality"}.get(geo_level, "other")


def clean_polygons(geom):
    """Fix a shape, round its corners, and keep only its polygon parts."""
    geom = set_precision(make_valid(geom), COORDINATE_GRID_DEG)
    parts = getattr(geom, "geoms", [geom])
    polygons = [p for p in parts if p.geom_type in ("Polygon", "MultiPolygon") and not p.is_empty]
    return unary_union(polygons) if polygons else None


def label_point(geom):
    """Pick a point for the town's name that is always inside its polygon.

    A centroid can fall outside a curved town or in the sea, so we use it only
    when it is inside the town's largest piece.
    """
    largest = max(getattr(geom, "geoms", [geom]), key=lambda part: part.area)
    centre = largest.centroid
    point = centre if largest.contains(centre) else largest.representative_point()
    rounded = Point(round(point.x, 5), round(point.y, 5))
    return rounded if geom.covers(rounded) else Point(point.x, point.y)


def build_towns(source_features, config, source_id=BOUNDARY_SOURCE_ID):
    """Clip each town to the site bounds and return its GeoJSON Features."""
    site_box = box(config["bounds_west"], config["bounds_south"],
                   config["bounds_east"], config["bounds_north"])
    towns = []
    for feature in source_features:
        props = feature["properties"]
        clipped = clean_polygons(make_valid(shape(feature["geometry"])).intersection(site_box))
        if clipped is None or clipped.area < MIN_TOWN_AREA_DEG2:
            continue  # this town is outside the site
        name = town_display_name(props["adm3_en"])
        identifier = town_id(config["id"], name)
        label = label_point(clipped)
        towns.append({
            "type": "Feature",
            "id": identifier,
            "properties": {
                "id": identifier,
                "site_id": config["id"],
                "name": name,
                "kind": town_kind(props.get("geo_level")),
                "label_lat": label.y,
                "label_lon": label.x,
                "source_code": str(props["adm3_psgc"]),
                "source_id": source_id,
            },
            "geometry": mapping(clipped),
        })
    return sorted(towns, key=lambda town: town["properties"]["name"])


def build_land(towns, config, source_id=BOUNDARY_SOURCE_ID):
    """Make one land shape from the union of the towns (docs/05, land_areas seed)."""
    land = clean_polygons(unary_union([shape(town["geometry"]) for town in towns]))
    identifier = f"{config['id']}_land"
    return [{
        "type": "Feature",
        "id": identifier,
        "properties": {"id": identifier, "site_id": config["id"], "source_id": source_id},
        "geometry": mapping(land),
    }]


def _stamped(rows, now):
    """Add the created_at and updated_at columns to hand-written rows."""
    return [{**row, "created_at": now, "updated_at": now} for row in rows]


def write_sources(data_folder, context_folder, now):
    """Write sources.json, which all sites share."""
    sources = json.loads((Path(context_folder) / "sources.json").read_text(encoding="utf-8"))
    write_json(Path(data_folder) / "sources.json", _stamped(sources, now), now)


def build_context(site_id, data_folder=DATA_FOLDER, context_folder=CONTEXT_FOLDER):
    """Write sources, towns, land and events for one site."""
    config = load_site(site_id)
    now = utc_now_text()
    site_folder = Path(data_folder) / "sites" / site_id
    write_sources(data_folder, context_folder, now)
    boundary_file = context_folder / f"{site_id}_boundaries.json"
    source = json.loads(boundary_file.read_text(encoding="utf-8"))
    # A boundary file can name its own source and license. Without them it's the Philippine source.
    source_id = source.get("source_id", BOUNDARY_SOURCE_ID)
    license_name = source.get("license")
    towns = build_towns(source["features"], config, source_id)
    write_geojson(site_folder / "towns.geojson", towns, now, license_name)
    write_geojson(site_folder / "land.geojson", build_land(towns, config, source_id), now, license_name)
    events_file = context_folder / f"{site_id}_events.json"
    if events_file.is_file():
        events = json.loads(events_file.read_text(encoding="utf-8"))
        write_json(site_folder / "events.json", _stamped(events, now), now)
    return [town["properties"]["name"] for town in towns]


if __name__ == "__main__":
    print("Towns:", build_context(sys.argv[1] if len(sys.argv) > 1 else "mayon"))

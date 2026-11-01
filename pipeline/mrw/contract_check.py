"""Task T-006: check every published data file against docs/05-database-design.md.

Run from the project folder:
    python pipeline/mrw/contract_check.py              (checks site/data)
    python pipeline/mrw/contract_check.py pipeline/out --unpublished

The check prints one line per problem and exits with code 1 if it finds any,
which is what makes CI stop the deploy. It never changes a file.
"""
import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image
from pyproj import Geod
from shapely import get_coordinates
from shapely.geometry import shape

SCHEMA_VERSION = "1.0"
REPO_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_FOLDER = REPO_ROOT / "pipeline" / "context"
# The pipeline measures the reach on the radar's map projection, and this check measures on the
# Earth's shape. They differ by a few metres at 10 km, and shapes are rounded to about 1 m.
REACH_TOLERANCE_KM = 0.05

# Enums from 05 section 5
SITE_STATUS = {"draft", "published"}
CHANGE_TYPE = {"new_material", "ground_movement", "flood"}
TOWN_KIND = {"city", "municipality", "other"}
ORBIT_DIRECTION = {"ascending", "descending"}
PRODUCT_TYPE = {"GCOV", "GUNW"}
MATURITY = {"BETA", "PROVISIONAL"}
PAIR_STATUS = {"processing", "ready", "published", "failed"}
LAYER_KIND = {"before_db", "after_db", "change_db", "coherence_loss", "new_material",
              "movement_cm", "flood_water"}
IMAGE_FORMAT = {"png", "webp"}
GRID_DTYPE_BYTES = {"uint8": 1, "int8": 1, "int16": 2}
NO_DATA_REASON = {"253": "masked_by_product", "254": "sea", "255": "outside_coverage"}
CONFIDENCE_LEVEL = {"none", "low", "high"}
DETECTION_RESULT = {"yes", "no", "not_visible"}
CONTEXT_USE = {"basemap", "boundaries", "coastline", "channels", "events", "validation", "analysis", "radar"}

# Every MVP pair has these layers. coherence_loss is added when coherence was used.
BASE_LAYER_KINDS = {"before_db", "after_db", "change_db", "new_material"}
NEW_MATERIAL_VALUES = {0, 1, 2, 253, 254, 255}

PASS_ID = re.compile(r"^[AD]\d{3}F\d{3}_\d{8}T\d{6}$")
PAIR_ID = re.compile(r"^[a-z0-9_]+_[AD]\d{3}F\d{3}_\d{8}_\d{8}$")
DATE_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_ZONE = re.compile(r"^(UTC|[A-Za-z_]+(/[A-Za-z0-9_+-]+)+)$")
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def field(kind, required=True, enum=None, pattern=None, low=None, high=None):
    """Describe one column: its type, whether it is required, and its limits."""
    return {"kind": kind, "required": required, "enum": enum, "pattern": pattern,
            "low": low, "high": high}


# One table per entry: the columns from 05 section 3, with the same names.
SITES = {
    "id": field("string", pattern=re.compile(r"^[a-z0-9_]+$")),
    "name": field("string"),
    "country": field("string"),
    "status": field("string", enum=SITE_STATUS),
    "time_zone": field("string", pattern=TIME_ZONE),
    "center_lat": field("number", low=-90, high=90),
    "center_lon": field("number", low=-180, high=180),
    "bounds_west": field("number", low=-180, high=180),
    "bounds_south": field("number", low=-90, high=90),
    "bounds_east": field("number", low=-180, high=180),
    "bounds_north": field("number", low=-90, high=90),
    "default_zoom": field("integer", low=0, high=22),
    "min_zoom": field("integer", low=0, high=22),
    "max_zoom": field("integer", low=0, high=22),
    "summit_lat": field("number", required=False, low=-90, high=90),
    "summit_lon": field("number", required=False, low=-180, high=180),
    "danger_zone_radius_km": field("number", required=False),
    "danger_zone_label": field("string", required=False),
    "detection_reach_km": field("number", required=False),
    "channel_strip_half_width_m": field("number", required=False),
    "wording_set": field("string", required=False, enum={"plain_change"}),
    "boundary_credit": field("string", required=False),
    "boundary_credit_url": field("url", required=False),
    "change_types": field("array"),
    "created_at": field("date-time"),
    "updated_at": field("date-time"),
}
TOWNS = {
    "id": field("string"),
    "site_id": field("string"),
    "name": field("string"),
    "kind": field("string", enum=TOWN_KIND),
    "label_lat": field("number", low=-90, high=90),
    "label_lon": field("number", low=-180, high=180),
    "source_code": field("string", required=False),
    "source_id": field("string"),
}
CHANNELS = {
    "id": field("string"),
    "site_id": field("string"),
    "name": field("string"),
    "alt_names": field("array", required=False),
    "town_ids": field("array"),
    "name_source": field("string"),
    "name_source_url": field("url", required=False),
    "also_name_source_url": field("url", required=False),
    "line_source_id": field("string"),
    "confirmed_by": field("string"),
    "confirmed_on": field("date"),
    "imagery_date": field("date"),
    "label_lat": field("number", low=-90, high=90),
    "label_lon": field("number", low=-180, high=180),
    "strip_geometry": field("object"),
    "checked_geometry": field("object"),
    "not_checked_geometry": field("object", required=False),
}
CHANNEL_AREAS = {
    "id": field("string"),
    "site_id": field("string"),
    "channel_id": field("string"),
    "pair_id": field("string", pattern=PAIR_ID),
    "flagged_area_km2": field("number", required=False, low=0),
    "checked_area_km2": field("number", low=0),
    "created_at": field("date-time"),
    "updated_at": field("date-time"),
}
LAND = {
    "id": field("string"),
    "site_id": field("string"),
    "source_id": field("string"),
}
PASSES = {
    "id": field("string", pattern=PASS_ID),
    "site_id": field("string"),
    "mission": field("string"),
    "product_type": field("string", enum=PRODUCT_TYPE),
    "granule_id": field("string"),
    "track": field("integer", low=1, high=173),
    "frame": field("integer", low=1, high=176),
    "orbit_direction": field("string", enum=ORBIT_DIRECTION),
    "cycle": field("integer", low=1),
    "acquired_start": field("date-time"),
    "acquired_end": field("date-time"),
    "polarizations": field("array"),
    "pixel_spacing_m": field("number", enum={10, 20, 80}),
    "maturity": field("string", enum=MATURITY),
    "vertex_url": field("url"),
    "created_at": field("date-time"),
    "updated_at": field("date-time"),
}
PAIRS = {
    "id": field("string", pattern=PAIR_ID),
    "site_id": field("string"),
    "status": field("string", enum=PAIR_STATUS),
    "track": field("integer", low=1, high=173),
    "frame": field("integer", low=1, high=176),
    "orbit_direction": field("string", enum=ORBIT_DIRECTION),
    "before_pass_id": field("string", pattern=PASS_ID),
    "after_pass_id": field("string", pattern=PASS_ID),
    "before_acquired_start": field("date-time"),
    "after_acquired_start": field("date-time"),
    "previous_pair_id": field("string", required=False, pattern=PAIR_ID),
    "gunw_granule_id": field("string", required=False),
    "gunw_vertex_url": field("url", required=False),
    "coherence_used": field("boolean"),
    "brightness_threshold_db": field("number"),
    "coherence_loss_threshold": field("number", required=False, low=0, high=1),
    "high_confidence_area_km2": field("number", low=0),
    "low_confidence_area_km2": field("number", low=0),
    "new_material_area_km2": field("number", low=0),
    "pipeline_version": field("string", pattern=re.compile(r"^\d+\.\d+\.\d+$")),
    "error_message": field("string", required=False),
    "check_note": field("string", required=False),
    "published_at": field("date-time", required=False),
    "created_at": field("date-time"),
    "updated_at": field("date-time"),
}
LAYERS = {
    "id": field("string"),
    "pair_id": field("string"),
    "kind": field("string", enum=LAYER_KIND),
    "title": field("string"),
    "units": field("string"),
    "image_path": field("string"),
    "image_format": field("string", enum=IMAGE_FORMAT),
    "bounds_west": field("number", low=-180, high=180),
    "bounds_south": field("number", low=-90, high=90),
    "bounds_east": field("number", low=-180, high=180),
    "bounds_north": field("number", low=-90, high=90),
    "image_width": field("integer", low=1),
    "image_height": field("integer", low=1),
    "grid_path": field("string", required=False),
    "grid_dtype": field("string", required=False, enum=set(GRID_DTYPE_BYTES)),
    "grid_scale": field("number", required=False),
    "grid_nodata": field("integer", required=False),
    "no_data_codes": field("object", required=False),
    "grid_width": field("integer", required=False, low=1),
    "grid_height": field("integer", required=False, low=1),
    "color_scale_min": field("number", required=False),
    "color_scale_max": field("number", required=False),
    "legend": field("array"),
    "source_granule_ids": field("array"),
    "created_at": field("date-time"),
    "updated_at": field("date-time"),
}
EVENTS = {
    "id": field("string"),
    "site_id": field("string"),
    "name": field("string"),
    "event_date": field("date"),
    "description": field("string", required=False),
    "source_name": field("string"),
    "source_url": field("url"),
    "created_at": field("date-time"),
    "updated_at": field("date-time"),
}
VALIDATIONS = {
    "id": field("string"),
    "pair_id": field("string"),
    "source_name": field("string"),
    "source_url": field("url"),
    "source_date": field("date"),
    "method": field("string"),
    "items": field("array"),
    "created_at": field("date-time"),
    "updated_at": field("date-time"),
}
VALIDATION_ITEMS = {
    "id": field("string"),
    "validation_id": field("string"),
    "place_name": field("string"),
    "channel_id": field("string", required=False),
    "reported_in_source": field("boolean"),
    "detected": field("string", enum=DETECTION_RESULT),
    "note": field("string", required=False),
    "created_at": field("date-time"),
    "updated_at": field("date-time"),
}
SOURCES = {
    "id": field("string"),
    "name": field("string"),
    "provider": field("string"),
    "used_for": field("string", enum=CONTEXT_USE),
    "url": field("url"),
    "license": field("string"),
    "retrieved_on": field("date"),
    "site_id": field("string", required=False),
    "created_at": field("date-time"),
    "updated_at": field("date-time"),
}


def _valid_date_text(text, kind):
    """Return True if the text is a real date or date-time in the 05 format."""
    pattern = DATE_TIME if kind == "date-time" else DATE_ONLY
    if not isinstance(text, str) or not pattern.match(text):
        return False
    try:
        if kind == "date-time":
            datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
        else:
            date.fromisoformat(text)
    except ValueError:
        return False
    return True


def _type_ok(value, kind):
    """Return True if a value has the JSON type a column asks for."""
    if kind in ("date", "date-time"):
        return _valid_date_text(value, kind)
    if kind == "url":
        return isinstance(value, str) and value.startswith(("http://", "https://"))
    if kind == "string":
        return isinstance(value, str)
    if kind == "boolean":
        return isinstance(value, bool)
    # In Python True counts as a number, so booleans are ruled out by hand.
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "array":
        return isinstance(value, list)
    if kind == "object":
        return isinstance(value, dict)
    return False


def check_row(row, table, where, errors):
    """Check one record against a table: missing, unknown, wrong type, out of range."""
    if not isinstance(row, dict):
        errors.append(f"{where}: expected an object")
        return
    for name in row:
        if name not in table:
            errors.append(f"{where}: unknown field '{name}'")
    for name, rule in table.items():
        if name not in row:
            if rule["required"]:
                errors.append(f"{where}: missing required field '{name}'")
            continue
        value = row[name]
        if value is None:
            if rule["required"]:
                errors.append(f"{where}: required field '{name}' is null")
            continue
        if not _type_ok(value, rule["kind"]):
            errors.append(f"{where}: field '{name}' should be {rule['kind']}, got {value!r}")
            continue
        if rule["enum"] is not None and value not in rule["enum"]:
            errors.append(f"{where}: field '{name}' has invalid value {value!r}")
        if rule["pattern"] is not None and not rule["pattern"].match(value):
            errors.append(f"{where}: field '{name}' has invalid format {value!r}")
        if rule["low"] is not None and value < rule["low"]:
            errors.append(f"{where}: field '{name}' is below {rule['low']}")
        if rule["high"] is not None and value > rule["high"]:
            errors.append(f"{where}: field '{name}' is above {rule['high']}")


def _refuse_constant(name):
    """Python accepts NaN and Infinity in JSON, but browsers don't, so they are errors."""
    raise ValueError(f"{name} is not valid JSON")


def _load_json(path, errors):
    """Read a JSON file. Return None and record an error if it can't be parsed."""
    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=_refuse_constant)
    except (ValueError, OSError) as problem:
        errors.append(f"{path}: can't be read as JSON ({problem})")
        return None


def _check_stamp(holder, where, errors):
    """Check generated_at and schema_version, which every file must carry."""
    if not _valid_date_text(holder.get("generated_at"), "date-time"):
        errors.append(f"{where}: generated_at is missing or not a UTC date-time")
    if holder.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{where}: schema_version should be {SCHEMA_VERSION!r}, "
                      f"got {holder.get('schema_version')!r}")


def load_json_file(path, errors):
    """Read a JSON file, check its envelope and return its 'data' member."""
    content = _load_json(path, errors)
    if content is None:
        return None
    if not isinstance(content, dict) or set(content) != {"data", "meta"}:
        errors.append(f"{path}: envelope must be exactly 'data' and 'meta'")
        return None
    if not isinstance(content["meta"], dict):
        errors.append(f"{path}: 'meta' must be an object")
        return None
    _check_stamp(content["meta"], path, errors)
    return content["data"]


def load_geojson_file(path, errors):
    """Read a GeoJSON file, check its envelope and return its Feature list."""
    content = _load_json(path, errors)
    if content is None:
        return None
    if not isinstance(content, dict) or content.get("type") != "FeatureCollection":
        errors.append(f"{path}: must be a FeatureCollection")
        return None
    _check_stamp(content, path, errors)
    if "license" in content and not (isinstance(content["license"], str) and content["license"]):
        errors.append(f"{path}: 'license' must be a non-empty string")
    features = content.get("features")
    if not isinstance(features, list):
        errors.append(f"{path}: 'features' must be an array")
        return None
    return features


def _check_data_array(data, path, errors):
    """Return data if it is the array the file should hold, otherwise record an error."""
    if not isinstance(data, list):
        errors.append(f"{path}: 'data' must be an array")
        return []
    return data


def _unique_ids(rows, where, errors):
    """Check that no two rows share an id, and return the set of ids."""
    ids = set()
    for row in rows:
        row_id = row.get("id") if isinstance(row, dict) else None
        if row_id in ids:
            errors.append(f"{where}: duplicate id {row_id!r}")
        if row_id is not None:
            ids.add(row_id)
    return ids


def _check_bounds(row, where, errors):
    """West must be less than east, and south less than north."""
    west, east = row.get("bounds_west"), row.get("bounds_east")
    south, north = row.get("bounds_south"), row.get("bounds_north")
    if all(isinstance(v, (int, float)) for v in (west, east, south, north)):
        if west >= east or south >= north:
            errors.append(f"{where}: bounds are reversed")


def _check_time_zone(name, where, errors):
    """The browser stops on an unknown time zone, so it must be a real IANA name."""
    if not isinstance(name, str):
        return
    try:
        ZoneInfo(name)
    except (KeyError, ValueError, OSError):
        errors.append(f"{where}: unknown time zone {name!r}")


def check_sites(path, errors):
    """Check sites.json and return its rows."""
    rows = _check_data_array(load_json_file(path, errors), path, errors)
    _unique_ids(rows, path, errors)
    for number, row in enumerate(rows):
        where = f"{path} row {number}"
        check_row(row, SITES, where, errors)
        if not isinstance(row, dict):
            continue
        _check_bounds(row, where, errors)
        _check_time_zone(row.get("time_zone"), where, errors)
        if row.get("status") != "published":
            errors.append(f"{where}: only published sites may appear in sites.json")
        zooms = [row.get(k) for k in ("min_zoom", "default_zoom", "max_zoom")]
        if all(isinstance(z, int) for z in zooms) and not zooms[0] <= zooms[1] <= zooms[2]:
            errors.append(f"{where}: zooms must be min_zoom <= default_zoom <= max_zoom")
        radius = row.get("danger_zone_radius_km")
        if radius is not None:
            if isinstance(radius, (int, float)) and radius <= 0:
                errors.append(f"{where}: danger_zone_radius_km must be above 0")
            if row.get("summit_lat") is None or row.get("summit_lon") is None:
                errors.append(f"{where}: danger zone needs summit_lat and summit_lon")
            if not row.get("danger_zone_label"):
                errors.append(f"{where}: danger zone needs danger_zone_label")
        changes = row.get("change_types")
        if isinstance(changes, list):
            if not changes or any(c not in CHANGE_TYPE for c in changes):
                errors.append(f"{where}: change_types must hold at least 1 valid value")
        if not 1 <= len(str(row.get("name", ""))) <= 80:
            errors.append(f"{where}: name must be 1-80 characters")
    return rows


def check_sources(path, errors):
    """Check sources.json and return its ids."""
    rows = _check_data_array(load_json_file(path, errors), path, errors)
    for number, row in enumerate(rows):
        check_row(row, SOURCES, f"{path} row {number}", errors)
        # A row with a site_id belongs to that site only. Without one it's shared by all sites.
        site_id = row.get("site_id") if isinstance(row, dict) else None
        if site_id and not (Path(path).parent / "sites" / str(site_id)).is_dir():
            errors.append(f"{path} row {number}: site_id {site_id!r} has no data folder")
    return _unique_ids(rows, path, errors)


def _check_geometry(feature, allowed, where, errors):
    """Return the shapely shape of a Feature, or None if its geometry is bad."""
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") not in allowed:
        errors.append(f"{where}: geometry must be one of {sorted(allowed)}")
        return None
    try:
        geom = shape(geometry)
    except (ValueError, TypeError, AttributeError, IndexError) as problem:
        errors.append(f"{where}: geometry can't be read ({problem})")
        return None
    if geom.is_empty or not geom.is_valid:
        errors.append(f"{where}: geometry is empty or invalid")
        return None
    return geom


def _feature_rows(features, table, allowed, path, site_id, errors):
    """Check each Feature's type, id, properties and geometry; yield the good ones."""
    for number, feature in enumerate(features):
        where = f"{path} feature {number}"
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            errors.append(f"{where}: must be a Feature")
            continue
        props = feature.get("properties")
        check_row(props, table, where, errors)
        if not isinstance(props, dict):
            continue
        if feature.get("id") != props.get("id"):
            errors.append(f"{where}: Feature id must equal properties.id")
        if props.get("site_id") != site_id:
            errors.append(f"{where}: site_id should be {site_id!r}")
        yield where, props, _check_geometry(feature, allowed, where, errors)


def check_towns(path, site_id, source_ids, errors):
    """Check towns.geojson and return its town ids."""
    features = load_geojson_file(path, errors) or []
    ids = set()
    allowed = {"Polygon", "MultiPolygon"}
    for where, props, geom in _feature_rows(features, TOWNS, allowed, path, site_id, errors):
        if props.get("id") in ids:
            errors.append(f"{where}: duplicate id {props.get('id')!r}")
        ids.add(props.get("id"))
        if props.get("source_id") not in source_ids:
            errors.append(f"{where}: source_id {props.get('source_id')!r} is not in sources.json")
        lat, lon = props.get("label_lat"), props.get("label_lon")
        if geom is not None and isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            if not geom.covers(shape({"type": "Point", "coordinates": [lon, lat]})):
                errors.append(f"{where}: label point is outside the town's polygon")
    return ids


def check_land(path, site_id, source_ids, errors):
    """Check land.geojson."""
    features = load_geojson_file(path, errors) or []
    if len(features) != 1:
        errors.append(f"{path}: must hold exactly 1 land feature")
    allowed = {"Polygon", "MultiPolygon"}
    for where, props, _geom in _feature_rows(features, LAND, allowed, path, site_id, errors):
        if props.get("source_id") not in source_ids:
            errors.append(f"{where}: source_id {props.get('source_id')!r} is not in sources.json")


def _owner_checks(site_id, context_folder):
    """Read the owner's verdicts on a site's channels. A site with no record has none."""
    path = Path(context_folder) / f"{site_id}_channels.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"checks": []}


def _km_from_summit(geom, site_row):
    """The distance over the Earth's surface from the summit to each point of a shape."""
    points = get_coordinates(geom)
    summit_lons = [site_row["summit_lon"]] * len(points)
    summit_lats = [site_row["summit_lat"]] * len(points)
    metres = Geod(ellps="WGS84").inv(summit_lons, summit_lats, points[:, 0].tolist(), points[:, 1].tolist())[2]
    return [value / 1000 for value in metres]


def _check_channel_reach(props, site_row, where, errors):
    """The strip stops at the reach, and what lies past it is drawn as not checked (FR-064, FR-071)."""
    strip = _check_geometry({"geometry": props.get("strip_geometry")}, {"Polygon", "MultiPolygon"}, f"{where} strip_geometry", errors)
    checked = _check_geometry({"geometry": props.get("checked_geometry")}, {"LineString", "MultiLineString"}, f"{where} checked_geometry", errors)
    beyond = None
    if props.get("not_checked_geometry") is not None:
        beyond = _check_geometry({"geometry": props["not_checked_geometry"]}, {"LineString", "MultiLineString"}, f"{where} not_checked_geometry", errors)
    reach = (site_row or {}).get("detection_reach_km")
    if not reach:
        return
    if strip is not None and max(_km_from_summit(strip, site_row)) > reach + REACH_TOLERANCE_KM:
        errors.append(f"{where}: strip_geometry goes past the reach distance")
    if checked is not None and max(_km_from_summit(checked, site_row)) > reach + REACH_TOLERANCE_KM:
        errors.append(f"{where}: checked_geometry goes past the reach distance")
    if beyond is not None and min(_km_from_summit(beyond, site_row)) < reach - REACH_TOLERANCE_KM:
        errors.append(f"{where}: not_checked_geometry starts inside the reach distance")


def check_channels(path, site_id, source_ids, town_ids, errors, site_row=None, context_folder=CONTEXT_FOLDER):
    """Check channels.geojson and return its channel ids. Only confirmed lines may be here (FR-065)."""
    features = load_geojson_file(path, errors) or []
    allowed = {"LineString", "MultiLineString"}
    confirmed = {check["channel"]: check for check in _owner_checks(site_id, context_folder)["checks"]
                 if check["verdict"] == "confirmed"}
    ids = set()
    for where, props, _geom in _feature_rows(features, CHANNELS, allowed, path, site_id, errors):
        if props.get("id") in ids:
            errors.append(f"{where}: duplicate id {props.get('id')!r}")
        ids.add(props.get("id"))
        if props.get("line_source_id") not in source_ids:
            errors.append(f"{where}: line_source_id is not in sources.json")
        towns = props.get("town_ids")
        if not towns:
            errors.append(f"{where}: a channel needs at least 1 town")
        for town_id in towns if isinstance(towns, list) else []:
            if town_id not in town_ids:
                errors.append(f"{where}: town_ids item {town_id!r} is not in towns.geojson")
        check = confirmed.get(props.get("name"))
        if check is None:
            errors.append(f"{where}: {props.get('name')!r} has no recorded confirmation from the owner (FR-065)")
        elif props.get("confirmed_on") != check["checked_on"]:
            errors.append(f"{where}: confirmed_on differs from the owner's record (FR-065)")
        _check_channel_reach(props, site_row, where, errors)
    return ids


def _names_never_shown(context_folder):
    """Every candidate channel the owner hasn't confirmed, from the records and their candidate files."""
    names = set()
    for path in Path(context_folder).glob("*_channels.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        confirmed = {check["channel"] for check in record["checks"] if check["verdict"] == "confirmed"}
        candidates = json.loads((Path(context_folder) / record["candidates_file"]).read_text(encoding="utf-8"))["features"]
        names |= {check["channel"] for check in record["checks"]} | {item["properties"]["channel"] for item in candidates}
        names -= confirmed
    return names


def check_no_unconfirmed_names(root, errors, context_folder=CONTEXT_FOLDER):
    """An unconfirmed channel must never be drawn or listed, so its name can't be in the channel files (FR-065).

    The owner's rule stops there: other files, such as a validation, can cite it as a place name.
    """
    names = _names_never_shown(context_folder)
    if not names:
        return
    pattern = re.compile(r"\b(" + "|".join(re.escape(name) for name in sorted(names)) + r")\b", re.IGNORECASE)
    for file_name in ("channels.geojson", "channel_areas.json"):
        for path in sorted(Path(root).rglob(file_name)):
            # A file that isn't valid UTF-8 is reported where its contents are checked, so it can't stop this.
            found = pattern.search(path.read_text(encoding="utf-8", errors="replace"))
            if found:
                errors.append(f"{path}: names {found.group(0)!r}, a channel the owner hasn't confirmed (FR-065)")


def check_events(path, site_id, errors):
    """Check events.json."""
    rows = _check_data_array(load_json_file(path, errors), path, errors)
    _unique_ids(rows, path, errors)
    for number, row in enumerate(rows):
        where = f"{path} row {number}"
        check_row(row, EVENTS, where, errors)
        if not isinstance(row, dict):
            continue
        if row.get("site_id") != site_id:
            errors.append(f"{where}: site_id should be {site_id!r}")
        if not 1 <= len(str(row.get("name", ""))) <= 60:
            errors.append(f"{where}: name must be 1-60 characters")


def _check_pass(row, pair, where, errors):
    """Check one pass, including that its id and copied fields agree with the pair."""
    check_row(row, PASSES, where, errors)
    if not isinstance(row, dict):
        return
    if not isinstance(row.get("polarizations"), list) or not row.get("polarizations"):
        errors.append(f"{where}: polarizations must hold at least 1 item")
    for name in ("track", "frame", "orbit_direction", "site_id"):
        if row.get(name) != pair.get(name):
            errors.append(f"{where}: {name} differs from the pair (FR-027)")
    start, end = row.get("acquired_start"), row.get("acquired_end")
    if isinstance(start, str) and isinstance(end, str) and end < start:
        errors.append(f"{where}: acquired_end is before acquired_start")
    track, frame = row.get("track"), row.get("frame")
    if not isinstance(track, int) or not isinstance(frame, int):
        return  # already reported, and the id can't be worked out without them
    if isinstance(start, str) and isinstance(row.get("id"), str):
        stamp = start.replace("-", "").replace(":", "").rstrip("Z")
        letter = "A" if row.get("orbit_direction") == "ascending" else "D"
        expected = f"{letter}{track:03d}F{frame:03d}_{stamp}"
        if row["id"] != expected:
            errors.append(f"{where}: id should be {expected!r}")


def _unequal_gaps(row):
    """Read the dates in the two pair ids, and say if the pairs span different numbers of days."""
    try:
        first, second = str(row["previous_pair_id"]).split("_")[-2:]
        third = str(row["id"]).split("_")[-1]
        days = [datetime.strptime(text, "%Y%m%d") for text in (first, second, third)]
    except (KeyError, ValueError):
        return False  # a bad id has already been reported
    return second != str(row["id"]).split("_")[-2] or days[1] - days[0] != days[2] - days[1]


def check_pair_row(row, where, errors, published=True):
    """Check one pair record (05 TBL-05), with the rules that link its columns."""
    table = PAIRS
    check_row({k: v for k, v in row.items() if k not in ("passes", "layers")}, table, where, errors)
    status = row.get("status")
    if published and status != "published":
        errors.append(f"{where}: published files may only hold status 'published' (FR-059)")
    if published and row.get("published_at") is None:
        errors.append(f"{where}: published_at must be set")
    if row.get("error_message") is not None and status != "failed":
        errors.append(f"{where}: error_message is only allowed when status is 'failed'")
    threshold = row.get("brightness_threshold_db")
    if isinstance(threshold, (int, float)) and threshold <= 0:
        errors.append(f"{where}: brightness_threshold_db must be above 0")
    used = row.get("coherence_used")
    loss = row.get("coherence_loss_threshold")
    if used is False and loss is not None:
        errors.append(f"{where}: coherence_loss_threshold must be null without coherence")
    if used is True and loss is None:
        errors.append(f"{where}: coherence_loss_threshold is needed when coherence is used")
    if used is True and (row.get("gunw_granule_id") is None or row.get("previous_pair_id") is None):
        errors.append(f"{where}: coherence needs gunw_granule_id and previous_pair_id")
    if used is True and _unequal_gaps(row):
        errors.append(f"{where}: coherence needs a previous pair with the same time gap")
    if used is False and row.get("high_confidence_area_km2") not in (0, 0.0):
        errors.append(f"{where}: no coherence means no high-confidence area (FR-030)")
    areas = [row.get(k) for k in ("high_confidence_area_km2", "low_confidence_area_km2",
                                  "new_material_area_km2")]
    if all(isinstance(a, (int, float)) for a in areas):
        # The tolerance only covers how computers store decimals.
        if abs(areas[0] + areas[1] - areas[2]) > 1e-6:
            errors.append(f"{where}: new_material_area_km2 must equal high + low")
    before, after = row.get("before_acquired_start"), row.get("after_acquired_start")
    if isinstance(before, str) and isinstance(after, str) and after <= before:
        errors.append(f"{where}: the after pass must be later than the before pass")
    _check_pair_id(row, where, errors)


def _check_pair_id(row, where, errors):
    """The pair id must spell out its site, track, frame, direction and dates."""
    try:
        letter = "A" if row["orbit_direction"] == "ascending" else "D"
        before = row["before_acquired_start"][:10].replace("-", "")
        after = row["after_acquired_start"][:10].replace("-", "")
        expected = f"{row['site_id']}_{letter}{row['track']:03d}F{row['frame']:03d}_{before}_{after}"
    except (KeyError, TypeError, ValueError):
        return  # the missing or wrong field has already been reported
    if row.get("id") != expected:
        errors.append(f"{where}: id should be {expected!r}")


def _check_legend(layer, where, errors):
    """Each legend item needs a value, label, color and confidence (NFR-008)."""
    legend = layer.get("legend")
    if not isinstance(legend, list):
        return
    if layer.get("kind") == "new_material" and not legend:
        errors.append(f"{where}: new_material legend can't be empty")
    for item in legend:
        if layer.get("kind") == "new_material" and isinstance(item, dict) and item.get("confidence") is None:
            errors.append(f"{where}: new_material legend items need a confidence (NFR-008)")
        if not isinstance(item, dict) or set(item) != {"value", "label", "color", "confidence"}:
            errors.append(f"{where}: legend items need value, label, color and confidence")
            continue
        if not isinstance(item["value"], (int, float)) or not isinstance(item["label"], str):
            errors.append(f"{where}: legend item has a bad value or label")
        if not isinstance(item["color"], str) or not HEX_COLOR.match(item["color"]):
            errors.append(f"{where}: legend color {item['color']!r} is not a hex color")
        if item["confidence"] is not None and item["confidence"] not in CONFIDENCE_LEVEL:
            errors.append(f"{where}: legend confidence {item['confidence']!r} is invalid")


def _check_image(layer, folder, where, errors):
    """The image file must exist and be exactly the size and format the record says."""
    image_path = layer.get("image_path")
    if not isinstance(image_path, str):
        return
    path = folder / image_path
    if not path.is_file():
        errors.append(f"{where}: image file {image_path} is missing")
        return
    try:
        with Image.open(path) as image:
            size, file_format = image.size, image.format
    except OSError as problem:
        errors.append(f"{where}: image {image_path} can't be read ({problem})")
        return
    if size != (layer.get("image_width"), layer.get("image_height")):
        errors.append(f"{where}: image is {size[0]} x {size[1]}, record says "
                      f"{layer.get('image_width')} x {layer.get('image_height')}")
    if str(file_format).lower() != layer.get("image_format"):
        errors.append(f"{where}: image file format is {file_format}, "
                      f"record says {layer.get('image_format')}")


def _check_grid(layer, folder, where, errors, coherence_used=True):
    """The grid file must have exactly width x height x cell-size bytes (API-010)."""
    grid_path = layer.get("grid_path")
    if grid_path is None:
        return
    for name in ("grid_dtype", "grid_scale", "grid_width", "grid_height"):
        if layer.get(name) is None:
            errors.append(f"{where}: {name} is required with grid_path")
    scale = layer.get("grid_scale")
    if isinstance(scale, (int, float)) and scale <= 0:
        errors.append(f"{where}: grid_scale must be above 0")
    path = folder / grid_path
    if not path.is_file():
        errors.append(f"{where}: grid file {grid_path} is missing")
        return
    cell_bytes = GRID_DTYPE_BYTES.get(layer.get("grid_dtype"))
    width, height = layer.get("grid_width"), layer.get("grid_height")
    if cell_bytes is None or not isinstance(width, int) or not isinstance(height, int):
        return
    content = path.read_bytes()
    if len(content) != width * height * cell_bytes:
        errors.append(f"{where}: grid has {len(content)} bytes, expected "
                      f"{width * height * cell_bytes}")
    elif layer.get("kind") == "new_material" and cell_bytes == 1:
        values = set(content)
        unknown = values - NEW_MATERIAL_VALUES
        if unknown:
            errors.append(f"{where}: grid holds invalid cell values {sorted(unknown)[:5]}")
        if not coherence_used and 2 in values:
            errors.append(f"{where}: grid has high-confidence cells without coherence (FR-030)")


def check_layer(layer, pair, folder, where, errors):
    """Check one layer record and the image and grid files it points to."""
    check_row(layer, LAYERS, where, errors)
    if not isinstance(layer, dict):
        return
    _check_bounds(layer, where, errors)
    if layer.get("pair_id") != pair.get("id"):
        errors.append(f"{where}: pair_id differs from the pair")
    if layer.get("id") != f"{pair.get('id')}_{layer.get('kind')}":
        errors.append(f"{where}: id should be <pair_id>_<kind>")
    low, high = layer.get("color_scale_min"), layer.get("color_scale_max")
    if low is not None and high is not None and high <= low:
        errors.append(f"{where}: color_scale_max must be above color_scale_min")
    if not layer.get("source_granule_ids"):
        errors.append(f"{where}: source_granule_ids needs at least 1 item (NFR-008)")
    codes = layer.get("no_data_codes")
    if isinstance(codes, dict) and any(NO_DATA_REASON.get(k) != v for k, v in codes.items()):
        errors.append(f"{where}: no_data_codes has an invalid code or reason")
    if layer.get("kind") == "new_material":
        if layer.get("grid_path") is None:
            errors.append(f"{where}: the new_material layer needs a value grid")
        if not isinstance(codes, dict) or set(codes) != set(NO_DATA_REASON):
            errors.append(f"{where}: the new_material layer needs all 3 no_data_codes (FR-011)")
    _check_legend(layer, where, errors)
    _check_image(layer, folder, where, errors)
    _check_grid(layer, folder, where, errors, pair.get("coherence_used") is not False)


def check_pair_folder(folder, site_id, errors, published=True):
    """Check one pair folder: pair.json, its 2 passes, its layers and their files."""
    path = folder / "pair.json"
    if not path.is_file():
        errors.append(f"{folder}: pair.json is missing")
        return None
    pair = load_json_file(path, errors)
    if not isinstance(pair, dict):
        errors.append(f"{path}: 'data' must be an object")
        return None
    check_pair_row(pair, path, errors, published)
    if pair.get("id") != folder.name:
        errors.append(f"{path}: id should match the folder name {folder.name!r}")
    if pair.get("site_id") != site_id:
        errors.append(f"{path}: site_id should be {site_id!r}")
    _check_pair_passes(pair, path, errors)
    _check_pair_layers(pair, folder, path, errors)
    return pair


def _check_pair_passes(pair, path, errors):
    """A pair holds exactly its before pass and its after pass."""
    passes = pair.get("passes")
    if not isinstance(passes, list) or len(passes) != 2:
        errors.append(f"{path}: 'passes' must hold exactly 2 passes")
        return
    for number, row in enumerate(passes):
        _check_pass(row, pair, f"{path} pass {number}", errors)
    by_id = {row.get("id"): row for row in passes if isinstance(row, dict)}
    granules = [row.get("granule_id") for row in passes if isinstance(row, dict)]
    if len(set(granules)) != len(granules):
        errors.append(f"{path}: the 2 passes must have different granule_id values")
    links = (("before_pass_id", "before_acquired_start"), ("after_pass_id", "after_acquired_start"))
    for id_name, start_name in links:
        row = by_id.get(pair.get(id_name))
        if row is None:
            errors.append(f"{path}: {id_name} is not in 'passes'")
        elif row.get("acquired_start") != pair.get(start_name):
            errors.append(f"{path}: {start_name} differs from the pass's acquired_start")


def _check_pair_layers(pair, folder, path, errors):
    """A pair holds one layer of each kind, each with its image and grid."""
    layers = pair.get("layers")
    if not isinstance(layers, list):
        errors.append(f"{path}: 'layers' must be an array")
        return
    for number, layer in enumerate(layers):
        check_layer(layer, pair, folder, f"{path} layer {number}", errors)
    kinds = [layer.get("kind") for layer in layers if isinstance(layer, dict)]
    if len(kinds) != len(set(kinds)):
        errors.append(f"{path}: a layer kind appears twice")
    needed = set(BASE_LAYER_KINDS)
    if pair.get("coherence_used"):
        needed.add("coherence_loss")
    if not needed <= set(kinds):
        errors.append(f"{path}: layers missing {sorted(needed - set(kinds))}")


def check_validation(path, pair_id, errors, published=False):
    """Check an optional validation.json."""
    row = load_json_file(path, errors)
    if not isinstance(row, dict):
        errors.append(f"{path}: 'data' must be an object")
        return
    check_row(row, VALIDATIONS, path, errors)
    if row.get("pair_id") != pair_id:
        errors.append(f"{path}: pair_id should be {pair_id!r}")
    if published and "DRAFT" in json.dumps(row):
        errors.append(f"{path}: a draft validation can't be published")
    items = row.get("items")
    for number, item in enumerate(items if isinstance(items, list) else []):
        where = f"{path} item {number}"
        check_row(item, VALIDATION_ITEMS, where, errors)
        if isinstance(item, dict) and item.get("validation_id") != row.get("id"):
            errors.append(f"{where}: validation_id differs from the validation")


def _check_row_matches_pair(row, pair_path, where, errors):
    """A pairs.json row must say the same as the pair's own file, or the screens disagree."""
    full = load_json_file(pair_path, [])
    if not isinstance(full, dict):
        return  # reported when the pair folder itself is checked
    columns = set(row) | (set(full) - {"passes", "layers"})
    for name in sorted(columns):
        if row.get(name) != full.get(name):
            errors.append(f"{where}: {name} differs from {pair_path.name}")


def check_pairs_list(path, site_id, site_folder, errors):
    """Check pairs.json, oldest first, and that each row matches its pair.json."""
    rows = _check_data_array(load_json_file(path, errors), path, errors)
    _unique_ids(rows, path, errors)
    starts = []
    for number, row in enumerate(rows):
        where = f"{path} row {number}"
        if not isinstance(row, dict):
            errors.append(f"{where}: expected an object")
            continue
        check_pair_row(row, where, errors)
        if row.get("site_id") != site_id:
            errors.append(f"{where}: site_id should be {site_id!r}")
        starts.append(str(row.get("after_acquired_start")))
        pair_path = site_folder / "pairs" / str(row.get("id")) / "pair.json"
        if not pair_path.is_file():
            errors.append(f"{where}: this pair has no pair.json folder")
            continue
        _check_row_matches_pair(row, pair_path, where, errors)
    if starts != sorted(starts):
        errors.append(f"{path}: pairs must be sorted oldest first by after_acquired_start")
    return {row.get("id") for row in rows if isinstance(row, dict)}


def check_channel_areas(path, site_id, channel_ids, pair_ids, errors):
    """Check channel_areas.json: one row per channel and pair, with the rules that link its columns."""
    rows = _check_data_array(load_json_file(path, errors), path, errors)
    _unique_ids(rows, path, errors)
    seen = set()
    for number, row in enumerate(rows):
        where = f"{path} row {number}"
        check_row(row, CHANNEL_AREAS, where, errors)
        if not isinstance(row, dict):
            continue
        channel_id, pair_id = row.get("channel_id"), row.get("pair_id")
        seen.add((channel_id, pair_id))
        if row.get("site_id") != site_id:
            errors.append(f"{where}: site_id should be {site_id!r}")
        if channel_id not in channel_ids:
            errors.append(f"{where}: channel_id {channel_id!r} is not in channels.geojson")
        if pair_id not in pair_ids:
            errors.append(f"{where}: pair_id {pair_id!r} is not a published pair")
        if row.get("id") != f"{channel_id}__{pair_id}":
            errors.append(f"{where}: id should be <channel_id>__<pair_id>")
        flagged, checked = row.get("flagged_area_km2"), row.get("checked_area_km2")
        if not isinstance(checked, (int, float)):
            continue
        if (flagged is None) != (checked == 0):
            errors.append(f"{where}: flagged_area_km2 must be null when checked_area_km2 is 0, and only then")
        if isinstance(flagged, (int, float)) and flagged > checked:
            errors.append(f"{where}: flagged_area_km2 is above checked_area_km2")
    for channel_id in sorted(channel_ids):
        for pair_id in sorted(pair_ids):
            if (channel_id, pair_id) not in seen:
                errors.append(f"{path}: no row for channel {channel_id!r} in pair {pair_id!r} (US-026/AC-1)")


def check_site_folder(folder, source_ids, errors, published=True, site_row=None):
    """Check the files of one site. Which ones must exist is decided in check_data_dir."""
    site_id = folder.name
    town_ids = set()
    channel_ids = set()
    if (folder / "towns.geojson").is_file():
        town_ids = check_towns(folder / "towns.geojson", site_id, source_ids, errors)
    if (folder / "land.geojson").is_file():
        check_land(folder / "land.geojson", site_id, source_ids, errors)
    if (folder / "channels.geojson").is_file():
        if site_row and site_row.get("channel_strip_half_width_m") is None:
            errors.append(f"{folder / 'channels.geojson'}: a site with channels needs channel_strip_half_width_m (FR-064)")
        channel_ids = check_channels(folder / "channels.geojson", site_id, source_ids, town_ids, errors, site_row)
    if (folder / "events.json").is_file():
        check_events(folder / "events.json", site_id, errors)
    listed = set()
    if (folder / "pairs.json").is_file():
        listed = check_pairs_list(folder / "pairs.json", site_id, folder, errors)
    if (folder / "channel_areas.json").is_file():
        check_channel_areas(folder / "channel_areas.json", site_id, channel_ids, listed, errors)
    for pair_folder in sorted((folder / "pairs").glob("*")):
        if not pair_folder.is_dir():
            continue
        pair = check_pair_folder(pair_folder, site_id, errors, published)
        if published and pair_folder.name not in listed:
            errors.append(f"{pair_folder}: this folder is not listed in pairs.json (FR-059)")
        if pair and (pair_folder / "validation.json").is_file():
            check_validation(pair_folder / "validation.json", pair.get("id"), errors, published)
    return _known_files(folder)


def _known_files(folder):
    """List the JSON and GeoJSON files that this check knows how to read."""
    names = ["towns.geojson", "land.geojson", "channels.geojson", "channel_areas.json", "events.json", "pairs.json"]
    known = {folder / name for name in names}
    for pair_folder in (folder / "pairs").glob("*"):
        known |= {pair_folder / "pair.json", pair_folder / "validation.json"}
    return known


def _check_required_top_files(root, errors):
    """Without these, no visitor can use the site at all."""
    for name in ("sites.json", "sources.json"):
        if not (root / name).is_file():
            errors.append(f"{root / name}: this required file is missing")


def _check_required_site_files(folder, errors, site_row):
    """A listed site needs these to open. Channels and events are optional for the screen (03 section 5),
    but a site that says it has channels must have them, or its Channels button would lead nowhere."""
    names = ["towns.geojson", "land.geojson", "pairs.json"]
    if site_row.get("channel_strip_half_width_m") is not None:
        names += ["channels.geojson", "channel_areas.json"]
    for name in names:
        if not (folder / name).is_file():
            errors.append(f"{folder / name}: this required file is missing")


def check_data_dir(root, published=True):
    """Check everything under a data folder and return a list of problems (empty = good)."""
    root = Path(root)
    errors = []
    known = {root / "sites.json", root / "sources.json"}
    if published:
        _check_required_top_files(root, errors)
    source_ids = set()
    if (root / "sources.json").is_file():
        source_ids = check_sources(root / "sources.json", errors)
    site_rows = []
    if (root / "sites.json").is_file():
        site_rows = check_sites(root / "sites.json", errors)
    for row in site_rows:
        site_id = row.get("id") if isinstance(row, dict) else None
        if site_id and not (root / "sites" / str(site_id)).is_dir():
            errors.append(f"{root / 'sites.json'}: site {site_id!r} has no data folder")
        elif site_id and published:
            _check_required_site_files(root / "sites" / str(site_id), errors, row)
    rows_by_id = {row.get("id"): row for row in site_rows if isinstance(row, dict)}
    for folder in sorted((root / "sites").glob("*")):
        if folder.is_dir():
            known |= check_site_folder(folder, source_ids, errors, published, rows_by_id.get(folder.name))
    if published:
        check_no_unconfirmed_names(root, errors)
    # Every data file must be one the contract describes. Drafts have their own folder in pipeline/out.
    for pattern in ("*.json", "*.geojson"):
        for path in sorted(root.rglob(pattern)):
            if path not in known and "validation_drafts" not in path.parts and "reports" not in path.parts:
                errors.append(f"{path}: this file is not part of the data contract")
    return errors


def main(argv=None):
    """Command-line entry point: print problems and return 1 if there are any."""
    parser = argparse.ArgumentParser(description="Check data files against docs/05.")
    parser.add_argument("folder", nargs="?", default=str(REPO_ROOT / "site" / "data"))
    parser.add_argument("--unpublished", action="store_true",
                        help="check pipeline/out, where pairs have status 'ready'")
    args = parser.parse_args(argv)
    errors = check_data_dir(args.folder, published=not args.unpublished)
    for error in errors:
        print(error)
    print(f"Contract check: {len(errors)} error(s) in {args.folder}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

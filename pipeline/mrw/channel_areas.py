"""Task T-010: write the channels the owner confirmed, with their towns, sources and strips.

Run from the project folder:
    python pipeline/mrw/channel_areas.py mayon

It writes site/data/sites/<id>/channels.geojson. A candidate line gets in only if the owner's check
in pipeline/context/<id>_channels.json says "confirmed", and its line is copied exactly as it is.

A strip is the ground within a set distance of a channel's line. Strips stop at the site's reach
distance, because the radar map doesn't look further from the summit than that.
"""
import json
import sys
from pathlib import Path

import numpy as np
from pyproj import Transformer
from shapely import set_precision, transform as transform_points
from shapely.geometry import Point, mapping, shape

# Lets this file run as a script from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mrw.config import SITES_FOLDER, load_site_config, utc_now_text
from mrw.context import CONTEXT_FOLDER, COORDINATE_GRID_DEG, DATA_FOLDER, write_geojson, write_sources

# ODbL asks for the license to be clear on the data itself, and the channel lines come from OpenStreetMap.
LINE_LICENSE = "ODbL 1.0, (c) OpenStreetMap contributors"
# A line cut at a town's edge can touch the next town, so a town counts only with this much of the line.
MIN_TOWN_LENGTH_M = 100
# A channel's name is drawn this far along the part of its line that the map checks.
LABEL_SHARE = 0.6
# Candidate lines have 7 decimals, so the parts cut from them keep the same.
LINE_DECIMALS = 7


class ChannelError(Exception):
    """The channel files can't be built. The message says why."""


def utm_epsg(lon, lat):
    """The UTM map projection, in metres, for a place. The radar's own grid uses the same one."""
    zone = int((lon + 180) // 6) + 1
    return (32600 if lat >= 0 else 32700) + zone


def move_points(geometry, transformer):
    """Run every point of a shape through a map-projection conversion."""
    def convert(points):
        xs, ys = transformer.transform(points[:, 0], points[:, 1])
        return np.column_stack([xs, ys])
    return transform_points(geometry, convert)


def strip_half_width(config, config_path):
    """How far a strip goes on each side of the line. A site with channels must set it (FR-064)."""
    width = config.get("channel_strip_half_width_m")
    if width is None:
        raise ChannelError(f"Channel strip width missing in site config: {config_path}")
    return width


def reach_circle(config, to_metres):
    """The ground the map checks, as a circle in metres. None for a site with no reach distance."""
    reach_km = (config.get("filters") or {}).get("max_distance_km")
    if not reach_km or config.get("summit_lon") is None:
        return None
    return Point(to_metres.transform(config["summit_lon"], config["summit_lat"])).buffer(reach_km * 1000, quad_segs=64)


def build_strip(line, half_width_m, circle):
    """The strip around a line in metres: the line's width on each side, stopping at the reach."""
    strip = line.buffer(half_width_m, quad_segs=4)
    return strip.intersection(circle) if circle is not None else strip


def split_at_reach(line, circle):
    """Cut a line in metres into the part the map checks and the part past the reach, or None."""
    if circle is None:
        return line, None
    beyond = line.difference(circle)
    return line.intersection(circle), None if beyond.is_empty else beyond


def towns_along(line, towns):
    """The ids of the towns a line passes through, the one with the most of the line first."""
    lengths = [(line.intersection(outline).length, town_id) for town_id, outline in towns]
    return [town_id for length, town_id in sorted(lengths, reverse=True) if length >= MIN_TOWN_LENGTH_M]


def rounded_line(geometry):
    """A line as GeoJSON, rounded like the candidate lines."""
    def rounded(points):
        return np.round(points, LINE_DECIMALS)
    return mapping(transform_points(geometry, rounded))


def channel_feature(check, candidate, site_id, line_source_id, half_width_m, circle, towns, to_metres, to_degrees):
    """Build one `channels` row (docs/05 TBL-03) from the owner's check and the candidate line."""
    line = move_points(shape(candidate["geometry"]), to_metres)
    checked, not_checked = split_at_reach(line, circle)
    strip = set_precision(move_points(build_strip(line, half_width_m, circle), to_degrees), COORDINATE_GRID_DEG)
    label = move_points(checked.interpolate(LABEL_SHARE, normalized=True), to_degrees)
    return {
        "type": "Feature",
        "id": check["id"],
        "properties": {
            "id": check["id"],
            "site_id": site_id,
            "name": check["channel"],
            "alt_names": check["alt_names"],
            "town_ids": towns_along(line, towns),
            "name_source": check["name_source"],
            "name_source_url": check["name_source_url"],
            "line_source_id": line_source_id,
            "confirmed_by": check["checked_by"],
            "confirmed_on": check["checked_on"],
            "imagery_date": check["imagery_date"],
            "label_lat": round(label.y, 5),
            "label_lon": round(label.x, 5),
            "strip_geometry": mapping(strip),
            "checked_geometry": rounded_line(move_points(checked, to_degrees)),
            "not_checked_geometry": rounded_line(move_points(not_checked, to_degrees)) if not_checked is not None else None,
        },
        # The owner confirmed this line, so it's published exactly as it is.
        "geometry": candidate["geometry"],
    }


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_channels(site_id, data_folder=DATA_FOLDER, context_folder=CONTEXT_FOLDER, sites_folder=SITES_FOLDER, now=None):
    """Write channels.geojson for a site. Returns its Features."""
    config_path = Path(sites_folder) / f"{site_id}.json"
    config = load_site_config(config_path)
    record = read_json(Path(context_folder) / f"{site_id}_channels.json")
    half_width_m = strip_half_width(config, config_path)
    epsg = utm_epsg(config["center_lon"], config["center_lat"])
    to_metres = Transformer.from_crs(4326, epsg, always_xy=True)
    to_degrees = Transformer.from_crs(epsg, 4326, always_xy=True)
    site_folder = Path(data_folder) / "sites" / site_id
    towns = [(town["properties"]["id"], move_points(shape(town["geometry"]), to_metres))
             for town in read_json(site_folder / "towns.geojson")["features"]]
    candidates = {item["properties"]["channel"]: item
                  for item in read_json(Path(context_folder) / record["candidates_file"])["features"]}
    circle = reach_circle(config, to_metres)
    features = [channel_feature(check, candidates[check["channel"]], site_id, record["line_source_id"], half_width_m,
                                circle, towns, to_metres, to_degrees)
                for check in record["checks"] if check["verdict"] == "confirmed"]
    features.sort(key=lambda feature: feature["properties"]["name"])
    write_geojson(site_folder / "channels.geojson", features, now or utc_now_text(), LINE_LICENSE)
    return features


def main(argv):
    """Command-line entry point. Prints the stop message and returns 1 on failure."""
    site_id = argv[0]
    try:
        features = build_channels(site_id)
    except ChannelError as problem:
        print(problem)
        return 1
    write_sources(DATA_FOLDER, CONTEXT_FOLDER, utc_now_text())
    for feature in features:
        print(feature["properties"]["name"], feature["properties"]["town_ids"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

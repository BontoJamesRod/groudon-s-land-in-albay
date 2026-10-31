"""Tests for the context files (T-009, T-011)."""
from shapely.geometry import Point, box, mapping, shape

from mrw.config import load_site
from mrw.context import build_land, build_towns, label_point, town_display_name, town_id


def source_town(name, level, geom):
    return {"properties": {"adm3_en": name, "adm3_psgc": 500517000, "geo_level": level},
            "geometry": mapping(geom)}


def test_city_names_read_the_way_people_say_them():
    assert town_display_name("City of Tabaco") == "Tabaco City"
    assert town_display_name("Daraga") == "Daraga"
    assert town_id("mayon", "Tabaco City") == "mayon_tabaco_city"
    assert town_id("mayon", "Rapu-Rapu") == "mayon_rapu_rapu"


def test_towns_are_clipped_to_the_site_and_outsiders_dropped():
    config = load_site("mayon")
    towns = build_towns([
        source_town("City of Tabaco", "City", box(123.70, 13.30, 123.90, 13.50)),
        source_town("Far Away", "Mun", box(120.0, 10.0, 120.1, 10.1)),
    ], config)
    assert [t["properties"]["name"] for t in towns] == ["Tabaco City"]
    assert towns[0]["properties"]["kind"] == "city"
    west, south, east, north = shape(towns[0]["geometry"]).bounds
    assert east <= config["bounds_east"] and north <= config["bounds_north"]
    assert west >= 123.70 and south >= 13.30


def test_label_stays_inside_a_c_shaped_town():
    c_shape = box(0, 0, 3, 3).difference(box(1, 1, 3, 2))
    point = label_point(c_shape)
    assert c_shape.covers(Point(point.x, point.y))


def test_land_is_the_union_of_the_towns():
    config = load_site("mayon")
    towns = build_towns([
        source_town("A", "Mun", box(123.60, 13.20, 123.65, 13.25)),
        source_town("B", "Mun", box(123.65, 13.20, 123.70, 13.25)),
    ], config)
    land = build_land(towns, config)
    assert land[0]["id"] == "mayon_land"
    assert abs(shape(land[0]["geometry"]).area - 0.10 * 0.05) < 1e-6

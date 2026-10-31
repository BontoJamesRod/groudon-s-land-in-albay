"""Tests for the channels file, its strips and the owner's check (T-010, T-073, TC-073, TC-074)."""
import json
import re
from pathlib import Path

import pytest
from pyproj import Transformer
from shapely.geometry import LineString, Point, shape

from mrw.channel_areas import ChannelError, build_channels, build_strip, split_at_reach, strip_half_width, towns_along, utm_epsg
from mrw.config import load_site

REPO = Path(__file__).resolve().parents[2]
CONTEXT = REPO / "pipeline" / "context"
MAYON = REPO / "site" / "data" / "sites" / "mayon"
CONFIRMED = ["Basud", "Lidong", "Mi-isi", "Padang"]
NEVER_SHOWN = ["Bonga", "Buyuan", "Mabinit", "Maninila", "Masarawag", "Matanag"]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def published_channels():
    return read(MAYON / "channels.geojson")["features"]


def test_only_the_confirmed_channels_are_published():
    assert [item["properties"]["name"] for item in published_channels()] == CONFIRMED


@pytest.mark.parametrize("name", NEVER_SHOWN)
def test_tc074_no_other_candidate_is_anywhere_under_site_data(name):
    pattern = re.compile(rf"\b{name}\b", re.IGNORECASE)
    data = REPO / "site" / "data"
    files = [path for suffix in ("*.json", "*.geojson") for path in data.rglob(suffix)]
    assert files and [path for path in files if pattern.search(path.read_text(encoding="utf-8"))] == []


def test_the_confirmed_lines_are_used_exactly_as_they_are():
    candidates = {item["properties"]["channel"]: item for item in read(CONTEXT / "channel_name_candidates.geojson")["features"]}
    for item in published_channels():
        assert item["geometry"] == candidates[item["properties"]["name"]]["geometry"]


def test_every_channel_has_a_town_a_name_source_and_a_confirmation():
    for item in published_channels():
        props = item["properties"]
        assert props["town_ids"] and props["name_source"].startswith("PHIVOLCS") and props["name_source_url"]
        assert (props["confirmed_by"], props["confirmed_on"], props["imagery_date"]) == ("project owner", "2026-11-01", "2026-05-16")


def test_the_record_gives_a_verdict_or_no_verdict_for_every_candidate():
    record = read(CONTEXT / "mayon_channels.json")
    candidates = {item["properties"]["channel"] for item in read(CONTEXT / "channel_name_candidates.geojson")["features"]}
    assert {check["channel"] for check in record["checks"]} == candidates
    assert {check["channel"] for check in record["checks"] if check["verdict"] == "confirmed"} == set(CONFIRMED)


def test_the_owner_checks_report_says_the_same_as_the_record():
    report = (REPO / "pipeline" / "reports" / "owner-checks.md").read_text(encoding="utf-8")
    words = {"confirmed": "Confirmed", "not_confirmed": "Not confirmed", "no_verdict": "No verdict"}
    for check in read(CONTEXT / "mayon_channels.json")["checks"]:
        date, imagery, who = check.get("checked_on", "—"), check.get("imagery_date", "—"), check.get("checked_by")
        who = "Project owner" if who else "—"
        assert f"| {check['channel']} | {words[check['verdict']]} | {date} | {imagery} | {who} |" in report


def test_a_site_with_channels_needs_a_strip_width():
    with pytest.raises(ChannelError, match="Channel strip width missing in site config: some/file.json"):
        strip_half_width({}, "some/file.json")


def test_tc073_the_pipeline_stops_without_a_strip_width(tmp_path):
    config = load_site("mayon")
    del config["channel_strip_half_width_m"]
    (tmp_path / "mayon.json").write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ChannelError, match="Channel strip width missing in site config: .*mayon.json"):
        build_channels("mayon", sites_folder=tmp_path)


def test_the_site_config_sets_the_owners_strip_width():
    assert strip_half_width(load_site("mayon"), "mayon.json") == 200


def test_strip_goes_the_width_on_each_side_of_the_line():
    strip = build_strip(LineString([(0, 0), (1000, 0)]), 200, None)
    assert strip.bounds == pytest.approx((-200, -200, 1200, 200))
    # Inside: a rectangle of 1000 x 400 m, and two half circles of radius 200 m, drawn with short straight sides.
    assert strip.area == pytest.approx(1000 * 400 + 3.14159 * 200 ** 2, rel=0.02)


def test_strip_stops_at_the_reach():
    circle = Point(0, 0).buffer(1000, quad_segs=64)
    strip = build_strip(LineString([(0, 0), (5000, 0)]), 200, circle)
    assert strip.bounds[2] == pytest.approx(1000, abs=0.5)


def test_a_line_past_the_reach_is_split_there():
    circle = Point(0, 0).buffer(1000, quad_segs=64)
    checked, beyond = split_at_reach(LineString([(0, 0), (5000, 0)]), circle)
    assert checked.length == pytest.approx(1000, abs=0.5)
    assert beyond.length == pytest.approx(4000, abs=0.5)


def test_a_line_inside_the_reach_has_no_part_past_it():
    circle = Point(0, 0).buffer(1000, quad_segs=64)
    line = LineString([(0, 0), (500, 0)])
    checked, beyond = split_at_reach(line, circle)
    assert checked.length == pytest.approx(500) and beyond is None


def test_a_site_with_no_reach_checks_the_whole_line():
    line = LineString([(0, 0), (5000, 0)])
    assert split_at_reach(line, None) == (line, None)


def test_a_town_counts_only_with_enough_of_the_line():
    towns = [("big", shape({"type": "Polygon", "coordinates": [[(0, -9), (900, -9), (900, 9), (0, 9), (0, -9)]]})),
             ("touched", shape({"type": "Polygon", "coordinates": [[(900, -9), (950, -9), (950, 9), (900, 9), (900, -9)]]})),
             ("second", shape({"type": "Polygon", "coordinates": [[(950, -9), (1300, -9), (1300, 9), (950, 9), (950, -9)]]}))]
    assert towns_along(LineString([(0, 0), (1300, 0)]), towns) == ["big", "second"]


def test_the_channels_are_in_the_towns_their_lines_cross():
    towns = {item["id"]: item["properties"]["town_ids"] for item in published_channels()}
    assert towns == {"mayon_basud": ["mayon_santo_domingo"], "mayon_lidong": ["mayon_santo_domingo"],
                     "mayon_miisi": ["mayon_daraga", "mayon_legazpi_city"],
                     "mayon_padang": ["mayon_santo_domingo", "mayon_legazpi_city"]}


def test_utm_zones():
    assert utm_epsg(123.6856, 13.2572) == 32651
    assert utm_epsg(-80.865, 7.477) == 32617


def test_strips_and_checked_parts_stay_inside_the_reach_on_the_real_data():
    config = load_site("mayon")
    to_metres = Transformer.from_crs(4326, utm_epsg(config["center_lon"], config["center_lat"]), always_xy=True)
    summit = Point(to_metres.transform(config["summit_lon"], config["summit_lat"]))
    for item in published_channels():
        for key in ("strip_geometry", "checked_geometry"):
            points = shape(item["properties"][key])
            xy = points.exterior.coords if points.geom_type == "Polygon" else points.coords
            furthest = max(Point(to_metres.transform(*point)).distance(summit) for point in xy)
            assert furthest <= 10_002

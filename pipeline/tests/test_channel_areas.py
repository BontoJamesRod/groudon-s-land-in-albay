"""Tests for the channels file, its strips, its areas and the owner's check (T-010, T-073, T-074, TC-072 to TC-074)."""
import json
import re
from pathlib import Path

import numpy as np
import pytest
from pyproj import Transformer
from shapely.geometry import LineString, Point, mapping, shape

from mrw.channel_areas import (ChannelError, build_channels, build_strip, cell_area_km2, channel_row, move_points, read_grid,
                               rebuild_channel_areas, split_at_reach, strip_cells, strip_half_width, towns_along, utm_epsg)
from mrw.config import SITES_FOLDER, load_site

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


# A small made-up grid of 5 x 5 cells, each 0.01 degrees. At 13 degrees north a cell is about
# 1.084 km wide and 1.106 km tall, so its area is about 1.199 km2.
WEST, SOUTH = 123.0, 13.0
LAYER = {"bounds_west": WEST, "bounds_east": WEST + 0.05, "bounds_south": SOUTH, "bounds_north": SOUTH + 0.05,
         "grid_width": 5, "grid_height": 5, "kind": "new_material", "grid_path": "new_material.bin"}
ONE_CELL_KM2 = 1.199
NOW = "2026-11-01T00:00:00Z"


def cell_centre(row, column):
    return WEST + (column + 0.5) * 0.01, SOUTH + 0.05 - (row + 0.5) * 0.01


def small_channel(name="Test", half_width_m=1000, reach_m=3300):
    """A channel along the grid's middle row. Its strip takes in that row only, as far as the reach."""
    epsg = utm_epsg(WEST, SOUTH)
    to_metres = Transformer.from_crs(4326, epsg, always_xy=True)
    to_degrees = Transformer.from_crs(epsg, 4326, always_xy=True)
    start, end = cell_centre(2, 0), cell_centre(2, 4)
    line = move_points(LineString([start, end]), to_metres)
    circle = Point(to_metres.transform(*start)).buffer(reach_m, quad_segs=64)
    strip = move_points(build_strip(line, half_width_m, circle), to_degrees)
    return {"properties": {"id": f"mayon_{name.lower()}", "site_id": "mayon", "strip_geometry": mapping(strip)}}


def test_the_strip_cells_are_the_ones_whose_centres_are_inside():
    inside = strip_cells(small_channel()["properties"]["strip_geometry"], LAYER)
    # The middle row, up to the reach: centres are 0, 1.08, 2.17 and 3.25 km from the start, and the last is 4.34 km.
    assert np.argwhere(inside).tolist() == [[2, 0], [2, 1], [2, 2], [2, 3]]


def test_cell_area_matches_a_hand_calculation():
    assert cell_area_km2(LAYER) == pytest.approx(ONE_CELL_KM2, rel=0.005)


def test_tc072_only_flagged_cells_inside_the_strip_and_the_reach_count():
    cells = np.zeros((5, 5), dtype="uint8")
    cells[2, 1] = 1  # low, inside the strip: counts
    cells[2, 2] = 2  # high, inside the strip: counts
    cells[0, 1] = 2  # outside the strip: doesn't count
    cells[2, 4] = 1  # on the line, but beyond the reach: doesn't count
    row = channel_row(small_channel(), "mayon_A111F008_20261007_20261019", cells, LAYER, NOW)
    assert row["flagged_area_km2"] == pytest.approx(2 * ONE_CELL_KM2, abs=0.02)
    assert row["checked_area_km2"] == pytest.approx(4 * ONE_CELL_KM2, abs=0.05)
    assert row["id"] == "mayon_test__mayon_A111F008_20261007_20261019"


def test_cells_with_no_radar_value_are_not_checked_ground():
    cells = np.zeros((5, 5), dtype="uint8")
    cells[2, 0] = 254  # sea
    cells[2, 1] = 253  # marked invalid by the product
    cells[2, 2] = 255  # outside radar coverage
    row = channel_row(small_channel(), "pair", cells, LAYER, NOW)
    assert row["flagged_area_km2"] == 0
    assert row["checked_area_km2"] == pytest.approx(ONE_CELL_KM2, abs=0.01)


def test_a_strip_with_no_radar_value_has_no_area_rather_than_zero():
    cells = np.full((5, 5), 254, dtype="uint8")
    row = channel_row(small_channel(), "pair", cells, LAYER, NOW)
    assert row["flagged_area_km2"] is None
    assert row["checked_area_km2"] == 0


def test_a_few_flagged_cells_are_never_reported_as_nothing():
    tiny = {**LAYER, "bounds_east": WEST + 0.0005, "bounds_north": SOUTH + 0.0005}
    channel = {"properties": {"id": "mayon_test", "site_id": "mayon", "strip_geometry": mapping(shape({
        "type": "Polygon", "coordinates": [[(WEST, SOUTH), (WEST + 0.0005, SOUTH), (WEST + 0.0005, SOUTH + 0.0005), (WEST, SOUTH + 0.0005), (WEST, SOUTH)]]}))}}
    cells = np.zeros((5, 5), dtype="uint8")
    cells[2, 2] = 1
    assert channel_row(channel, "pair", cells, tiny, NOW)["flagged_area_km2"] == 0.01


@pytest.fixture
def small_site(tmp_path):
    """A data folder with 2 channels and 2 small pairs."""
    site = tmp_path / "sites" / "mayon"
    channels = [small_channel("One"), small_channel("Two")]
    pairs = ["mayon_A111F008_20261007_20261019", "mayon_D104F082_20261007_20261019"]
    for number, pair_id in enumerate(pairs):
        folder = site / "pairs" / pair_id
        folder.mkdir(parents=True)
        cells = np.zeros((5, 5), dtype="uint8")
        cells[2, number] = 1
        (folder / "new_material.bin").write_bytes(cells.tobytes())
        (folder / "pair.json").write_text(json.dumps({"data": {"layers": [LAYER]}}), encoding="utf-8")
    (site / "pairs.json").write_text(json.dumps({"data": [{"id": pair_id} for pair_id in pairs]}), encoding="utf-8")
    (site / "channels.geojson").write_text(json.dumps({"features": channels}), encoding="utf-8")
    return tmp_path


def test_tc072_there_is_one_row_per_channel_and_pair(small_site):
    rows = rebuild_channel_areas("mayon", small_site, SITES_FOLDER, NOW)
    assert len(rows) == 4
    assert len({row["id"] for row in rows}) == 4
    assert {(row["channel_id"], row["pair_id"]) for row in rows} == {
        (channel, pair) for channel in ("mayon_one", "mayon_two")
        for pair in ("mayon_A111F008_20261007_20261019", "mayon_D104F082_20261007_20261019")}
    saved = read(small_site / "sites" / "mayon" / "channel_areas.json")
    assert saved["data"] == rows
    assert "OpenStreetMap" in saved["meta"]["license"]


def test_rebuilding_keeps_when_a_row_was_first_written(small_site):
    rebuild_channel_areas("mayon", small_site, SITES_FOLDER, NOW)
    rows = rebuild_channel_areas("mayon", small_site, SITES_FOLDER, "2026-11-02T00:00:00Z")
    assert {row["created_at"] for row in rows} == {NOW}
    assert {row["updated_at"] for row in rows} == {"2026-11-02T00:00:00Z"}


def test_a_site_with_no_channels_has_nothing_to_rebuild(tmp_path):
    assert rebuild_channel_areas("panama", tmp_path, SITES_FOLDER, NOW) == []
    assert not (tmp_path / "sites" / "panama" / "channel_areas.json").exists()


def test_tc073_rebuilding_stops_without_a_strip_width(small_site, tmp_path):
    config = load_site("mayon")
    del config["channel_strip_half_width_m"]
    folder = tmp_path / "configs"
    folder.mkdir()
    (folder / "mayon.json").write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ChannelError, match="Channel strip width missing in site config"):
        rebuild_channel_areas("mayon", small_site, folder, NOW)


def published_rows():
    return read(MAYON / "channel_areas.json")["data"]


def latest_layer(pair_id):
    pair = read(MAYON / "pairs" / pair_id / "pair.json")["data"]
    return next(item for item in pair["layers"] if item["kind"] == "new_material")


def test_the_published_areas_are_up_to_date():
    pairs = {row["id"] for row in read(MAYON / "pairs.json")["data"]}
    assert {row["pair_id"] for row in published_rows()} == pairs
    assert len(published_rows()) == len(pairs) * len(CONFIRMED)
    channels = {item["id"]: item for item in published_channels()}
    for row in published_rows():
        layer = latest_layer(row["pair_id"])
        cells = read_grid(MAYON / "pairs" / row["pair_id"], layer)
        fresh = channel_row(channels[row["channel_id"]], row["pair_id"], cells, layer, NOW)
        assert (fresh["flagged_area_km2"], fresh["checked_area_km2"]) == (row["flagged_area_km2"], row["checked_area_km2"])


def test_the_grid_gives_about_the_same_total_as_the_pair():
    """The pair's total comes from the radar's own grid, and the published grid is a copy of it on map cells."""
    for summary in read(MAYON / "pairs.json")["data"]:
        layer = latest_layer(summary["id"])
        cells = read_grid(MAYON / "pairs" / summary["id"], layer)
        total = np.count_nonzero(np.isin(cells, (1, 2))) * cell_area_km2(layer)
        assert total == pytest.approx(summary["new_material_area_km2"], rel=0.03)


def test_a_channels_flagged_area_is_never_more_than_the_pairs():
    totals = {row["id"]: row["new_material_area_km2"] for row in read(MAYON / "pairs.json")["data"]}
    for row in published_rows():
        assert row["flagged_area_km2"] <= totals[row["pair_id"]]

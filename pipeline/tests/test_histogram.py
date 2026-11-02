"""TC-083 and TC-084: the numbers behind the brightness histogram (F-21)."""
import json
from pathlib import Path

import numpy as np
import pytest

from mrw.channel_areas import cell_area_km2, strip_cells
from mrw.config import load_site
from mrw.contract_check import check_data_dir
from mrw.histogram import BIN_COUNT, BIN_START_DB, BIN_WIDTH_DB, channel_histogram_row, count_bins, histogram_row

REPO = Path(__file__).resolve().parents[2]
SITES = REPO / "site" / "data" / "sites"


def read_data(path):
    return json.loads(path.read_text(encoding="utf-8"))["data"]


def published_pairs():
    return [(site.name, folder) for site in sorted(SITES.iterdir()) for folder in sorted((site / "pairs").iterdir())]


def grid_of(folder):
    pair = read_data(folder / "pair.json")
    layer = next(item for item in pair["layers"] if item["kind"] == "new_material")
    return pair, layer, np.fromfile(folder / layer["grid_path"], dtype="uint8").reshape(layer["grid_height"], layer["grid_width"])


def test_a_bin_holds_its_lower_edge_and_not_its_upper_edge():
    counts = count_bins(np.array([0.0, 0.1, 0.25, -0.1]))
    zero = round(-BIN_START_DB / BIN_WIDTH_DB)
    assert counts["counts"][zero] == 2 and counts["counts"][zero + 1] == 1 and counts["counts"][zero - 1] == 1


def test_values_past_the_ends_are_counted_on_their_own():
    counts = count_bins(np.array([-10.5, -10.0, 9.99, 10.0, 11.0]))
    assert (counts["below"], counts["above"]) == (1, 2)
    assert sum(counts["counts"]) == 2 and len(counts["counts"]) == BIN_COUNT


def test_only_checked_land_inside_the_reach_is_counted():
    change = np.array([[4.0, 0.5, np.nan, 5.0], [-4.0, 1.0, 2.0, 6.0]])
    classes = np.array([[1, 0, 253, 0], [1, 0, 254, 0]], dtype="uint8")
    in_reach = np.array([[True, True, True, False], [True, True, True, False]])
    row = histogram_row("pair", "mayon", change, classes, in_reach)
    # Sea and masked cells are left out, and so is what lies past the reach.
    assert row["total_cells"] == 4 and row["flagged_cells"] == 2 and row["flagged_share"] == 0.5


def test_a_site_with_no_checked_ground_has_a_share_of_zero():
    row = histogram_row("pair", "mayon", np.full((1, 2), np.nan), np.full((1, 2), 254, dtype="uint8"), np.ones((1, 2), dtype=bool))
    assert row["total_cells"] == 0 and row["flagged_share"] == 0


def test_a_channels_counts_stay_inside_its_strip():
    layer = {"bounds_west": 0.0, "bounds_south": 0.0, "bounds_east": 4.0, "bounds_north": 2.0, "grid_width": 4, "grid_height": 2}
    ring = [[0, 0], [1, 0], [1, 2], [0, 2], [0, 0]]
    channels = [{"properties": {"id": "mayon_test", "strip_geometry": {"type": "Polygon", "coordinates": [ring]}}}]
    change, classes = np.array([[5.0, 1, 1, 1], [1.0, 1, 1, 1]]), np.array([[1, 0, 0, 0], [0, 0, 0, 0]], dtype="uint8")
    row = channel_histogram_row("pair", "mayon", change, classes, np.ones((2, 4), dtype=bool), channels, layer)
    assert row["channels"][0]["channel_id"] == "mayon_test"
    assert row["channels"][0]["total_cells"] == 2 and row["channels"][0]["flagged_cells"] == 1


@pytest.mark.parametrize("site_id, folder", published_pairs(), ids=lambda value: getattr(value, "name", value))
def test_tc084_flagged_cells_match_the_published_grid(site_id, folder):
    histogram = read_data(folder / "histogram.json")
    pair, _layer, grid = grid_of(folder)
    assert histogram["pair_id"] == pair["id"] and histogram["site_id"] == site_id
    assert histogram["flagged_cells"] == np.count_nonzero(np.isin(grid, (1, 2)))
    assert sum(histogram["counts"]) + histogram["below"] + histogram["above"] == histogram["total_cells"]
    assert histogram["total_cells"] <= np.count_nonzero(np.isin(grid, (0, 1, 2)))


@pytest.mark.parametrize("site_id, folder", published_pairs(), ids=lambda value: getattr(value, "name", value))
def test_tc084_the_tails_past_the_line_hold_the_flagged_cells(site_id, folder):
    histogram = read_data(folder / "histogram.json")
    threshold = load_site(site_id)["thresholds"]["brightness_threshold_db"]
    assert read_data(folder / "pair.json")["brightness_threshold_db"] == threshold
    edge = round((threshold - BIN_START_DB) / BIN_WIDTH_DB)
    other_edge = round((-threshold - BIN_START_DB) / BIN_WIDTH_DB)
    tails = sum(histogram["counts"][edge:]) + sum(histogram["counts"][:other_edge]) + histogram["below"] + histogram["above"]
    # A cell of exactly minus the threshold is flagged, yet sits in the bin above the line. That's rare, so allow a few.
    assert abs(tails - histogram["flagged_cells"]) <= 5


def test_tc084_each_channels_flagged_cells_match_its_strip_in_the_grid():
    channels = json.loads((SITES / "mayon" / "channels.geojson").read_text(encoding="utf-8"))["features"]
    areas = {(row["channel_id"], row["pair_id"]): row for row in read_data(SITES / "mayon" / "channel_areas.json")}
    for folder in sorted((SITES / "mayon" / "pairs").iterdir()):
        pair, layer, grid = grid_of(folder)
        rows = {row["channel_id"]: row for row in read_data(folder / "channel_histogram.json")["channels"]}
        assert set(rows) == {channel["properties"]["id"] for channel in channels}
        for channel in channels:
            row = rows[channel["properties"]["id"]]
            inside = strip_cells(channel["properties"]["strip_geometry"], layer)
            assert row["flagged_cells"] == np.count_nonzero(np.isin(grid[inside], (1, 2)))
            assert row["total_cells"] * cell_area_km2(layer) == pytest.approx(areas[(channel["properties"]["id"], pair["id"])]["checked_area_km2"], rel=0.01)


def test_panama_has_no_channel_histogram():
    assert not list((SITES / "panama" / "pairs").glob("*/channel_histogram.json"))


def test_channel_histogram_carries_its_license():
    folder = next((SITES / "mayon" / "pairs").iterdir())
    assert "ODbL" in json.loads((folder / "channel_histogram.json").read_text(encoding="utf-8"))["meta"]["license"]


def test_published_data_passes_with_the_new_files():
    assert check_data_dir(REPO / "site" / "data") == []

"""Tests for the optional false-alarm filters. They must do nothing unless turned on."""
import json

import numpy as np
import pytest

from mrw.classify import HIGH, LOW, NONE
from mrw.config import SITES_FOLDER, SiteConfigError, load_site, load_site_config
from mrw.filters import FILTERS_OFF, FilterConfigError, apply_filters, check_filters, keep_high_only, keep_persistent, remove_small_clusters
from mrw.gcov import MASKED_BY_PRODUCT, SEA

CELL_M2 = 400


def grid():
    """A patch of 4 cells, one single cell, sea and a masked slope."""
    return np.array([
        [LOW, LOW, NONE, NONE, SEA],
        [HIGH, LOW, NONE, NONE, SEA],
        [NONE, NONE, NONE, NONE, MASKED_BY_PRODUCT],
        [NONE, NONE, NONE, LOW, NONE],
    ], dtype="uint8")


@pytest.mark.parametrize("filters", [None, {}, FILTERS_OFF])
def test_all_off_changes_nothing(filters):
    assert np.array_equal(apply_filters(grid(), filters, CELL_M2), grid())


def test_mayon_uses_only_the_owner_chosen_10_km_reach():
    assert load_site("mayon")["filters"] == {**FILTERS_OFF, "max_distance_km": 10}


def test_the_web_app_knows_the_same_reach_as_the_config():
    text = (SITES_FOLDER.parents[1] / "site" / "js" / "map.js").read_text(encoding="utf-8")
    assert "DETECTION_REACH_KM = { mayon: 10 }" in text


def test_reach_clears_far_detections_and_keeps_codes():
    distance = np.full(grid().shape, 5.0)
    distance[:, 0] = 11.0
    result = apply_filters(grid(), {"max_distance_km": 10}, CELL_M2, distance_km=distance)
    assert result[0, 0] == NONE and result[1, 0] == NONE
    assert result[0, 1] == LOW
    assert result[0, 4] == SEA


def test_reach_stops_without_distances():
    with pytest.raises(FilterConfigError, match="distance"):
        apply_filters(grid(), {"max_distance_km": 10}, CELL_M2)


def test_small_clusters_go_and_no_data_codes_stay():
    result = remove_small_clusters(grid(), 2 * CELL_M2, CELL_M2)
    assert result[3, 3] == NONE
    assert np.array_equal(result[:2, :2], grid()[:2, :2])
    assert result[0, 4] == SEA and result[2, 4] == MASKED_BY_PRODUCT


def test_a_patch_exactly_at_the_limit_stays():
    assert remove_small_clusters(grid(), 4 * CELL_M2, CELL_M2)[0, 0] == LOW


def test_corner_touching_cells_are_one_patch():
    classes = np.array([[LOW, NONE], [NONE, LOW]], dtype="uint8")
    assert np.array_equal(remove_small_clusters(classes, 2 * CELL_M2, CELL_M2), classes)


def test_empty_grid_is_fine():
    classes = np.zeros((3, 3), dtype="uint8")
    assert np.array_equal(remove_small_clusters(classes, 100, CELL_M2), classes)


def test_high_only_clears_low_and_keeps_codes():
    result = keep_high_only(grid())
    assert result[1, 0] == HIGH
    assert np.count_nonzero(result == LOW) == 0
    assert result[0, 4] == SEA


def test_persistence_keeps_only_cells_flagged_again():
    later = np.zeros_like(grid())
    later[0, 0] = HIGH
    result = keep_persistent(grid(), later)
    assert result[0, 0] == LOW
    assert result[0, 1] == NONE and result[1, 0] == NONE
    assert result[0, 4] == SEA


def test_persistence_stops_without_the_next_pair():
    with pytest.raises(FilterConfigError, match="next pair"):
        apply_filters(grid(), {"persist_across_pairs": True}, CELL_M2)


def test_persistence_stops_on_different_sizes():
    with pytest.raises(FilterConfigError, match="same size"):
        keep_persistent(grid(), np.zeros((2, 2), dtype="uint8"))


@pytest.mark.parametrize("filters", [{"max_distance_km": 0}, {"max_distance_km": "far"}, {"min_cluster_m2": 0}, {"min_cluster_m2": True}, {"high_confidence_only": "yes"},
                                     {"persist_across_pairs": 1}, {"mystery": 1}])
def test_bad_settings_stop(filters):
    with pytest.raises(FilterConfigError):
        check_filters(filters)


def test_bad_filter_in_a_site_config_stops_loading(tmp_path):
    config = json.loads((SITES_FOLDER / "mayon.json").read_text(encoding="utf-8"))
    config["filters"]["min_cluster_m2"] = -5
    path = tmp_path / "site.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(SiteConfigError, match="min_cluster_m2"):
        load_site_config(path)

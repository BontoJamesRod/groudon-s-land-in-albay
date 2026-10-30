"""Tests for the gcov module on small test arrays (T-014, TC-027)."""
import numpy as np
from pyproj import Transformer
from shapely.geometry import box

from mrw.gcov import (HAS_VALUE, MASKED_BY_PRODUCT, OUTSIDE_COVERAGE, SEA, brightness_change, land_mask,
                      no_data_reasons, process_gcov, speckle_filter, to_db)

EPSG = 32651


def utm_axes(rows=40, columns=40):
    x0, y0 = Transformer.from_crs(4326, EPSG, always_xy=True).transform(123.6, 13.3)
    return x0 + np.arange(columns) * 10.0, y0 - np.arange(rows) * 10.0


def test_tc027_change_is_plus_10_db():
    before, after = to_db(np.array([0.01])), to_db(np.array([0.1]))
    assert np.isclose(brightness_change(before, after)[0], 10.0)


def test_tc027_nan_and_zero_become_no_data_never_infinity():
    decibels = to_db(np.array([0.0, np.nan, -1.0, 1.0]))
    assert np.isnan(decibels[:3]).all()
    assert decibels[3] == 0.0
    assert not np.isinf(decibels).any()


def test_speckle_filter_averages_5_by_5():
    power = np.zeros((9, 9)) + 1.0
    power[4, 4] = 26.0
    filtered = speckle_filter(power)
    assert np.isclose(filtered[4, 4], 2.0)  # (24 x 1 + 26) / 25
    assert np.isclose(filtered[0, 0], 1.0)


def test_speckle_filter_ignores_missing_neighbours_and_keeps_them_missing():
    power = np.full((9, 9), 4.0)
    power[4, 4] = np.nan
    filtered = speckle_filter(power)
    assert np.isnan(filtered[4, 4])
    assert np.isclose(filtered[4, 5], 4.0)


def test_each_no_data_reason_and_their_order():
    change = np.array([[1.0, np.nan, 1.0, 1.0, np.nan]])
    before_mask = np.array([[1, 1, 0, 255, 255]], dtype="uint8")
    after_mask = np.array([[1, 1, 1, 1, 255]], dtype="uint8")
    land = np.array([[True, True, True, True, False]])
    reasons = no_data_reasons(before_mask, after_mask, change, land)
    assert reasons.tolist() == [[HAS_VALUE, MASKED_BY_PRODUCT, MASKED_BY_PRODUCT, OUTSIDE_COVERAGE, SEA]]


def test_land_mask_finds_the_land_half():
    x_values, y_values = utm_axes()
    to_lonlat = Transformer.from_crs(EPSG, 4326, always_xy=True)
    west, north = to_lonlat.transform(x_values[0] - 500, y_values[0] + 500)
    middle, south = to_lonlat.transform(x_values[20], y_values[-1] - 500)
    mask = land_mask(box(west, south, middle, north), x_values, y_values, EPSG)
    assert mask[:, :18].all()
    assert not mask[:, 23:].any()


def test_process_gcov_runs_end_to_end_and_keeps_the_math():
    x_values, y_values = utm_axes()
    shape = (len(y_values), len(x_values))
    before = {"HHHH": np.full(shape, 0.01, dtype="float32"), "mask": np.ones(shape, dtype="uint8"),
              "x": x_values, "y": y_values, "epsg": np.array(EPSG)}
    after = {**before, "HHHH": np.full(shape, 0.1, dtype="float32")}
    result = process_gcov(before, after, box(123, 13, 124, 14))
    assert np.allclose(result["change_db"], 10.0)
    assert (result["reasons"] == HAS_VALUE).all()
    assert result["spacing_x_m"] == 10.0

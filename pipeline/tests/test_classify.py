"""Tests for the classify module (T-017, TC-022, TC-023)."""
import numpy as np

from mrw.classify import HIGH, LOW, NONE, areas_km2, classify
from mrw.gcov import HAS_VALUE, MASKED_BY_PRODUCT, OUTSIDE_COVERAGE, SEA

# These test values aren't the project's thresholds: they only exercise the rules.
BRIGHTNESS = 3.0
LOSS = 0.3


def run(change, loss, reasons=None):
    change = np.array([change], dtype="float64")
    loss = None if loss is None else np.array([loss], dtype="float64")
    reasons = np.zeros(change.shape, dtype="uint8") if reasons is None else np.array([reasons], dtype="uint8")
    return classify(change, loss, reasons, BRIGHTNESS, LOSS)[0].tolist()


def test_both_signals_give_high():
    assert run([4.0], [0.5]) == [HIGH]


def test_tc022_only_one_signal_gives_low_never_high():
    assert run([4.0, 0.5], [0.1, 0.5]) == [LOW, LOW]


def test_neither_signal_gives_none():
    assert run([1.0], [0.1]) == [NONE]


def test_a_brightness_drop_counts_like_a_rise():
    assert run([-4.0], [0.5]) == [HIGH]


def test_exactly_on_the_threshold_passes():
    assert run([3.0], [0.3]) == [HIGH]


def test_tc023_no_coherence_means_no_high_class():
    classes = run([4.0, 1.0], None)
    assert classes == [LOW, NONE]
    grid = np.array([classes], dtype="uint8")
    assert areas_km2(grid, 10, 10)["high_confidence_area_km2"] == 0


def test_missing_coherence_at_one_pixel_still_allows_low():
    assert run([4.0], [np.nan]) == [LOW]


def test_no_data_codes_are_kept_even_when_values_would_pass():
    codes = [HAS_VALUE, MASKED_BY_PRODUCT, SEA, OUTSIDE_COVERAGE]
    assert run([4.0, 4.0, 4.0, np.nan], [0.5, 0.5, 0.5, 0.5], codes) == [HIGH, MASKED_BY_PRODUCT, SEA, OUTSIDE_COVERAGE]


def test_nan_change_never_passes():
    assert run([np.nan], [0.1]) == [NONE]


def test_areas_add_up():
    grid = np.array([[HIGH] * 300 + [LOW] * 700 + [NONE, SEA]], dtype="uint8")
    areas = areas_km2(grid, 10, 10)
    assert areas["high_confidence_area_km2"] == 0.03
    assert areas["low_confidence_area_km2"] == 0.07
    assert areas["new_material_area_km2"] == 0.1

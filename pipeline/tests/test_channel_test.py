"""Tests for the night 4 channel test's fixed rules. Everything here is made-up numbers."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reports"))

from channel_test import count_at_least, decide, fraction, ratio, refuse_download


def test_five_of_nine_at_2_is_go():
    assert decide([2.0] * 5 + [1.0] * 4, [0.0] * 9, True) == "GO"


def test_four_quarry_pairs_with_five_channel_pairs_is_weak():
    assert decide([2.0] * 4 + [1.0] * 5, [1.5] * 5 + [1.0] * 4, True) == "WEAK"


def test_neither_is_no_go():
    assert decide([1.9] * 9, [1.4] * 9, True) == "NO-GO"


def test_no_quarries_is_not_tested_even_with_strong_channels():
    assert decide([], [3.0] * 9, False) == "NOT TESTED"


def test_flagged_fraction_ignores_pixels_with_no_value():
    flagged = np.array([True, False, False, True])
    area = np.array([True, True, True, False])
    has_value = np.array([True, True, False, True])
    assert fraction(flagged, area, has_value) == 0.5


def test_zero_quiet_flags_count_as_passing_but_zero_over_zero_does_not():
    assert ratio(0.1, 0.0) == float("inf")
    assert ratio(0.0, 0.0) is None
    assert count_at_least([float("inf"), None, 1.0], 2.0) == 1


def test_a_missing_crop_stops_rather_than_downloads():
    with pytest.raises(RuntimeError, match="nothing may be downloaded"):
        refuse_download("any url", "any folder")

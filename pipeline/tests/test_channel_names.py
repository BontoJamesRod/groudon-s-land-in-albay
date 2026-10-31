"""Tests for the channel-name matching rules. The small network here is made up."""
import sys
from pathlib import Path

from shapely.geometry import LineString, box

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reports"))

from channel_names import confidence, cut_at_town, follow_downhill


def test_a_name_tag_that_reaches_the_town_is_high():
    assert confidence(True, None, 1.5, True, []) == "high"


def test_medium_needs_every_condition():
    assert confidence(False, 300, 3.0, True, []) == "medium"
    assert confidence(False, 500, 3.0, True, []) == "low"
    assert confidence(False, 300, 6.0, True, []) == "low"
    assert confidence(False, 300, 3.0, False, []) == "low"
    assert confidence(False, 300, 3.0, True, ["Bonga"]) == "low"


def test_following_joins_segments_and_enters_a_river_partway():
    segments = {1: [(0, 0), (1, 0)], 2: [(5, 5), (1, 0), (2, 0)], 3: [(2, 0), (3, 0)]}
    ids, points = follow_downhill(1, segments)
    assert ids == [1, 2, 3]
    assert points == [(0, 0), (1, 0), (2, 0), (3, 0)]


def test_line_is_cut_at_the_last_point_inside_the_town():
    line, reached = cut_at_town(LineString([(0, 0), (10, 0)]), box(2, -1, 6, 1))
    assert reached and line.length == 6
    _, reached = cut_at_town(LineString([(0, 0), (10, 0)]), box(20, 20, 30, 30))
    assert not reached

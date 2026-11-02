"""Tests for the second try at channel names: one line per name, each on its own evidence, nothing published."""
import json
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "pipeline" / "reports"))

from channel_names_v2 import CHANNELS, build_rows, follow_with_choices, read_places, split_at_joins

CONTEXT = REPO / "pipeline" / "context"
GEOJSON = CONTEXT / "channel_name_candidates_v2.geojson"
KML = CONTEXT / "channel_name_candidates_v2.kml"
ASKED_FOR = ["Bonga", "Mabinit", "Matanag", "Buyuan", "Masarawag", "Maninila", "Anoling", "Bulawan", "Buang", "San Vicente",
             "Quirangay", "Tumpa", "Upper Nasisi", "Upper Nabonton"]


def saved_features():
    return json.loads(GEOJSON.read_text(encoding="utf-8"))["features"]


@pytest.fixture(scope="module")
def rows():
    return build_rows()


def by_name(rows):
    return {row["channel"]: row for row in rows if row["role"] == "name"}


def test_following_takes_the_chosen_fork():
    segments = {1: [(0, 0), (1, 0)], 2: [(1, 0), (2, 1)], 3: [(1, 0), (2, -1)], 4: [(2, -1), (3, -1)]}
    assert follow_with_choices(1, segments) == [(0, 0), (1, 0), (2, 1)]
    assert follow_with_choices(1, segments, [3]) == [(0, 0), (1, 0), (2, -1), (3, -1)]


def test_a_chosen_segment_must_be_downhill_of_the_top():
    with pytest.raises(ValueError):
        follow_with_choices(1, {1: [(0, 0), (1, 0)], 2: [(5, 5), (6, 6)]}, [2])


def test_two_lines_stop_where_they_join():
    paths = {"A": [(0, 0), (1, 0), (2, 0), (3, 0)], "B": [(0, 5), (1, 3), (2, 0), (3, 0)]}
    split = split_at_joins(paths, {})
    assert split["A"] == ([(0, 0), (1, 0), (2, 0)], ["B"])
    assert split["B"] == ([(0, 5), (1, 3), (2, 0)], ["A"])


def test_a_line_stops_where_it_joins_a_confirmed_line():
    split = split_at_joins({"A": [(0, 0), (1, 0), (2, 0)]}, {"Confirmed": [(5, 5), (1, 0), (9, 9)]})
    assert split["A"] == ([(0, 0), (1, 0)], ["Confirmed"])


def test_lines_that_share_only_their_top_do_not_count_as_joined():
    split = split_at_joins({"A": [(0, 0), (1, 0)], "B": [(0, 0), (0, 1)]}, {})
    assert split["A"][1] == [] and split["B"][1] == []


def test_every_name_has_one_line():
    names = [f["properties"]["channel"] for f in saved_features() if f["properties"]["role"] == "name"]
    assert len(names) == len(set(names))
    assert set(ASKED_FOR) <= set(names)


def test_no_name_uses_another_places_evidence():
    places = read_places()
    used = [item["place"] for item in CHANNELS if item["place"]]
    assert len(used) == len(set(used))
    for item in CHANNELS:
        if item["place"]:
            place = places[item["place"]]
            own_words = {place["name"], *(place["alt_name"] or "").split(";")}
            assert item["name"].replace("Upper ", "") in own_words or item["name"] == "Bonga"
    assert places[next(i["place"] for i in CHANNELS if i["name"] == "Buyuan")]["name"] == "Buyoan"


def test_shared_names_no_longer_share_a_line(rows):
    named = by_name(rows)
    for first, second in (("Bonga", "Mabinit"), ("Masarawag", "Maninila")):
        assert named[first]["line"].intersection(named[second]["line"].buffer(5)).length < 100


def test_the_rivers_below_the_joins_belong_to_neither_name(rows):
    lowers = [row for row in rows if row["role"] != "name"]
    assert all(row["confidence"] == "not a candidate" for row in lowers)
    titles = " ".join(row["channel"] for row in lowers)
    assert "Pawa-Burabod River" in titles and "San Francisco River" in titles


def test_a_name_with_a_doubt_cannot_be_medium(rows):
    for row in by_name(rows).values():
        if row["closer_place"] or row["tied_branch"]:
            assert row["confidence"] == "low"


def test_every_line_gives_its_evidence():
    for feature in saved_features():
        words = " ".join(feature["properties"]["evidence"])
        for part in ("OSM name tag", "Nearest barangay of any name", "Town reached", "OSM ways", "Name comes from"):
            assert part in words
        if feature["properties"]["role"] == "name":
            assert "Flank" in words and "Shared segment" in words


def test_the_kml_says_colours_are_confidence_not_hazard():
    text = KML.read_text(encoding="utf-8")
    root = ElementTree.fromstring(text)
    tag = "{http://www.opengis.net/kml/2.2}"
    folders = [folder.find(f"{tag}name").text for folder in root.iter(f"{tag}Folder")]
    assert folders[0] == "LEGEND: colours are match confidence, NOT hazard level"
    assert len(list(root.iter(f"{tag}Placemark"))) == len(saved_features())
    # Green, yellow and red would read as safe and dangerous.
    assert not {"ff00c800", "ff00d7ff", "ff0000ff"} & {color.text for color in root.iter(f"{tag}color")}


def test_the_candidates_are_not_published():
    data = REPO / "site" / "data"
    assert not list(data.rglob("channel_name_candidates*"))
    published = json.loads((data / "sites" / "mayon" / "channels.geojson").read_text(encoding="utf-8"))["features"]
    assert sorted(f["properties"]["name"] for f in published) == ["Basud", "Lidong", "Mi-isi", "Padang"]


def test_saved_files_match_a_fresh_build(rows):
    saved = {f["properties"]["channel"]: f["properties"]["confidence"] for f in saved_features()}
    assert saved == {row["channel"]: row["confidence"] for row in rows}

"""Tests for search and pairs using fake search results (T-012, TC-025, TC-026)."""
import pytest

from mrw.config import load_site
from mrw.pairs import (MIXED_PASSES_MESSAGE, PairError, build_track_pairs, check_same_track, find_gunw,
                       pair_id, pass_id, require_product)
from mrw.search import (BlindnessError, is_before_cutoff, parse_gcov, parse_gunw, require_before_cutoff,
                        search_gcov, search_gunw)

GCOV_1 = "NISAR_L2_PR_GCOV_032_111_A_008_4005_DHDH_A_20261007T211319_20261007T211354_P05023_N_F_J_001"
GCOV_2 = "NISAR_L2_PR_GCOV_033_111_A_008_4005_DHDH_A_20261019T211319_20261019T211354_P05023_N_F_J_001"
GCOV_ERUPTION = "NISAR_L2_PR_GCOV_034_111_A_008_4005_DHDH_A_20261031T211319_20261031T211354_P05023_N_F_J_001"
GCOV_OTHER = "NISAR_L2_PR_GCOV_033_104_D_082_4005_DHDH_A_20261019T100000_20261019T100035_P05023_N_F_J_001"
GUNW_SAFE = ("NISAR_L2_PR_GUNW_032_111_A_008_033_4000_SH_20261007T211319_20261007T211354_"
             "20261019T211319_20261019T211354_P05023_N_F_J_001")
# Its first date is safe, its second date is after the eruption: it must be refused.
GUNW_ERUPTION = ("NISAR_L2_PR_GUNW_033_111_A_008_034_4000_SH_20261019T211319_20261019T211354_"
                 "20261031T211319_20261031T211354_P05023_N_F_J_001")


class FakeResult:
    def __init__(self, name):
        self.properties = {"sceneName": name, "url": f"https://example.org/{name}.h5"}


def fake_searcher(*names):
    """Stand in for ASF, returning these product names and remembering the request."""
    def search(**options):
        search.options = options
        return [FakeResult(name) for name in names]
    return search


def test_gcov_name_is_parsed():
    parsed = parse_gcov(GCOV_1)
    assert (parsed["track"], parsed["frame"], parsed["orbit_direction"], parsed["cycle"]) == (111, 8, "ascending", 32)
    assert parsed["acquired_start"] == "2026-10-07T21:13:19Z"
    assert parsed["acquired_end"] == "2026-10-07T21:13:54Z"


def test_gunw_name_is_parsed():
    parsed = parse_gunw(GUNW_SAFE)
    assert parsed["before_acquired_start"] == "2026-10-07T21:13:19Z"
    assert parsed["after_acquired_start"] == "2026-10-19T21:13:19Z"


def test_blind_check_looks_at_every_date():
    assert is_before_cutoff(GUNW_SAFE)
    assert not is_before_cutoff(GUNW_ERUPTION)
    assert not is_before_cutoff(GCOV_ERUPTION)
    assert not is_before_cutoff("no dates in this name")
    with pytest.raises(BlindnessError):
        require_before_cutoff(GUNW_ERUPTION)


def test_search_drops_eruption_products_and_limits_the_request():
    searcher = fake_searcher(GCOV_2, GCOV_ERUPTION, GCOV_1)
    passes = search_gcov(load_site("mayon"), "2026-06-17", searcher=searcher)
    assert [p["granule_id"] for p in passes] == [GCOV_1, GCOV_2]
    assert searcher.options["end"].strftime("%Y-%m-%d") == "2026-10-29"


def test_gunw_search_drops_a_product_whose_second_date_is_after_the_cutoff():
    products = search_gunw(load_site("mayon"), "2026-06-17", searcher=fake_searcher(GUNW_SAFE, GUNW_ERUPTION))
    assert [p["granule_id"] for p in products] == [GUNW_SAFE]


def test_mixed_tracks_stop_with_the_exact_message():
    with pytest.raises(PairError) as caught:
        check_same_track(parse_gcov(GCOV_1), parse_gcov(GCOV_OTHER))
    assert str(caught.value) == "Passes are not from the same track, frame and direction"
    assert str(caught.value) == MIXED_PASSES_MESSAGE
    with pytest.raises(PairError):
        pair_id("mayon", parse_gcov(GCOV_1), parse_gcov(GCOV_OTHER))


def test_missing_product_stops_with_the_exact_message():
    with pytest.raises(PairError) as caught:
        require_product("FAKE_GRANULE", {GCOV_1})
    assert str(caught.value) == "Product not available yet: FAKE_GRANULE"


def test_ids_follow_docs_05():
    assert pass_id(parse_gcov(GCOV_1)) == "A111F008_20261007T211319"
    assert pair_id("mayon", parse_gcov(GCOV_1), parse_gcov(GCOV_2)) == "mayon_A111F008_20261007_20261019"


def test_consecutive_pairs_never_mix_tracks_and_link_the_previous_pair():
    third = GCOV_2.replace("20261019", "20261029").replace("_033_111", "_034_111")
    passes = [parse_gcov(name) for name in (GCOV_1, GCOV_OTHER, GCOV_2, third)]
    pairs = build_track_pairs("mayon", passes)
    assert [p["id"] for p in pairs] == ["mayon_A111F008_20261007_20261019", "mayon_A111F008_20261019_20261029"]
    assert pairs[0]["previous"] is None
    assert pairs[1]["previous"] is pairs[0]


def test_gunw_is_matched_to_exactly_its_two_passes():
    before, after = parse_gcov(GCOV_1), parse_gcov(GCOV_2)
    gunw = parse_gunw(GUNW_SAFE)
    assert find_gunw(before, after, [gunw]) is gunw
    assert find_gunw(after, before, [gunw]) is None
    assert find_gunw(before, parse_gcov(GCOV_OTHER), [gunw]) is None

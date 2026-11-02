"""TC-098: the owner's rule for holding a pair (docs/04, ADR-014). Grids and numbers here are made up."""
import json

import numpy as np
import pytest

from mrw.classify import HIGH, LOW
from mrw.gcov import MASKED_BY_PRODUCT, OUTSIDE_COVERAGE, SEA
from mrw.hold_check import (BASELINE_PATH, LARGE_GAP_SHARE, cached_crop, gap_days, hold_reasons, limits_from, look_closer_reasons,
                            outer_flagged_km2, refuse_download, track_agreement, volcano_no_data_share, where_change_is)
from mrw.search import BlindnessError

OLD_GRANULE = "NISAR_L2_PR_GCOV_033_111_A_008_4005_DHDH_A_20261019T211319_20261019T211354_P05023_N_F_J_001"
GOOD = {"before": "PROVISIONAL", "after": "PROVISIONAL", "gunw": "PROVISIONAL", "previous": "PROVISIONAL"}
BASELINE = {"far_median_coherence_change_low": -0.2, "far_median_coherence_change_high": 0.1,
            "outer_flagged_km2_high": 3.0, "outer_km": 8}


def measured(**changes):
    return {"pair_id": "a_pair", "granules": list(GOOD), "total_km2": 1.0, "far_median_coherence_change": 0.0,
            "outer_flagged_km2": 1.0, "volcano_no_data_share": 0.0, **changes}


def test_tc098_an_ordinary_pair_has_nothing_to_hold_or_look_at():
    assert hold_reasons(measured(), GOOD) == []
    assert look_closer_reasons(measured(), BASELINE) == []


def test_tc098_a_large_area_alone_does_nothing():
    big = measured(total_km2=500.0)
    assert hold_reasons(big, GOOD) == []
    assert look_closer_reasons(big, BASELINE) == []


@pytest.mark.parametrize("maturity", ["BETA", "OTHER (URGENT_RESPONSE)"])
def test_tc098_reason_a_a_product_below_provisional_holds(maturity):
    reasons = hold_reasons(measured(), {**GOOD, "gunw": maturity})
    assert len(reasons) == 1 and reasons[0].startswith("(a)") and maturity in reasons[0]


def test_tc098_reason_a_a_validated_product_is_fine():
    assert hold_reasons(measured(), {**GOOD, "after": "VALIDATED"}) == []


def test_tc098_reason_a_a_product_missing_from_asf_holds():
    missing = {key: value for key, value in GOOD.items() if key != "before"}
    assert hold_reasons(measured(), missing)[0].startswith("(a)")


@pytest.mark.parametrize("median", [-0.21, 0.11])
def test_tc098_check_b_only_says_to_look_closer(median):
    far = measured(far_median_coherence_change=median)
    assert hold_reasons(far, GOOD) == []
    reasons = look_closer_reasons(far, BASELINE)
    assert len(reasons) == 1 and reasons[0].startswith("(b)")


@pytest.mark.parametrize("median", [-0.2, 0.1, None])
def test_tc098_check_b_the_ends_of_the_range_and_no_coherence_pass(median):
    assert look_closer_reasons(measured(far_median_coherence_change=median), BASELINE) == []


def test_tc098_check_c_only_says_to_look_closer():
    far = measured(outer_flagged_km2=3.1)
    assert hold_reasons(far, GOOD) == []
    reasons = look_closer_reasons(far, BASELINE)
    assert len(reasons) == 1 and reasons[0].startswith("(c)")
    assert look_closer_reasons(measured(outer_flagged_km2=3.0), BASELINE) == []


def test_tc098_reason_d_large_gaps_over_the_volcano_hold():
    assert hold_reasons(measured(volcano_no_data_share=LARGE_GAP_SHARE), GOOD) == []
    reasons = hold_reasons(measured(volcano_no_data_share=LARGE_GAP_SHARE + 0.01), GOOD)
    assert len(reasons) == 1 and reasons[0].startswith("(d)")


def test_tc098_the_longer_gap_doesnt_set_the_limit_for_check_c():
    row = {"far_median_coherence_change": 0.0, "volcano_no_data_share": 0.0}
    limits = limits_from([{**row, "gap_days": 12, "outer_flagged_km2": 1.5}, {**row, "gap_days": 24, "outer_flagged_km2": 3.5}])
    assert limits["outer_flagged_km2_high"] == 1.5
    assert limits["usual_gap_pairs"] == 1


def test_tc098_pairs_without_coherence_dont_set_the_range_for_check_b():
    row = {"gap_days": 12, "outer_flagged_km2": 1.0, "volcano_no_data_share": 0.0}
    limits = limits_from([{**row, "far_median_coherence_change": -0.1}, {**row, "far_median_coherence_change": None},
                          {**row, "far_median_coherence_change": 0.2}])
    assert (limits["far_median_coherence_change_low"], limits["far_median_coherence_change_high"]) == (-0.1, 0.2)
    assert limits["pairs_with_coherence"] == 2


def test_tc098_gap_in_days():
    assert gap_days({"before_acquired_start": "2026-07-27T21:13:21Z", "after_acquired_start": "2026-08-20T21:13:19Z"}) == 24


def test_tc098_outer_area_counts_only_flagged_cells_past_the_distance():
    cells = np.array([[LOW, HIGH, 0, LOW]], dtype="uint8")
    distance = np.array([[1.0, 9.0, 9.0, 8.5]])
    assert outer_flagged_km2(cells, distance, 0.5) == 1.0


def test_tc098_where_change_is_compares_with_change_spread_evenly():
    cells = np.array([[LOW, HIGH, 0, 0, LOW, 0, SEA, 0]], dtype="uint8")
    distance = np.array([[1.0, 2.0, 3.0, 7.0, 9.0, 9.5, 2.0, 12.0]])
    channels = np.array([[True, False, False, False, False, False, False, False]])
    where = where_change_is(cells, distance, 6, 10, channels)
    assert where["flagged"] == pytest.approx({"near": 2 / 3, "far": 1 / 3, "channels": 1 / 3})
    # Six cells of checked ground inside the reach: the sea and the cell past 10 km don't count.
    assert where["even"] == pytest.approx({"near": 3 / 6, "far": 2 / 6, "channels": 1 / 6})


def test_tc098_where_change_is_with_nothing_flagged():
    cells = np.zeros((1, 2), dtype="uint8")
    where = where_change_is(cells, np.array([[1.0, 9.0]]), 6, 10, np.zeros((1, 2), dtype=bool))
    assert where["flagged"] == {"near": None, "far": None, "channels": None}


def test_tc098_no_data_share_leaves_out_the_sea_and_the_far_ground():
    cells = np.array([[0, MASKED_BY_PRODUCT, OUTSIDE_COVERAGE, SEA, MASKED_BY_PRODUCT]], dtype="uint8")
    distance = np.array([[1.0, 2.0, 3.0, 4.0, 9.0]])
    assert volcano_no_data_share(cells, distance, 6) == pytest.approx(2 / 3)


def test_tc098_no_data_share_with_no_land_at_all():
    assert volcano_no_data_share(np.array([[SEA]], dtype="uint8"), np.array([[1.0]]), 6) == 0.0


def test_tc098_agreement_on_the_same_cells_and_nearby():
    first = np.zeros((20, 20), dtype="uint8")
    second = np.zeros((20, 20), dtype="uint8")
    first[1, 1] = LOW     # both flag this block of 10 x 10 cells, on different cells
    second[2, 2] = HIGH
    first[15, 15] = LOW   # only one track flags this block
    assert track_agreement(first, second) == {"same_cell": 0.0, "within_about_200_m": 0.5}
    assert track_agreement(first, first)["same_cell"] == 1.0


def test_tc098_nothing_flagged_by_either_track_is_said_plainly():
    empty = np.zeros((20, 20), dtype="uint8")
    assert track_agreement(empty, empty) == {"same_cell": None, "within_about_200_m": None}


def test_a_product_after_the_cutoff_is_refused_too(tmp_path):
    with pytest.raises(BlindnessError):
        cached_crop(OLD_GRANULE.replace("20261019", "20261112"), "https://example.invalid/a.h5", "/group", ("data",), (1, 2, 3, 4), raw_folder=tmp_path)


def test_the_check_never_downloads(tmp_path):
    with pytest.raises(FileNotFoundError, match="doesn't download"):
        refuse_download("https://example.invalid/a.h5")
    with pytest.raises(FileNotFoundError, match="doesn't download"):
        cached_crop(OLD_GRANULE, "https://example.invalid/a.h5", "/group", ("data",), (1, 2, 3, 4), raw_folder=tmp_path)


def test_the_saved_baseline_covers_the_published_pairs_before_the_eruption():
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    assert baseline["pair_count"] == len(baseline["pairs"]) == 11
    assert baseline["usual_gap_pairs"] == 10
    assert baseline["far_median_coherence_change_low"] < baseline["far_median_coherence_change_high"]
    assert max(row["after"] for row in baseline["pairs"]) < "2026-10-30"

"""TC-098: the owner's rule for holding a pair (docs/04, ADR-014). Grids and numbers here are made up."""
import json
from pathlib import Path

import numpy as np
import pytest

from mrw.classify import HIGH, LOW
from mrw.gcov import MASKED_BY_PRODUCT, OUTSIDE_COVERAGE, SEA
from mrw.search import BlindnessError
from mrw.hold_check import (BASELINE_PATH, LARGE_GAP_SHARE, cached_crop, hold_reasons, outer_flagged_km2, refuse_download,
                            track_agreement, volcano_no_data_share)

OLD_GRANULE = "NISAR_L2_PR_GCOV_033_111_A_008_4005_DHDH_A_20261019T211319_20261019T211354_P05023_N_F_J_001"
GOOD = {"before": "PROVISIONAL", "after": "PROVISIONAL", "gunw": "PROVISIONAL", "previous": "PROVISIONAL"}
BASELINE = {"median_coherence_change_low": -0.2, "median_coherence_change_high": 0.1,
            "outer_flagged_km2_high": 3.0, "outer_km": 8}


def measured(**changes):
    return {"pair_id": "a_pair", "granules": list(GOOD), "total_km2": 1.0, "median_coherence_change": 0.0,
            "outer_flagged_km2": 1.0, "volcano_no_data_share": 0.0, **changes}


def test_tc098_an_ordinary_pair_has_no_reason_to_hold():
    assert hold_reasons(measured(), GOOD, BASELINE) == []


def test_tc098_a_large_area_alone_is_not_a_reason_to_hold():
    assert hold_reasons(measured(total_km2=500.0), GOOD, BASELINE) == []


@pytest.mark.parametrize("maturity", ["BETA", "OTHER (URGENT_RESPONSE)"])
def test_tc098_reason_a_a_product_below_provisional(maturity):
    reasons = hold_reasons(measured(), {**GOOD, "gunw": maturity}, BASELINE)
    assert len(reasons) == 1 and reasons[0].startswith("(a)") and maturity in reasons[0]


def test_tc098_reason_a_a_validated_product_is_fine():
    assert hold_reasons(measured(), {**GOOD, "after": "VALIDATED"}, BASELINE) == []


def test_tc098_reason_a_a_product_missing_from_asf():
    missing = {key: value for key, value in GOOD.items() if key != "before"}
    assert hold_reasons(measured(), missing, BASELINE)[0].startswith("(a)")


@pytest.mark.parametrize("median", [-0.21, 0.11])
def test_tc098_reason_b_either_side_of_the_range(median):
    reasons = hold_reasons(measured(median_coherence_change=median), GOOD, BASELINE)
    assert len(reasons) == 1 and reasons[0].startswith("(b)")


@pytest.mark.parametrize("median", [-0.2, 0.1, None])
def test_tc098_reason_b_the_ends_of_the_range_and_no_coherence_pass(median):
    assert hold_reasons(measured(median_coherence_change=median), GOOD, BASELINE) == []


def test_tc098_reason_c_too_much_flagged_far_from_the_summit():
    reasons = hold_reasons(measured(outer_flagged_km2=3.1), GOOD, BASELINE)
    assert len(reasons) == 1 and reasons[0].startswith("(c)")
    assert hold_reasons(measured(outer_flagged_km2=3.0), GOOD, BASELINE) == []


def test_tc098_reason_d_large_gaps_over_the_volcano():
    assert hold_reasons(measured(volcano_no_data_share=LARGE_GAP_SHARE), GOOD, BASELINE) == []
    reasons = hold_reasons(measured(volcano_no_data_share=LARGE_GAP_SHARE + 0.01), GOOD, BASELINE)
    assert len(reasons) == 1 and reasons[0].startswith("(d)")


def test_tc098_every_reason_is_named():
    reasons = hold_reasons(measured(median_coherence_change=1.0, outer_flagged_km2=9.0, volcano_no_data_share=0.9),
                           {**GOOD, "after": "BETA"}, BASELINE)
    assert [reason[:3] for reason in reasons] == ["(a)", "(b)", "(c)", "(d)"]


def test_tc098_outer_area_counts_only_flagged_cells_past_the_distance():
    cells = np.array([[LOW, HIGH, 0, LOW]], dtype="uint8")
    distance = np.array([[1.0, 9.0, 9.0, 8.5]])
    assert outer_flagged_km2(cells, distance, 0.5) == 1.0


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
    assert baseline["median_coherence_change_low"] < baseline["median_coherence_change_high"]
    assert max(row["after"] for row in baseline["pairs"]) < "2026-10-30"
    assert Path(BASELINE_PATH).parts[-2] == "reports"

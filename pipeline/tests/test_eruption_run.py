"""Tests for the eruption script. Every pass here is a made-up dictionary, and nothing is searched."""
from datetime import datetime, timezone

import pytest

from mrw import eruption_run
from mrw.config import load_site
from mrw.eruption_run import NotReady, eruption_pairs, has_coherence, process, require_owner_go_ahead
from mrw.search import list_all_maturities, search_gcov

CUTOFF_NOW = datetime(2026, 10, 30, tzinfo=timezone.utc)
LIFTED = datetime(2026, 11, 1, tzinfo=timezone.utc)


def one_pass(date, track=104):
    return {"track": track, "acquired_start": f"{date}T10:16:00Z", "granule_id": f"G_{track}_{date}"}


def make_pair(first, second, track=104, gunw=True, previous=None):
    return {"id": f"{track}_{first}_{second}", "before": one_pass(first, track), "after": one_pass(second, track),
            "gunw": {"granule_id": "fake"} if gunw else None, "previous": previous}


def config_with_status(status):
    config = load_site("mayon")
    config["thresholds"] = {**config["thresholds"], "status": status}
    return config


def final_config():
    return config_with_status("FINAL")


def test_provisional_thresholds_stop_it():
    with pytest.raises(NotReady, match="PROVISIONAL"):
        require_owner_go_ahead(config_with_status("PROVISIONAL"), LIFTED)


def test_a_cutoff_that_is_not_lifted_stops_it():
    with pytest.raises(NotReady, match="BLIND_CUTOFF"):
        require_owner_go_ahead(final_config(), CUTOFF_NOW)


def test_final_thresholds_and_a_lifted_cutoff_pass():
    require_owner_go_ahead(final_config(), LIFTED)


def test_the_command_stops_before_any_search(monkeypatch, capsys):
    def no_search(*args, **kwargs):
        raise AssertionError("searched before the owner's go-ahead")
    monkeypatch.setattr(eruption_run, "search_gcov", no_search)
    monkeypatch.setattr(eruption_run, "search_gunw", no_search)
    monkeypatch.setattr(eruption_run, "load_site", lambda site_id: config_with_status("PROVISIONAL"))
    assert eruption_run.main(["check"]) == 1
    assert "PROVISIONAL" in capsys.readouterr().out


def test_only_watched_tracks_after_the_eruption_are_kept():
    wanted = make_pair("2026-10-19", "2026-10-31")
    pairs = [make_pair("2026-10-07", "2026-10-19"), wanted, make_pair("2026-10-26", "2026-11-07", track=39)]
    assert eruption_pairs(pairs) == [wanted]


def test_coherence_needs_both_gunws_and_equal_gaps():
    baseline = make_pair("2026-10-07", "2026-10-19")
    assert has_coherence(make_pair("2026-10-19", "2026-10-31", previous=baseline))
    assert not has_coherence(make_pair("2026-10-19", "2026-10-31", gunw=False, previous=baseline))
    assert not has_coherence(make_pair("2026-10-19", "2026-10-31", previous=make_pair("2026-10-07", "2026-10-19", gunw=False)))
    assert not has_coherence(make_pair("2026-10-19", "2026-11-12", previous=baseline))


def test_a_pair_without_coherence_is_skipped(capsys):
    def no_run(*args):
        raise AssertionError("processed a pair without coherence")
    assert process([make_pair("2026-10-19", "2026-10-31")], final_config(), runner=no_run) == []
    assert "Skipped" in capsys.readouterr().out


class FakeResult:
    def __init__(self, name, collection):
        self.properties = {"sceneName": name, "collectionName": collection, "url": None}


def fake_search(**options):
    """Answer like ASF, including a product past the cutoff, which must never come through."""
    if options["processingLevel"] == "GCOV":
        return [FakeResult("NISAR_L2_PR_GCOV_033_111_A_008_4005_DHDH_A_20261019T211319_20261019T211354_P05023_N_F_J_001", "NISAR_PROVISIONAL_V1"),
                FakeResult("NISAR_L2_UR_GCOV_034_111_A_008_4005_DHDH_A_20261031T211319_20261031T211354_P05023_N_F_J_001", "NISAR_UR"),
                FakeResult("NISAR_L2_UR_GCOV_035_111_A_008_4005_DHDH_A_20261112T211319_20261112T211354_P05023_N_F_J_001", "NISAR_UR"),
                FakeResult("NISAR_L2_PR_GCOV_033_222_A_008_4005_DHDH_A_20261019T211319_20261019T211354_P05023_N_F_J_001", "NISAR_PROVISIONAL_V1")]
    return []


def test_check_all_lists_urgent_response_and_stays_before_the_cutoff(capsys):
    rows = list_all_maturities(load_site("mayon"), "2026-06-01", eruption_run.MAYON_TRACKS, searcher=fake_search)
    assert sorted((row["maturity"], row["acquired"][:10]) for row in rows) == [("PROVISIONAL", "2026-10-19"), ("URGENT RESPONSE", "2026-10-31")]
    eruption_run.check_all(rows)
    output = capsys.readouterr().out
    assert "Track 111 frame 8 GCOV URGENT RESPONSE: 1, newest 2026-10-31T21:13:19Z" in output
    assert "20261112" not in output


def test_the_pipelines_own_search_still_leaves_out_urgent_response():
    names = [one["granule_id"] for one in search_gcov(load_site("mayon"), "2026-06-01", searcher=fake_search)]
    assert not any("_UR_" in name for name in names)


def test_check_all_stops_before_any_search_without_the_go_ahead(monkeypatch):
    def no_search(*args, **kwargs):
        raise AssertionError("searched before the owner's go-ahead")
    monkeypatch.setattr(eruption_run, "list_all_maturities", no_search)
    monkeypatch.setattr(eruption_run, "load_site", lambda site_id: config_with_status("PROVISIONAL"))
    assert eruption_run.main(["check-all"]) == 1


def test_check_prints_the_newest_pass_for_each_track_and_frame(capsys):
    passes = [{"track": 111, "frame": 8, "acquired_start": "2026-10-07T21:13:19Z"},
              {"track": 111, "frame": 8, "acquired_start": "2026-10-19T21:13:19Z"},
              {"track": 104, "frame": 82, "acquired_start": "2026-10-19T10:16:00Z"},
              {"track": 104, "frame": 81, "acquired_start": "2026-09-25T10:16:00Z"}]
    eruption_run.check([], passes)
    output = capsys.readouterr().out
    assert "Track 104 frame 81: 2026-09-25T10:16:00Z" in output
    assert "Track 104 frame 82: 2026-10-19T10:16:00Z" in output
    assert "Track 111 frame 8: 2026-10-19T21:13:19Z" in output
    assert "2026-10-07" not in output
    assert "Track 104: no new pass on ASF yet" in output

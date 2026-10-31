"""Tests for the site config (T-008, TC-036)."""
import json

import pytest

from mrw.config import SiteConfigError, build_sites_row, load_site, load_site_config, thresholds_are_provisional
from mrw.contract_check import SITES, check_row


def write_config(tmp_path, **changes):
    """Save a copy of the Mayon config with some values changed."""
    config = load_site("mayon")
    config.update(changes)
    path = tmp_path / "test_site.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_mayon_config_gives_a_valid_sites_row():
    row = build_sites_row(load_site("mayon"), now="2026-10-31T00:00:00Z")
    errors = []
    check_row(row, SITES, "row", errors)
    assert errors == []
    assert set(row) == set(SITES)
    assert (row["default_zoom"], row["min_zoom"], row["max_zoom"]) == (12, 10, 16)


def test_pipeline_only_settings_are_not_published():
    row = build_sites_row(load_site("mayon"))
    assert "thresholds" not in row and "tracks" not in row and "provisional_fields" not in row


def test_thresholds_and_zooms_are_marked_provisional():
    config = load_site("mayon")
    assert {"default_zoom", "min_zoom", "max_zoom"} <= set(config["provisional_fields"])
    # The two places that say whether the thresholds are final must agree.
    assert thresholds_are_provisional(config) == ("thresholds" in config["provisional_fields"])


@pytest.mark.parametrize("changes", [
    {"bounds_west": 123.81, "bounds_east": 123.56},
    {"bounds_south": 13.38, "bounds_north": 13.14},
    {"bounds_west": 123.56, "bounds_east": 123.56},
])
def test_reversed_bounds_give_the_exact_message(tmp_path, changes):
    path = write_config(tmp_path, **changes)
    with pytest.raises(SiteConfigError) as caught:
        load_site_config(path)
    assert str(caught.value) == f"Invalid bounds in site config: {path}"


@pytest.mark.parametrize("changes", [
    {"default_zoom": 30},
    {"default_zoom": 5},
    {"status": "live"},
    {"id": "Not Valid"},
    {"thresholds": {"status": "PROVISIONAL", "brightness_threshold_db": -1, "coherence_loss_threshold": 0.3}},
    {"thresholds": {"status": "PROVISIONAL", "brightness_threshold_db": 3, "coherence_loss_threshold": 2}},
    {"thresholds": None},
    {"thresholds": {"brightness_threshold_db": 3, "coherence_loss_threshold": 0.3}},
    {"unexpected": 1},
])
def test_other_bad_values_stop(tmp_path, changes):
    with pytest.raises(SiteConfigError):
        load_site_config(write_config(tmp_path, **changes))


def test_unreadable_file_stops(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{oops", encoding="utf-8")
    with pytest.raises(SiteConfigError):
        load_site_config(path)


def test_mayon_has_a_strip_width_and_a_movement_mask():
    config = load_site("mayon")
    assert config["channel_strip_half_width_m"] > 0
    assert 0 <= config["ground_movement"]["min_coherence"] <= 1


@pytest.mark.parametrize("setting, match", [
    ({"channel_strip_half_width_m": 0}, "channel_strip_half_width_m"),
    ({"ground_movement": {"min_coherence": 2}}, "ground_movement"),
    ({"ground_movement": 1}, "ground_movement"),
])
def test_bad_strip_or_mask_settings_stop(tmp_path, setting, match):
    path = tmp_path / "test_site.json"
    path.write_text(json.dumps({**load_site("mayon"), **setting}), encoding="utf-8")
    with pytest.raises(SiteConfigError, match=match):
        load_site_config(path)

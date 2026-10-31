"""Tests for the optional "brightness leads" rule. The default rule keeps its own tests in test_classify.py."""
import json

import numpy as np
import pytest

from mrw.classify import BRIGHTNESS_LEADS, EITHER_SIGNAL, HIGH, LOW, NONE, classify
from mrw.config import SiteConfigError, load_site, load_site_config
from mrw.gcov import SEA

# Made-up values that only exercise the rules. They aren't proposed thresholds.
BRIGHTNESS = 7.0
LOSS = 0.6


def run(change, loss, reasons=None, **options):
    change = np.array([change], dtype="float64")
    loss = None if loss is None else np.array([loss], dtype="float64")
    reasons = np.zeros(change.shape, dtype="uint8") if reasons is None else np.array([reasons], dtype="uint8")
    return classify(change, loss, reasons, BRIGHTNESS, LOSS, **options)[0].tolist()


def test_both_signals_give_high():
    assert run([8.0], [0.7], rule=BRIGHTNESS_LEADS) == [HIGH]


def test_brightness_alone_gives_low():
    assert run([8.0, -8.0], [0.1, 0.1], rule=BRIGHTNESS_LEADS) == [LOW, LOW]


def test_coherence_alone_adds_no_area():
    assert run([1.0], [0.9], rule=BRIGHTNESS_LEADS) == [NONE]


def test_no_coherence_data_still_flags_brightness_as_low():
    assert run([8.0, 1.0], None, rule=BRIGHTNESS_LEADS) == [LOW, NONE]


def test_no_data_codes_stay():
    assert run([8.0], [0.7], reasons=[SEA], rule=BRIGHTNESS_LEADS) == [SEA]


def test_the_rule_only_removes_cells_that_had_coherence_alone():
    rng = np.random.default_rng(1)
    change, loss = rng.uniform(-10, 10, 500), rng.uniform(0, 1, 500)
    reasons = np.zeros(500, dtype="uint8")
    default = classify(change, loss, reasons, BRIGHTNESS, LOSS)
    leads = classify(change, loss, reasons, BRIGHTNESS, LOSS, rule=BRIGHTNESS_LEADS)
    coherence_alone = (np.abs(change) < BRIGHTNESS) & (loss >= LOSS)
    assert (leads[coherence_alone] == NONE).all()
    assert (leads[~coherence_alone] == default[~coherence_alone]).all()


def test_default_is_the_rule_used_today():
    assert run([1.0], [0.9]) == [LOW]
    assert run([1.0], [0.9], rule=EITHER_SIGNAL) == [LOW]


def test_unknown_rule_stops():
    with pytest.raises(ValueError):
        run([1.0], [0.9], rule="something_else")


def test_mayon_uses_the_owners_rule():
    assert load_site("mayon")["thresholds"]["rule"] == BRIGHTNESS_LEADS


def test_bad_rule_in_a_config_stops(tmp_path):
    config = load_site("mayon")
    config["thresholds"]["rule"] = "something_else"
    path = tmp_path / "test_site.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(SiteConfigError, match="thresholds.rule"):
        load_site_config(path)

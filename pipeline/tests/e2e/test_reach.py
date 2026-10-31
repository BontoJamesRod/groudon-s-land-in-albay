"""The 10 km limit must be visible, and must never read as "nothing is there"."""
import pytest
from playwright.sync_api import expect

from .conftest import read_data
from .test_mvp import card, tap_at

pytestmark = pytest.mark.e2e

OAS = (13.3186, 123.57845)  # about 13.5 km from the summit, on land


def test_legend_says_how_far_the_map_looks(app):
    expect(app.locator("#legend-title")).to_contain_text("within 10 km of the summit")
    expect(app.locator("#legend-title")).to_contain_text("PROVISIONAL")


def test_the_limit_is_drawn_on_the_map(app):
    expect(app.locator('.leaflet-overlay-pane path[stroke-dasharray="2 6"]')).to_have_count(1)


def test_a_far_tap_says_not_checked_instead_of_nothing_found(app):
    tap_at(app, *OAS)
    expect(card(app)).to_contain_text("Oas")
    expect(card(app)).to_contain_text("Not checked: this map only looks within 10 km of the summit")
    expect(card(app)).not_to_contain_text("No new material detected")


def test_a_near_tap_still_gets_a_result(app):
    tap_at(app, 13.2572 - 5 / 111.0, 123.6856)
    expect(card(app)).to_contain_text("Confidence:")
    expect(card(app)).not_to_contain_text("Not checked")


def test_help_explains_the_limit(app):
    app.click("#help-button")
    expect(app.locator("#help-panel")).to_contain_text("within 10 km of the summit")


def test_every_published_pair_carries_the_limit():
    for row in read_data("sites/mayon/pairs.json"):
        pair = read_data(f"sites/mayon/pairs/{row['id']}/pair.json")
        title = next(layer["title"] for layer in pair["layers"] if layer["kind"] == "new_material")
        assert "within 10 km" in title

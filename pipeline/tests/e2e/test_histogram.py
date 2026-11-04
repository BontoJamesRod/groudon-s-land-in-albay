"""TC-085 to TC-087: the brightness histogram in the panel (F-21)."""
import json

import pytest
from playwright.sync_api import expect

from .conftest import ROOT, open_drawer_if_closed, prepare_page, read_data, wait_until_ready
from .test_accessibility import problems_on

pytestmark = pytest.mark.e2e

CHART = "#histogram-chart svg"


def config_threshold(site_id="mayon"):
    config = json.loads((ROOT / "pipeline" / "sites" / f"{site_id}.json").read_text(encoding="utf-8"))
    return config["thresholds"]["brightness_threshold_db"]


def line_position(page, side):
    """Where a flag line is drawn, as the dB value that spot on the chart stands for."""
    return page.evaluate("""(side) => {
      const line = document.querySelector(`.histogram-line[data-db="${side}"]`);
      const width = document.querySelector('.histogram-chart').viewBox.baseVal.width;
      return (Number(line.getAttribute('x1')) / width) * 20 - 10;
    }""", side)


def test_tc085_the_lines_sit_at_the_configs_threshold(app):
    expect(app.locator(CHART)).to_be_visible()
    threshold = config_threshold()
    assert line_position(app, threshold) == pytest.approx(threshold)
    assert line_position(app, -threshold) == pytest.approx(-threshold)
    expect(app.locator(".histogram-line")).to_have_count(2)


def test_tc085_only_the_tails_past_the_line_are_shaded(app):
    expect(app.locator(CHART)).to_be_visible()
    threshold = config_threshold()
    far_enough = app.evaluate("""(threshold) => {
      const width = document.querySelector('.histogram-chart').viewBox.baseVal.width;
      const db = (x) => (x / width) * 20 - 10;
      return [...document.querySelectorAll('.histogram-flagged')].every((bar) => {
        const x = Number(bar.getAttribute('x'));
        return db(x) >= threshold - 0.001 || db(x) + 0.25 <= -threshold + 0.001;
      });
    }""", threshold)
    assert far_enough
    assert app.locator(".histogram-flagged").count() > 0
    assert app.evaluate("getComputedStyle(document.querySelector('.histogram-flagged')).fill") == "rgb(230, 159, 0)"


def test_tc085_the_sentence_gives_the_share_from_the_data(app):
    pair_id = read_data("sites/mayon/pairs.json")[-1]["id"]
    share = read_data(f"sites/mayon/pairs/{pair_id}/histogram.json")["flagged_share"]
    expect(app.locator("#histogram-sentence")).to_have_text(
        f"Most of the ground barely changed. The shaded edges changed by more than the line, so they're flagged: {share * 100:.1f}% of the checked land.")
    expect(app.locator("#histogram-note")).to_contain_text("within 10 km of the summit")
    assert "decibels" in app.locator(CHART).get_attribute("aria-label")


def test_tc085_the_chart_follows_the_selected_pass(app):
    expect(app.locator(CHART)).to_be_visible()
    before = app.locator("#histogram-sentence").inner_text()
    # The pair with the most different area, so that its sentence can't round to the same percentage.
    pairs = read_data("sites/mayon/pairs.json")
    other = max(pairs, key=lambda pair: abs(pair["new_material_area_km2"] - pairs[-1]["new_material_area_km2"]))
    app.select_option("#pair-list", other["id"])
    expect(app.locator("#histogram-sentence")).not_to_have_text(before)


def test_tc085_axe_passes_with_the_chart(app):
    expect(app.locator(CHART)).to_be_visible()
    assert problems_on(app) == []


def test_tc085_a_phone_shows_it_in_the_open_drawer(page, site_url):
    prepare_page(page, width=360, height=740)
    page.goto(site_url)
    wait_until_ready(page)
    expect(page.locator(".histogram")).to_be_hidden()
    open_drawer_if_closed(page)
    page.locator(CHART).scroll_into_view_if_needed()
    expect(page.locator(CHART)).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert problems_on(page) == []


def test_tc086_without_the_file_the_pair_still_shows(page, site_url):
    prepare_page(page)
    page.route("**/histogram.json", lambda route: route.fulfill(status=404))
    page.goto(site_url)
    wait_until_ready(page)
    expect(page.locator("#histogram-sentence")).to_have_text("Brightness chart not available for this pair")
    expect(page.locator(CHART)).to_have_count(0)
    expect(page.locator(".leaflet-radar-pane img")).to_have_count(1)
    expect(page.locator("#compare-button")).to_be_enabled()


def test_tc086_nothing_moves_the_line_and_the_help_says_why(app):
    expect(app.locator(CHART)).to_be_visible()
    expect(app.locator('input[type="range"]')).to_have_count(0)
    expect(app.locator('.histogram input, .histogram button:not(.info-button), .histogram select')).to_have_count(0)
    app.click("#help-button")
    expect(app.locator("#help-panel")).to_contain_text("The flag line can't be moved here.")
    expect(app.locator("#help-panel")).to_contain_text("before the eruption data was opened")


def test_tc087_an_open_channel_adds_its_outline_and_closing_removes_it(app):
    expect(app.locator(CHART)).to_be_visible()
    expect(app.locator(".histogram-outline")).to_have_count(0)
    app.click("#channels-button")
    app.locator("#channel-body .channel-row", has_text="Mi-isi").click()
    expect(app.locator(".histogram-outline")).to_have_count(1)
    expect(app.locator("#histogram-note")).to_contain_text("the Mi-isi strip")
    app.click("#channel-back")
    expect(app.locator(".histogram-outline")).to_have_count(0)
    expect(app.locator("#histogram-note")).not_to_contain_text("strip")


def test_tc087_a_missing_channel_file_leaves_the_chart_without_an_outline(page, site_url):
    prepare_page(page)
    page.route("**/channel_histogram.json", lambda route: route.fulfill(status=404))
    page.goto(site_url)
    wait_until_ready(page)
    expect(page.locator(CHART)).to_be_visible()
    page.click("#channels-button")
    page.locator("#channel-body .channel-row", has_text="Mi-isi").click()
    expect(page.locator(CHART)).to_be_visible()
    expect(page.locator(".histogram-outline")).to_have_count(0)


def test_panama_has_a_chart_and_no_outline_and_its_help_is_its_own(page, site_url):
    prepare_page(page)
    page.goto(site_url)
    wait_until_ready(page)
    page.click("#site-name")
    page.click("#picker-panel button:has-text('Azuero Peninsula')")
    expect(page.locator("#site-name")).to_have_text("Azuero Peninsula, Panama")
    expect(page.locator(CHART)).to_be_visible()
    expect(page.locator("#histogram-note")).to_contain_text("Land in this site.")
    page.click("#help-button")
    expect(page.locator("#help-panel")).to_contain_text("The flag line can't be moved here.")
    expect(page.locator("#help-panel")).not_to_contain_text("eruption data")

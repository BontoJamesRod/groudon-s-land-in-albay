"""TC-106 to TC-109: the calm design (F-24). Each test name carries its TC number."""
import re

import pytest
from playwright.sync_api import expect

from .conftest import latest_pair, open_channel, prepare_page, read_data, wait_until_ready
from .test_accessibility import problems_on
from .test_mvp import controls_too_small

pytestmark = pytest.mark.e2e

LATEST = latest_pair()


def open_at(page, site_url, width, height):
    prepare_page(page, width=width, height=height)
    page.goto(site_url)
    wait_until_ready(page)


def latest_record():
    return read_data(f"sites/mayon/pairs/{LATEST['id']}/pair.json")


def test_tc106_the_top_bar_has_the_name_the_site_chip_search_the_disclaimer_pill_and_help(app):
    expect(app.locator(".brand-name")).to_have_text("Mayon Radar Watch")
    expect(app.locator("#site-name")).to_have_text("Mayon Volcano, Albay")
    expect(app.locator("#search-button")).to_have_text("Find a town")
    expect(app.locator("#help-button")).to_have_attribute("aria-label", "What am I looking at?")
    expect(app.locator("#help-button")).to_have_text("?")
    pill = app.locator(".disclaimer-tag").evaluate("(tag) => [getComputedStyle(tag).backgroundColor, getComputedStyle(tag).color]")
    assert pill == ["rgb(253, 243, 228)", "rgb(122, 69, 16)"]
    app.click("#search-button")
    expect(app.locator("#search-panel")).to_be_visible()


def test_tc106_a_layer_switch_works_by_keyboard_with_a_visible_focus_ring(app):
    switch = app.locator("#layer-toggle")
    expect(switch).to_have_attribute("role", "switch")
    expect(app.locator(".radar-marks")).to_have_count(1)
    switch.focus()
    app.keyboard.press("Space")
    expect(switch).not_to_be_checked()
    expect(app.locator(".radar-marks")).to_have_count(0)
    assert switch.evaluate("(node) => getComputedStyle(node).outlineStyle") != "none"
    app.keyboard.press("Space")
    expect(switch).to_be_checked()


@pytest.mark.parametrize("width,height", [(1280, 800), (360, 740)])
def test_tc106_axe_passes_and_phone_targets_are_44_px(page, site_url, width, height):
    open_at(page, site_url, width, height)
    if width <= 700:
        assert controls_too_small(page) == []
    assert problems_on(page) == []


def test_tc107_the_desktop_column_has_four_cards_in_order(app):
    titles = app.locator(".side .section-title:visible, #channel-title").all_text_contents()
    assert titles == ["This pass", "Layers", "Channels since the last pass", "Brightness change"]
    expect(app.locator("#channels-button")).to_have_count(0)


def test_tc107_the_pass_card_reads_its_numbers_from_the_pair_record(app):
    pair = latest_record()
    expect(app.locator("#legend-area")).to_have_text(f"{pair['new_material_area_km2']:.2f} km²")
    widths = app.locator("#confidence-bar > span").evaluate_all("(parts) => parts.map((part) => parseFloat(part.style.width))")
    total = pair["high_confidence_area_km2"] + pair["low_confidence_area_km2"]
    assert widths == pytest.approx([pair["high_confidence_area_km2"] / total * 100, pair["low_confidence_area_km2"] / total * 100])
    expect(app.locator("#pair-sub")).to_contain_text(f"Track {pair['track']}")


def test_tc107_layers_have_switches_and_the_ring_has_none(app):
    expect(app.locator("#channel-count")).to_have_text("4 checked by eye")
    zone = app.locator("#zone-row")
    expect(zone).to_contain_text("Permanent Danger Zone (6 km)")
    expect(zone).to_contain_text("Always shown")
    expect(zone.locator("input")).to_have_count(0)


def test_tc107_a_row_opens_the_channel_page_in_the_column(app):
    open_channel(app, "Mi-isi")
    box = app.locator("#channel-panel").bounding_box()
    assert box["x"] >= app.locator("#map").bounding_box()["x"] + app.locator("#map").bounding_box()["width"]
    expect(app.locator("#layer-toggle")).to_be_hidden()


def test_tc107_panama_has_no_channel_card_and_says_changed(app):
    app.click("#site-name")
    app.click("#picker-panel button:has-text('Azuero Peninsula')")
    expect(app.locator("#pair-list")).to_have_value(re.compile("^panama_"))
    expect(app.locator("#channel-panel")).to_be_hidden()
    expect(app.locator("#zone-row")).to_be_hidden()
    expect(app.locator("#area-caption")).to_have_text("changed")
    expect(app.locator("#disclaimer-short")).to_have_text("Not an official warning · Follow SINAPROC")


@pytest.mark.parametrize("width,height", [(390, 844), (360, 740)])
def test_tc108_the_closed_sheet_shows_the_key_numbers_and_3_channels(page, site_url, width, height):
    open_at(page, site_url, width, height)
    assert page.locator("#map").bounding_box()["height"] >= 0.45 * height - 1
    for part in ("#pair-label", "#legend-area", "#confidence-bar"):
        expect(page.locator(part)).to_be_in_viewport()
    expect(page.locator("#channel-body .channel-row:visible")).to_have_count(3)
    expect(page.locator("#show-all")).to_have_text("Show all 4 channels and layers")
    expect(page.locator(".layers-card")).to_be_hidden()
    assert controls_too_small(page) == []


def test_tc108_the_open_sheet_shows_everything(page, site_url):
    open_at(page, site_url, 390, 844)
    page.click("#show-all")
    for part in (".layers-card", "#histogram-chart", "#compare-button", ".sheet-links"):
        expect(page.locator(part)).to_be_visible()
    expect(page.locator("#channel-body .channel-row:visible")).to_have_count(4)
    page.locator(".sheet-links button", has_text="Data sources").click()
    expect(page.locator("#sources-panel")).to_be_visible()


def test_tc108_folded_credits_sit_behind_a_credits_button_and_eox_stays(page, site_url):
    open_at(page, site_url, 390, 844)
    page.mouse.click(195, 200)  # a tap on the map folds the credits
    label = page.locator(".credits-label")
    expect(label).to_be_visible()
    expect(label).to_have_text("Credits")
    expect(page.locator(".credits-folded")).to_be_hidden()
    page.click('.basemap-button:has-text("Satellite")')
    expect(page.locator(".credits-short")).to_contain_text("EOxCloudless")
    expect(page.locator(".credits-short")).to_be_visible()


def test_tc109_the_channel_page_has_its_pass_card_chart_list_and_sources(app):
    open_channel(app, "Mi-isi")
    pairs = read_data("sites/mayon/pairs.json")
    area = next(row["flagged_area_km2"] for row in read_data("sites/mayon/channel_areas.json")
                if row["channel_id"] == "mayon_miisi" and row["pair_id"] == LATEST["id"])
    expect(app.locator("#channel-back")).to_have_text("All channels")
    expect(app.locator(".channel-pass-number")).to_have_text(f"{area:.3f} km²")
    expect(app.locator(".channel-col")).to_have_count(len(pairs))
    expect(app.locator(".channel-col-selected")).to_have_attribute("data-pair", LATEST["id"])
    expect(app.locator(".channel-section-title").first).to_contain_text("Every pass since June")
    expect(app.locator(".channel-not-checked")).to_contain_text("more than 10 km from the summit")
    source = app.locator(".channel-source")
    expect(source).to_contain_text("PHIVOLCS")
    expect(source.locator("a", has_text="OpenStreetMap")).to_have_attribute("href", "https://www.openstreetmap.org/copyright")


def test_tc109_the_selected_bar_and_row_follow_the_pass(app):
    open_channel(app, "Mi-isi")
    app.click("#channel-previous")
    before = read_data("sites/mayon/pairs.json")[-2]["id"]
    expect(app.locator(".channel-col-selected")).to_have_attribute("data-pair", before)
    expect(app.locator('.channel-bar[aria-current="true"]')).to_have_attribute("data-pair", before)
    expect(app.locator(".channel-pass-title")).to_contain_text(f"Track {read_data('sites/mayon/pairs.json')[-2]['track']}")


@pytest.mark.parametrize("width,height", [(1280, 800), (390, 844)])
def test_tc109_axe_on_the_channel_page(page, site_url, width, height):
    open_at(page, site_url, width, height)
    open_channel(page, "Mi-isi")
    if width <= 700:
        assert controls_too_small(page) == []
    assert problems_on(page) == []

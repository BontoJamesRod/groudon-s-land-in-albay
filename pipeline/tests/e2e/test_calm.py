"""TC-106 to TC-109 and TC-111 to TC-113: the calm design (F-24) and Panama as a test site. Each test name carries its TC number."""
import re

import pytest
from playwright.sync_api import expect

from .conftest import go_to_panama, open_footer_link, latest_pair, open_channel, prepare_page, read_data, wait_until_ready
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
    go_to_panama(app)
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


@pytest.mark.parametrize("width,height", [(1280, 800), (360, 740)])
def test_tc111_the_top_bar_shows_the_owners_logo_hidden_from_screen_readers(page, site_url, width, height):
    open_at(page, site_url, width, height)
    logo = page.locator(".brand-mark")
    expect(logo).to_be_visible()
    expect(logo).to_have_attribute("src", "img/mrw-logo.svg")
    expect(logo).to_have_attribute("alt", "")
    assert logo.evaluate("(img) => img.complete && img.naturalWidth > 0")
    box = logo.bounding_box()
    assert 22 <= box["width"] <= 26 and 22 <= box["height"] <= 26


def icon_links(page):
    """Return each tab-icon link as (rel, type, full address)."""
    return page.locator("link[rel*=icon]").evaluate_all("(links) => links.map((link) => [link.rel, link.type, link.href])")


@pytest.mark.parametrize("path", ["", "no/such/page"])
def test_tc111_both_pages_use_the_logo_as_the_tab_icon(page, site_url, path):
    page.goto(site_url + path)
    links = icon_links(page)
    assert [(rel, kind) for rel, kind, _ in links] == [
        ("icon", "image/svg+xml"), ("icon", "image/png"), ("apple-touch-icon", "")]
    assert [href.rsplit("/", 1)[1] for _, _, href in links] == ["mrw-logo.svg", "favicon-32.png", "apple-touch-icon.png"]
    for _, _, href in links:
        assert page.request.get(href).status == 200, href


@pytest.mark.parametrize("width,height", [(1280, 800), (360, 740)])
def test_tc112_the_site_name_is_plain_text_with_no_picker(page, site_url, width, height):
    open_at(page, site_url, width, height)
    name = page.locator("#site-name")
    expect(name).to_have_text("Mayon Volcano, Albay")
    assert name.evaluate("(node) => node.tagName") == "SPAN"
    expect(page.locator(".site-title button")).to_have_count(0)
    expect(page.locator("#picker-panel")).to_have_count(0)
    look = name.evaluate("""(node) => [getComputedStyle(node).borderTopWidth, getComputedStyle(node).backgroundColor,
                                        getComputedStyle(node, "::after").content]""")
    assert look == ["0px", "rgba(0, 0, 0, 0)", "none"]


def panama_areas():
    """The quiet pair's and the earthquake pair's areas, from Panama's records, as the panel writes them."""
    pairs = read_data("sites/panama/pairs.json")
    when = read_data("sites/panama/events.json")[0]["event_date"]
    index = next(i for i, pair in enumerate(pairs) if pair["before_acquired_start"][:10] < when <= pair["after_acquired_start"][:10])
    return f"{pairs[index - 1]['new_material_area_km2']:.2f}", f"{pairs[index]['new_material_area_km2']:.2f}"


def test_tc113_tested_in_panama_reads_its_numbers_from_panamas_records(app):
    open_footer_link(app, "#check-button")
    section = app.locator("#check-panel .tested")
    expect(section.locator("h3")).to_have_text("Tested in Panama")
    quiet, quake = panama_areas()
    expect(section).to_contain_text("same method, unchanged")
    expect(section).to_contain_text(f"More land changed after the earthquake ({quake} km²) than in the quiet pair before it ({quiet} km²).")
    expect(section).to_contain_text("at a scale of a few km")
    link = section.locator("a")
    expect(link).to_have_text("Open the Panama test map")
    expect(link).to_have_attribute("href", "?site=panama")
    expect(section.locator("p").last).to_have_text("Open the Panama test map")


@pytest.mark.parametrize("width,height", [(1280, 800), (360, 740)])
def test_tc113_panama_has_the_banner_and_keeps_its_own_wording(page, site_url, width, height):
    open_at(page, site_url, width, height)
    go_to_panama(page)
    expect(page.locator("#test-banner")).to_contain_text("Test site: Panama. It shows our method works outside Mayon.")
    expect(page.locator("#test-back")).to_have_text("← Back to Mayon")
    banner = page.locator("#test-banner").bounding_box()
    assert banner["y"] == 0 and banner["height"] <= 44  # a thin line, one 44 px row even on a phone
    expect(page.locator("#disclaimer-short")).to_have_text("Not an official warning · Follow SINAPROC")
    expect(page.locator("#area-caption")).to_have_text("changed")
    expect(page.locator(".leaflet-control-attribution")).to_contain_text("geoBoundaries")
    if width <= 700:
        assert controls_too_small(page) == []
    assert problems_on(page) == []
    open_footer_link(page, "#check-button")
    expect(page.locator("#check-panel")).to_be_visible()
    expect(page.locator("#check-panel .tested")).to_have_count(0)


def test_tc113_the_address_opens_panama_and_back_and_forward_follow_it(page, site_url):
    open_at(page, site_url + "?site=panama", 1280, 800)
    expect(page.locator("#site-name")).to_have_text("Azuero Peninsula, Panama")
    expect(page.locator("#test-banner")).to_be_visible()
    page.click("#test-back")
    expect(page).to_have_url(site_url)
    page.go_back()
    expect(page.locator("#site-name")).to_have_text("Azuero Peninsula, Panama")
    page.go_forward()
    expect(page.locator("#site-name")).to_have_text("Mayon Volcano, Albay")
    expect(page.locator("#test-banner")).to_be_hidden()


def test_tc113_an_unknown_site_in_the_address_opens_mayon(page, site_url):
    open_at(page, site_url + "?site=nowhere", 1280, 800)
    expect(page.locator("#site-name")).to_have_text("Mayon Volcano, Albay")
    expect(page.locator("#test-banner")).to_be_hidden()

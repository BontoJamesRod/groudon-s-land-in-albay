"""TC-102 to TC-105: info popovers, one line per item, the bottom bar and the map credits."""
import pytest
from playwright.sync_api import expect

from .conftest import go_to_panama, DISCLAIMER, SHORT_DISCLAIMER, open_drawer_if_closed, prepare_page, wait_until_ready
from .test_accessibility import problems_on
from .test_mvp import read_data_towns, tap_at

pytestmark = pytest.mark.e2e

LEGEND_INFO = "#legend-rows ~ .info"
AREA_INFO = ".area-line .info"
LEGAL_WORDS = ("illegal", "unpermitted", "violation")


def popover(page, holder):
    return page.locator(f"{holder} .info-popover")


def centre(page, selector):
    box = page.locator(selector).bounding_box()
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


def test_tc102_a_mouse_opens_it_after_a_pause_and_can_move_onto_it(app):
    app.mouse.move(*centre(app, f"{LEGEND_INFO} .info-button"))
    app.wait_for_timeout(100)
    expect(popover(app, LEGEND_INFO)).to_be_hidden()  # not straight away: a passing pointer doesn't open it
    expect(popover(app, LEGEND_INFO)).to_be_visible()
    expect(app.locator(f"{LEGEND_INFO} .info-button")).to_have_attribute("aria-expanded", "true")
    # Hoverable: the pointer crosses the gap onto the popover, and it stays.
    app.mouse.move(*centre(app, f"{LEGEND_INFO} .info-popover"), steps=8)
    app.wait_for_timeout(800)
    expect(popover(app, LEGEND_INFO)).to_be_visible()
    # Moving away closes it.
    app.mouse.move(5, 300, steps=5)
    expect(popover(app, LEGEND_INFO)).to_be_hidden()


def test_tc102_escape_dismisses_it_while_the_pointer_is_still_there(app):
    app.mouse.move(*centre(app, f"{LEGEND_INFO} .info-button"))
    expect(popover(app, LEGEND_INFO)).to_be_visible()
    app.keyboard.press("Escape")
    expect(popover(app, LEGEND_INFO)).to_be_hidden()
    app.wait_for_timeout(600)
    expect(popover(app, LEGEND_INFO)).to_be_hidden()


def test_tc102_a_click_keeps_it_open_until_a_click_outside(app):
    app.click(f"{AREA_INFO} .info-button")
    expect(popover(app, AREA_INFO)).to_be_visible()
    app.mouse.move(5, 300, steps=5)
    app.wait_for_timeout(800)
    expect(popover(app, AREA_INFO)).to_be_visible()  # persistent
    app.mouse.click(*centre(app, ".site-title"))
    expect(popover(app, AREA_INFO)).to_be_hidden()


def test_tc102_only_one_is_open_at_a_time(app):
    app.click(f"{AREA_INFO} .info-button")
    app.click(f"{LEGEND_INFO} .info-button")
    expect(popover(app, LEGEND_INFO)).to_be_visible()
    expect(popover(app, AREA_INFO)).to_be_hidden()


def test_tc102_touch_opens_it_with_a_tap_and_closes_it_with_a_tap_outside(browser, site_url):
    context = browser.new_context(viewport={"width": 360, "height": 740}, has_touch=True, is_mobile=True)
    page = context.new_page()
    prepare_page(page, width=360, height=740)
    page.goto(site_url)
    wait_until_ready(page)
    page.tap(".disclaimer-tag .info-button")
    tag = popover(page, ".disclaimer-tag .info")
    expect(tag).to_be_visible()
    expect(tag).to_have_text(DISCLAIMER)
    page.tap(".site-title")
    expect(tag).to_be_hidden()
    context.close()


def test_tc102_the_keyboard_opens_it_on_focus_and_with_enter_and_escape_closes_it(app):
    app.focus("#layer-toggle")
    app.keyboard.press("Tab")
    button = app.locator(f"{LEGEND_INFO} .info-button")
    expect(button).to_be_focused()
    expect(popover(app, LEGEND_INFO)).to_be_visible()
    app.keyboard.press("Escape")
    expect(popover(app, LEGEND_INFO)).to_be_hidden()
    expect(button).to_be_focused()
    app.keyboard.press("Enter")
    expect(popover(app, LEGEND_INFO)).to_be_visible()
    app.keyboard.press("Enter")
    expect(popover(app, LEGEND_INFO)).to_be_hidden()


def test_tc102_each_button_has_a_name_and_says_if_it_is_open(app):
    for button in app.locator(".info-button").all():
        assert button.get_attribute("aria-label").startswith("More about ")
        assert button.get_attribute("aria-expanded") in ("true", "false")


@pytest.mark.parametrize("holder", [LEGEND_INFO, AREA_INFO, ".pair-line .info", ".share-line .info", ".disclaimer-tag .info"])
def test_tc102_axe_passes_with_a_popover_open(app, holder):
    open_drawer_if_closed(app)
    app.click(f"{holder} .info-button")
    expect(popover(app, holder)).to_be_visible()
    assert problems_on(app) == []


def test_tc103_each_panel_shows_one_line_and_keeps_the_explanation(app):
    expect(app.locator("#pair-label")).to_have_text("Oct 8 – 20, 2026")
    expect(app.locator("#pair-sub")).to_have_text("Track 111 · morning pass, 5:13 AM")
    expect(app.locator("#pair-detail")).to_have_text("Oct 8, 2026 to Oct 20, 2026 (Asia/Manila), track 111, frame 8, ascending")
    expect(app.locator("#legend-rows li")).to_have_text(["Possible", "Likely"])
    expect(app.locator("#legend-full")).to_contain_text("Possible new material (brightness only). Confidence: low")
    expect(app.locator("#legend-area")).to_have_text("0.75 km²")
    expect(app.locator("#area-caption")).to_have_text("new material within 10 km of the summit")
    expect(app.locator("#area-courts")).to_have_text("About 1,786 basketball courts")
    area = app.locator("#legend-area-more")
    for text in ("Areas are in km².", "Total detected area: 0.75 km²", "basketball courts", "1 basketball court = 28 × 15 m"):
        expect(area).to_contain_text(text)
    expect(app.locator(".area-line .info-popover")).to_contain_text("drawn larger than life")
    expect(app.locator("#histogram-share")).to_have_text("0.2% flagged")
    expect(app.locator("#histogram-sentence")).to_contain_text("Most of the ground barely changed")
    expect(app.locator("#histogram-note")).to_contain_text("square-root scale")


def test_tc103_a_point_card_has_one_headline_and_the_rest_in_its_popover(app):
    town = next(row for row in read_data_towns() if row["name"] == "Daraga")
    tap_at(app, town["label_lat"], town["label_lon"])
    headline = app.locator("#readout-body .readout-headline .readout-title")
    expect(headline).to_have_text(__import__("re").compile(r"^Daraga: (no new material|possible new material|likely new material)$"))
    more = app.locator("#readout-body .info-popover")
    expect(more).to_contain_text("Distance to summit")
    expect(more).to_contain_text("Confidence:")
    expect(more).to_contain_text("Radar passes:")
    app.click("#readout-body .info-button")
    expect(more).to_be_visible()
    assert problems_on(app) == []


def popover_texts(page):
    return " ".join(page.locator(".info-popover").all_text_contents()).lower()


def test_tc103_no_banned_word_in_any_popover_on_either_site(app):
    open_drawer_if_closed(app)
    text = popover_texts(app)
    assert text and not [word for word in LEGAL_WORDS if word in text]
    go_to_panama(app)
    expect(app.locator("#disclaimer-short")).to_have_text("Not an official warning · Follow SINAPROC")
    expect(app.locator("#area-caption")).to_have_text("changed")
    text = popover_texts(app)
    assert not [word for word in LEGAL_WORDS if word in text]
    assert "landslide" not in text


def test_tc104_the_bottom_bar_slides_up_at_the_bottom_edge_and_back_down(app):
    height = app.viewport_size["height"]
    footer = app.locator(".footer")
    assert footer.bounding_box()["y"] > height - 10  # only a thin strip shows
    app.mouse.move(640, height - 2)
    app.wait_for_timeout(500)
    assert footer.bounding_box()["y"] < height - 40
    expect(app.locator("#sources-button")).to_be_in_viewport()
    app.mouse.move(640, 300)
    app.wait_for_timeout(900)
    assert footer.bounding_box()["y"] > height - 10


def test_tc104_keyboard_focus_brings_the_bar_up(app):
    app.focus("#sources-button")
    app.wait_for_timeout(400)
    assert app.locator(".footer").bounding_box()["y"] < app.viewport_size["height"] - 40


def test_tc104_no_sliding_for_visitors_who_ask_for_less_motion(page, site_url):
    page.emulate_media(reduced_motion="reduce")
    prepare_page(page)
    page.goto(site_url)
    wait_until_ready(page)
    assert page.evaluate("getComputedStyle(document.querySelector('.footer')).transitionDuration") in ("0s", "0s, 0s")


def test_tc104_on_a_phone_the_links_are_in_the_help_panel(page, site_url):
    prepare_page(page, width=360, height=740)
    page.goto(site_url)
    wait_until_ready(page)
    expect(page.locator(".footer")).to_be_hidden()
    page.click("#help-button")
    more = page.locator("#help-panel .help-more")
    expect(more).to_be_visible()
    more.locator("button", has_text="Data sources").click()
    expect(page.locator("#sources-panel")).to_be_visible()
    expect(page.locator("#help-panel")).to_be_hidden()


def test_tc104_on_a_desktop_the_help_panel_doesnt_repeat_them(app):
    app.click("#help-button")
    expect(app.locator("#help-panel .help-more")).to_be_hidden()


def test_tc105_the_credits_start_in_full_and_fold_after_a_move(app):
    credits = app.locator(".leaflet-control-attribution")
    expect(credits).to_contain_text("Boundaries")
    expect(credits).to_contain_text("produced using Copernicus WorldDEM-30")
    expect(app.locator(".credits-short")).to_have_count(0)
    app.mouse.move(*centre(app, "#map"))
    app.mouse.wheel(0, 200)
    short = app.locator(".credits-short")
    expect(short).to_have_text("Map data © OpenStreetMap contributors and others")
    full = credits.locator(".info-popover")
    for text in ("Boundaries", "produced using Copernicus WorldDEM-30", "OpenStreetMap contributors", "ODbL"):
        expect(full).to_contain_text(text)
    credits.locator(".info-button").click()
    expect(full).to_be_visible()


def test_tc105_the_credits_fold_after_5_seconds_on_their_own(app):
    expect(app.locator(".credits-short")).to_have_count(0)
    expect(app.locator(".credits-short")).to_have_count(1, timeout=8000)


def test_tc105_the_eox_credit_stays_in_full_on_satellite(app):
    app.click('.basemap-button:has-text("Satellite")')
    app.mouse.move(*centre(app, "#map"))
    app.mouse.wheel(0, 200)
    expect(app.locator(".credits-short")).to_contain_text("EOxCloudless")
    expect(app.locator(".credits-short")).to_contain_text("Contains modified Copernicus Sentinel data 2024")


def test_tc029_the_short_tag_is_on_screen_and_the_popover_has_the_full_line(app):
    expect(app.locator("#disclaimer-short")).to_have_text(SHORT_DISCLAIMER)
    expect(app.locator("#disclaimer-short")).to_be_in_viewport()
    expect(app.locator(".disclaimer")).to_have_text(DISCLAIMER)

"""Browser tests for the compare view: TC-018, TC-019 and the owner's snap-back bug."""
import re

import pytest
from playwright.sync_api import expect

from .conftest import latest_dates, prepare_page, wait_until_ready

pytestmark = pytest.mark.e2e

OLDER_PAIR = "mayon_A111F008_20260925_20261007"
ONE_SIGNAL_PAIR_LABEL = "Sep 26, 2026"


def divider_x(page):
    """Where the divider's line is, in pixels from the map's left edge."""
    return page.evaluate("parseFloat(document.getElementById('compare-divider').style.left)")


def clips(page):
    """The clip on each image: [before, after]."""
    return page.evaluate("[...document.querySelectorAll('.leaflet-compare-pane img')].map((image) => image.style.clipPath)")


def drag_divider(page, to_share):
    """Drag the divider with a real mouse to a share of the map's width."""
    box = page.locator("#map").bounding_box()
    middle_y = box["y"] + box["height"] / 2
    page.mouse.move(box["x"] + divider_x(page), middle_y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * to_share, middle_y, steps=8)
    page.mouse.up()


def radar_layer_is_shown(page):
    """A Leaflet pane has no size of its own, so read the setting that hides it."""
    return page.evaluate("document.querySelector('.leaflet-radar-pane').style.display !== 'none'")


def expect_compare_open(page):
    expect(page.locator("#compare-view")).to_be_visible()
    expect(page.locator("#compare-before")).to_have_text(re.compile(r"^Before: \w+ \d+, 2026$"))
    expect(page.locator("#compare-after")).to_have_text(re.compile(r"^After: \w+ \d+, 2026$"))
    expect(page.locator(".leaflet-compare-pane img")).to_have_count(2)


def test_tc018_compare_stays_open_drags_and_closes(app):
    app.click("#compare-button")
    app.wait_for_timeout(1000)
    expect_compare_open(app)
    expect(app.locator("#compare-before")).to_have_text(f"Before: {latest_dates()[0]}")
    expect(app.locator("#compare-after")).to_have_text(f"After: {latest_dates()[1]}")
    assert radar_layer_is_shown(app) is False

    box = app.locator("#map").bounding_box()
    start_clips = clips(app)
    drag_divider(app, 0.3)
    assert divider_x(app) == pytest.approx(box["width"] * 0.3, abs=2)
    left_clips = clips(app)
    assert left_clips != start_clips
    drag_divider(app, 0.7)
    assert divider_x(app) == pytest.approx(box["width"] * 0.7, abs=2)
    assert clips(app) != left_clips
    expect_compare_open(app)

    app.click("#compare-close")
    expect(app.locator("#compare-view")).to_be_hidden()
    expect(app.locator(".leaflet-compare-pane img")).to_have_count(0)
    assert radar_layer_is_shown(app) is True


def test_tc018_before_is_left_and_after_is_right(app):
    app.click("#compare-button")
    expect_compare_open(app)
    drag_divider(app, 0.4)
    images = app.evaluate("""[...document.querySelectorAll('.leaflet-compare-pane img')].map((image) => image.src)""")
    assert images[0].endswith("before_db.png") and images[1].endswith("after_db.png")
    before, after = clips(app)
    # The before image hides its right part, and the after image hides its left part.
    assert re.fullmatch(r"inset\(0px [\d.]+px 0px 0px\)", before)
    assert re.fullmatch(r"inset\(0px 0px 0px [\d.]+px\)", after)


def test_owner_bug_compare_survives_a_pair_that_is_still_loading(app, slow_files):
    """The owner's bug: when a pair finished loading, it closed a compare view opened meanwhile."""
    slow_files[f"{OLDER_PAIR}/new_material.png"] = 1.0
    app.select_option("#pair-list", OLDER_PAIR)
    app.click("#compare-button")
    expect(app.locator("#pair-label")).to_contain_text(ONE_SIGNAL_PAIR_LABEL, timeout=5000)
    app.wait_for_timeout(1000)
    expect_compare_open(app)
    expect(app.locator("#compare-before")).to_have_text("Before: Sep 26, 2026")
    expect(app.locator("#compare-after")).to_have_text("After: Oct 8, 2026")


def test_compare_follows_the_pair_when_the_pair_changes(app):
    app.click("#compare-button")
    expect_compare_open(app)
    app.select_option("#pair-list", OLDER_PAIR)
    expect(app.locator("#compare-before")).to_have_text("Before: Sep 26, 2026")
    expect_compare_open(app)
    assert radar_layer_is_shown(app) is False


def test_closed_compare_stays_closed_when_the_pair_changes(app):
    app.click("#compare-button")
    expect_compare_open(app)
    app.click("#compare-close")
    app.select_option("#pair-list", OLDER_PAIR)
    expect(app.locator("#pair-label")).to_contain_text(ONE_SIGNAL_PAIR_LABEL)
    app.wait_for_timeout(300)
    expect(app.locator("#compare-view")).to_be_hidden()


def test_compare_waits_for_the_first_pair(page, site_url, slow_files):
    """Before the first pair is ready, Compare must not claim the images are missing."""
    slow_files["new_material.png"] = 1.0
    prepare_page(page)
    page.goto(site_url)
    expect(page.locator("#compare-button")).to_be_disabled()
    expect(page.locator("#compare-message")).to_have_text("")
    wait_until_ready(page)
    expect(page.locator("#compare-button")).to_be_enabled()
    page.click("#compare-button")
    expect_compare_open(page)


def test_keyboard_moves_the_divider(app):
    app.click("#compare-button")
    expect_compare_open(app)
    start = divider_x(app)
    app.focus("#compare-divider")
    app.keyboard.press("ArrowLeft")
    assert divider_x(app) == pytest.approx(start - 20, abs=1)


@pytest.mark.parametrize("missing", ["before_db.png", "after_db.png"])
def test_tc019_missing_image_leaves_the_map_as_it_was(app, missing):
    app.route(f"**/{missing}", lambda route: route.fulfill(status=404))
    app.click("#compare-button")
    expect(app.locator("#compare-message")).to_have_text("Before/after images not available for this pair")
    expect(app.locator("#compare-view")).to_be_hidden()
    expect(app.locator(".leaflet-compare-pane img")).to_have_count(0)
    assert radar_layer_is_shown(app) is True
    expect(app.locator(".leaflet-radar-pane img")).to_have_count(1)

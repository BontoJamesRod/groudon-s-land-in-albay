"""Browser tests for the phone drawer: the map comes first, and the details slide up."""
import pytest
from playwright.sync_api import expect

from .conftest import close_list_on_a_phone, open_drawer_if_closed, prepare_page, wait_until_ready

pytestmark = pytest.mark.e2e

DISCLAIMER = "This is not an official warning. Follow PHIVOLCS and your LGU."
DEFAULT_ZOOM = 12


@pytest.fixture
def phone(page, site_url):
    prepare_page(page, width=360, height=740)
    page.goto(site_url)
    wait_until_ready(page)
    close_list_on_a_phone(page)
    return page


def height(page, selector):
    return page.locator(selector).bounding_box()["height"]


def map_size_is_current(page):
    return page.evaluate("testMap.getSize().y === testMap.getContainer().clientHeight")


def swipe(page, from_y, to_y):
    box = page.locator("#drawer-toggle").bounding_box()
    x = box["x"] + box["width"] / 2
    page.mouse.move(x, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(x, box["y"] + box["height"] / 2 + (to_y - from_y), steps=5)
    page.mouse.up()


def test_closed_on_a_phone_and_the_map_is_bigger_than_the_panel(phone):
    expect(phone.locator("#drawer-toggle")).to_have_attribute("aria-expanded", "false")
    expect(phone.locator("#legend-rows")).to_be_hidden()
    expect(phone.locator("#pair-list")).to_be_visible()
    assert height(phone, "#map") > 2 * height(phone, "#panel")
    assert map_size_is_current(phone)


def test_the_closed_drawer_says_the_results_are_provisional(phone):
    expect(phone.locator("#drawer-toggle")).to_contain_text("PROVISIONAL")
    expect(phone.locator("#drawer-toggle")).to_contain_text("within 10 km")


def test_tap_opens_and_closes(phone):
    closed_height = height(phone, "#map")
    phone.click("#drawer-toggle")
    expect(phone.locator("#drawer-toggle")).to_have_attribute("aria-expanded", "true")
    expect(phone.locator("#legend-rows")).to_be_visible()
    expect(phone.locator("#compare-button")).to_be_visible()
    assert height(phone, "#map") < closed_height
    assert map_size_is_current(phone)
    phone.click("#drawer-toggle")
    expect(phone.locator("#legend-rows")).to_be_hidden()
    assert height(phone, "#map") == closed_height
    assert map_size_is_current(phone)


def test_swipe_up_opens_and_swipe_down_closes(phone):
    swipe(phone, 0, -60)
    expect(phone.locator("#drawer-toggle")).to_have_attribute("aria-expanded", "true")
    swipe(phone, 0, 60)
    expect(phone.locator("#drawer-toggle")).to_have_attribute("aria-expanded", "false")


def test_disclaimer_stays_on_screen_either_way(phone):
    expect(phone.locator("#disclaimer-short")).to_be_in_viewport()
    phone.click("#drawer-toggle")
    expect(phone.locator(".disclaimer")).to_have_text(DISCLAIMER)
    expect(phone.locator("#disclaimer-short")).to_be_in_viewport()


def test_no_sideways_scroll_either_way(phone):
    assert phone.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    phone.click("#drawer-toggle")
    assert phone.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def test_compare_closes_the_drawer_to_give_the_map_room(phone):
    phone.click("#drawer-toggle")
    phone.click("#compare-button")
    expect(phone.locator("#compare-view")).to_be_visible()
    expect(phone.locator("#drawer-toggle")).to_have_attribute("aria-expanded", "false")
    assert map_size_is_current(phone)


def test_a_compare_error_keeps_the_drawer_open_so_it_can_be_read(phone):
    phone.route("**/before_db.png", lambda route: route.fulfill(status=404))
    phone.click("#drawer-toggle")
    phone.click("#compare-button")
    expect(phone.locator("#compare-message")).to_be_visible()
    expect(phone.locator("#compare-message")).to_have_text("Before/after images not available for this pair")


def test_latest_pass_message_shows_with_the_drawer_closed(phone):
    phone.click("#next")
    expect(phone.locator("#timeline-message")).to_have_text("This is the latest pass")
    expect(phone.locator("#timeline-message")).to_be_visible()


def test_danger_zone_label_shows_clear_of_the_credits_at_the_default_view(phone):
    label = phone.locator(".zone-label").bounding_box()
    credits = phone.locator(".leaflet-control-attribution").bounding_box()
    area = phone.locator("#map").bounding_box()
    assert label["y"] + label["height"] <= credits["y"]
    assert label["y"] >= area["y"]


def open_at(page, site_url, width, height):
    prepare_page(page, width=width, height=height)
    page.goto(site_url)
    wait_until_ready(page)


def test_tc082_a_short_phone_opens_one_zoom_step_out_with_the_label_clear(page, site_url):
    open_at(page, site_url, 360, 640)
    assert page.evaluate("testMap.getZoom()") == DEFAULT_ZOOM - 1
    center = page.evaluate("(() => { const c = testMap.getCenter(); return [c.lat, c.lng]; })()")
    assert center == pytest.approx([13.2572, 123.6856], abs=0.001)
    label = page.locator(".zone-label").bounding_box()
    credits = page.locator(".leaflet-control-attribution").bounding_box()
    assert label["y"] >= page.locator("#map").bounding_box()["y"]
    assert label["y"] + label["height"] <= credits["y"]


# Lists problems with the town names at the opening view: hidden, or with a channel label on top.
TOWN_PROBLEMS = """(() => {
  const touch = (a, b) => a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
  const shown = (label) => label.style.visibility !== 'hidden';
  const towns = [...document.querySelectorAll('.town-label')];
  const hidden = towns.filter((town) => !shown(town)).map((town) => town.textContent);
  const onTop = [...document.querySelectorAll('.channel-label')].filter(shown)
    .filter((label) => towns.some((town) => touch(town.getBoundingClientRect(), label.getBoundingClientRect())))
    .map((label) => label.textContent);
  return [...hidden, ...onTop];
})()"""
# Lists the town names that aren't whole on the map, above the credits.
TOWNS_IN_VIEW = """(() => {
  const map = document.getElementById('map').getBoundingClientRect();
  const credits = document.querySelector('.leaflet-control-attribution').getBoundingClientRect();
  return [...document.querySelectorAll('.town-label')].filter((town) => {
    const box = town.getBoundingClientRect();
    return box.left >= map.left && box.right <= map.right && box.top >= map.top && box.bottom <= credits.top;
  }).map((town) => town.textContent);
})()"""


def label_clears_the_credits(page):
    label = page.locator(".zone-label").bounding_box()
    assert label["y"] >= page.locator("#map").bounding_box()["y"]
    assert label["y"] + label["height"] <= page.locator(".leaflet-control-attribution").bounding_box()["y"]


def test_tc082_town_names_win_at_the_opening_view_on_a_short_phone(page, site_url):
    open_at(page, site_url, 360, 640)
    assert page.evaluate(TOWN_PROBLEMS) == []
    assert {"Daraga", "Legazpi City", "Camalig", "Santo Domingo"} <= set(page.evaluate(TOWNS_IN_VIEW))
    label_clears_the_credits(page)
    expect(page.locator(".zone-label")).to_have_text("Permanent Danger Zone (6 km)")


@pytest.mark.parametrize("letter_spacing", ["0", "0.6px"])
def test_tc082_the_label_clears_the_credits_on_the_smallest_phone(page, site_url, letter_spacing):
    """Extra space between letters makes any machine's font as wide as CI's."""
    page.add_init_script("addEventListener('DOMContentLoaded', () => { const style = document.createElement('style');"
                         f"style.textContent = '* {{ letter-spacing: {letter_spacing} !important; }}'; document.head.append(style); }});")
    open_at(page, site_url, 320, 568)
    label_clears_the_credits(page)
    assert page.evaluate(TOWN_PROBLEMS) == []


def test_tc082_a_desktop_keeps_the_label_below_the_ring(app):
    expect(app.locator(".zone-label-phone")).to_have_count(0)
    box = app.locator(".zone-label").bounding_box()
    assert box["y"] > app.locator("#map").bounding_box()["y"] + app.locator("#map").bounding_box()["height"] / 2


def test_tc082_a_short_desktop_keeps_the_default_zoom(page, site_url):
    open_at(page, site_url, 1280, 500)
    assert page.evaluate("testMap.getZoom()") == DEFAULT_ZOOM


def test_tc082_a_tall_phone_shows_the_whole_ring_beside_the_list(page, site_url):
    open_at(page, site_url, 390, 844)
    expect(page.locator("#channel-panel")).to_be_visible()
    label_clears_the_credits(page)
    assert page.evaluate(TOWN_PROBLEMS) == []


def test_a_short_phone_opens_on_the_map_with_the_list_one_tap_away(page, site_url):
    open_at(page, site_url, 360, 640)
    expect(page.locator("#channel-panel")).to_be_hidden()
    expect(page.locator("#pair-list")).to_be_visible()
    page.click("#channels-button")
    expect(page.locator("#channel-body .channel-row")).to_have_count(4)


def test_helper_opens_only_when_closed(phone):
    open_drawer_if_closed(phone)
    open_drawer_if_closed(phone)
    expect(phone.locator("#legend-rows")).to_be_visible()


def test_desktop_has_no_drawer(app):
    expect(app.locator("#drawer-toggle")).to_be_hidden()
    expect(app.locator("#legend-rows")).to_be_visible()
    expect(app.locator("#pair-label")).to_be_visible()
    expect(app.locator("#compare-button")).to_be_visible()

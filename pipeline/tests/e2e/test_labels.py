"""Browser tests for the map labels: the danger-zone label and the compare divider."""
import pytest
from playwright.sync_api import expect

from .conftest import open_drawer_if_closed, prepare_page, wait_until_ready

pytestmark = pytest.mark.e2e

ZOOMS = [10, 11, 12, 13, 14, 15, 16]
# Lists the town labels that are showing and that touch the danger-zone label.
OVERLAPS = """(() => {
  const zone = document.querySelector('.zone-label').getBoundingClientRect();
  return [...document.querySelectorAll('.town-label')]
    .filter((label) => label.style.visibility !== 'hidden')
    .filter((label) => {
      const box = label.getBoundingClientRect();
      return box.left < zone.right && box.right > zone.left && box.top < zone.bottom && box.bottom > zone.top;
    })
    .map((label) => label.textContent);
})()"""
LABEL_POSITIONS = """[...document.querySelectorAll('.town-label, .zone-label')].map((label) => {
  const box = label.getBoundingClientRect();
  return [label.textContent, Math.round(box.left), Math.round(box.top)];
})"""


@pytest.mark.parametrize("width", [1280, 360])
@pytest.mark.parametrize("zoom", ZOOMS)
def test_danger_zone_label_never_touches_a_town_label(page, site_url, width, zoom):
    prepare_page(page, width=width, height=800 if width == 1280 else 740)
    page.goto(site_url)
    wait_until_ready(page)
    page.evaluate(f"testMap.setView([13.2572, 123.6856], {zoom}, {{ animate: false }})")
    page.wait_for_timeout(100)
    assert page.evaluate(OVERLAPS) == []


def test_every_town_label_shows_at_the_default_zoom(app):
    """Hiding a town to make room is only for zoomed-out views (TC-001)."""
    hidden = app.evaluate("""[...document.querySelectorAll('.town-label')]
      .filter((label) => label.style.visibility === 'hidden').map((label) => label.textContent)""")
    assert hidden == []
    expect(app.locator(".zone-label")).to_be_in_viewport()


def test_opening_compare_does_not_shift_the_map(app):
    start = app.evaluate("(() => { const c = testMap.getCenter(); return [c.lat, c.lng, testMap.getSize().y]; })()")
    app.click("#compare-button")
    expect(app.locator("#compare-view")).to_be_visible()
    assert app.evaluate("(() => { const c = testMap.getCenter(); return [c.lat, c.lng, testMap.getSize().y]; })()") == start
    assert start[2] == app.evaluate("testMap.getContainer().clientHeight")


def drag_to(page, share):
    box = page.locator("#map").bounding_box()
    middle_y = box["y"] + box["height"] / 2
    x = box["x"] + float(page.evaluate("parseFloat(document.getElementById('compare-divider').style.left)"))
    page.mouse.move(x, middle_y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * share, middle_y, steps=6)
    page.mouse.up()


def test_labels_stay_still_while_the_divider_moves(app):
    start = app.evaluate(LABEL_POSITIONS)
    app.click("#compare-button")
    expect(app.locator("#compare-view")).to_be_visible()
    assert app.evaluate(LABEL_POSITIONS) == start
    for share in (0.2, 0.35, 0.5, 0.65, 0.8):
        drag_to(app, share)
        assert app.evaluate(LABEL_POSITIONS) == start


def test_the_line_follows_the_divider_and_runs_behind_the_labels(app):
    app.click("#compare-button")
    expect(app.locator(".compare-line")).to_be_visible()
    drag_to(app, 0.3)
    box = app.locator("#map").bounding_box()
    line = app.locator(".compare-line").bounding_box()
    assert line["x"] + line["width"] / 2 == pytest.approx(box["x"] + box["width"] * 0.3, abs=2)
    assert line["height"] == pytest.approx(box["height"], abs=1)
    # Line and labels share the map's layers, where a higher z-index is in front.
    line_z, label_z = app.evaluate("""[getComputedStyle(document.querySelector('.compare-line').parentElement).zIndex,
      getComputedStyle(document.querySelector('.leaflet-tooltip-pane')).zIndex].map(Number)""")
    assert line_z < label_z


def test_the_line_stays_on_the_divider_when_the_map_pans(app):
    app.click("#compare-button")
    expect(app.locator(".compare-line")).to_be_visible()
    before = app.locator(".compare-line").bounding_box()
    app.evaluate("testMap.panBy([120, 40], { animate: false })")
    after = app.locator(".compare-line").bounding_box()
    assert after["x"] == pytest.approx(before["x"], abs=1) and after["y"] == pytest.approx(before["y"], abs=1)


def test_the_line_goes_when_compare_closes(app):
    app.click("#compare-button")
    expect(app.locator(".compare-line")).to_be_visible()
    app.click("#compare-close")
    expect(app.locator(".compare-line")).to_be_hidden()


def test_labels_return_when_compare_closes(app):
    start = app.evaluate("[...document.querySelectorAll('.town-label, .zone-label')].map((label) => label.getBoundingClientRect().left)")
    app.click("#compare-button")
    expect(app.locator("#compare-view")).to_be_visible()
    app.click("#compare-close")
    assert app.evaluate("[...document.querySelectorAll('.town-label, .zone-label')].map((label) => label.getBoundingClientRect().left)") == start


def top_element_is_inside(page, selector):
    """Is this element what a tap at its center would actually reach?"""
    return page.evaluate(f"""(() => {{
      const target = document.querySelector('{selector}');
      const box = target.getBoundingClientRect();
      const top = document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
      return top === target || target.contains(top);
    }})()""")


@pytest.mark.parametrize("width, height", [(1280, 800), (360, 740)])
def test_date_labels_stay_in_front_of_the_divider(page, site_url, width, height):
    prepare_page(page, width=width, height=height)
    page.goto(site_url)
    wait_until_ready(page)
    open_drawer_if_closed(page)
    page.click("#compare-button")
    expect(page.locator("#compare-view")).to_be_visible()
    box = page.locator("#compare-before").bounding_box()
    page.focus("#compare-divider")
    area = page.locator("#map").bounding_box()
    # Put the divider's line through the middle of the "Before" label.
    page.evaluate(f"""document.getElementById('compare-divider').style.left = '{box['x'] + box['width'] / 2 - area['x']}px'""")
    order = page.evaluate("""[getComputedStyle(document.getElementById('compare-before')).zIndex,
      getComputedStyle(document.getElementById('compare-divider')).zIndex]""")
    assert order[0] != "auto" and (order[1] == "auto" or int(order[0]) > int(order[1]))


def test_close_works_with_the_divider_dragged_over_it(app):
    app.click("#compare-button")
    expect(app.locator("#compare-view")).to_be_visible()
    box = app.locator("#map").bounding_box()
    close = app.locator("#compare-close").bounding_box()
    middle_y = box["y"] + box["height"] / 2
    app.mouse.move(box["x"] + box["width"] / 2, middle_y)
    app.mouse.down()
    app.mouse.move(close["x"] + close["width"] / 2, middle_y, steps=6)
    app.mouse.up()
    assert top_element_is_inside(app, "#compare-close")
    app.click("#compare-close")
    expect(app.locator("#compare-view")).to_be_hidden()

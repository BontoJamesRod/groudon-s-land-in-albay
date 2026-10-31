"""Browser tests for the map labels: the danger-zone label and the compare divider."""
import pytest
from playwright.sync_api import expect

from .conftest import prepare_page, wait_until_ready

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
# Lists the labels that the divider's visible line runs through.
UNDER_LINE = """(() => {
  const line = document.querySelector('#compare-divider span').getBoundingClientRect();
  return [...document.querySelectorAll('.town-label, .zone-label')]
    .filter((label) => {
      const box = label.getBoundingClientRect();
      return box.left < line.right && box.right > line.left;
    })
    .map((label) => label.textContent);
})()"""


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


@pytest.mark.parametrize("share", [0.2, 0.35, 0.5, 0.65, 0.8])
def test_no_label_sits_under_the_divider(app, share):
    app.click("#compare-button")
    expect(app.locator("#compare-view")).to_be_visible()
    box = app.locator("#map").bounding_box()
    middle_y = box["y"] + box["height"] / 2
    app.mouse.move(box["x"] + box["width"] / 2, middle_y)
    app.mouse.down()
    app.mouse.move(box["x"] + box["width"] * share, middle_y, steps=6)
    app.mouse.up()
    assert app.evaluate(UNDER_LINE) == []


def test_labels_return_when_compare_closes(app):
    start = app.evaluate("[...document.querySelectorAll('.town-label, .zone-label')].map((label) => label.getBoundingClientRect().left)")
    app.click("#compare-button")
    expect(app.locator("#compare-view")).to_be_visible()
    app.click("#compare-close")
    assert app.evaluate("[...document.querySelectorAll('.town-label, .zone-label')].map((label) => label.getBoundingClientRect().left)") == start

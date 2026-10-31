"""Open each main screen at 1280 and 360 px, and take a picture of it.

A normal run keeps the pictures in a temporary folder, so running the tests changes no files.
To refresh the saved ones, with real map tiles, run in PowerShell:
    $env:SAVE_SCREENS = "1"; pytest pipeline/tests/e2e/test_screens.py; Remove-Item Env:SAVE_SCREENS
"""
import json
import os
from pathlib import Path

import pytest

from .conftest import ROOT, open_drawer_if_closed, prepare_page, read_fixture, wait_until_ready

pytestmark = pytest.mark.e2e

SAVED_FOLDER = ROOT / "pipeline" / "reports" / "screens"
SAVING = os.environ.get("SAVE_SCREENS") == "1"
SIZES = {1280: 800, 360: 740}


def open_nothing(page):
    pass


def open_readout(page):
    point = page.evaluate("""(() => {
      testMap.setView([13.1804, 123.69534], testMap.getZoom(), { animate: false });
      const p = testMap.latLngToContainerPoint([13.1804, 123.69534]);
      return [p.x, p.y];
    })()""")
    box = page.locator("#map").bounding_box()
    page.mouse.click(box["x"] + point[0], box["y"] + point[1])
    page.locator("#readout-body .readout-result").first.wait_for()


def open_search(page):
    page.click("#search-button")
    page.fill("#search-input", "Ta")


def open_compare(page):
    open_drawer_if_closed(page)
    page.click("#compare-button")
    page.locator("#compare-view").wait_for()


def opener(button, panel):
    def open_panel(page):
        page.click(button)
        page.locator(f"{panel} [data-body] > *").first.wait_for()
    return open_panel


SCREENS = {
    "main": open_nothing,
    "drawer-open": open_drawer_if_closed,
    "readout": open_readout,
    "search": open_search,
    "compare": open_compare,
    "help": opener("#help-button", "#help-panel"),
    "sources": opener("#sources-button", "#sources-panel"),
    "check": opener("#check-button", "#check-panel"),
    "picker": opener("#site-name", "#picker-panel"),
}


def save(page, name, width, tmp_path):
    folder = SAVED_FOLDER if SAVING else tmp_path
    folder.mkdir(parents=True, exist_ok=True)
    if SAVING:
        page.wait_for_load_state("networkidle")
    path = folder / f"{name}-{width}.jpg"
    page.screenshot(path=path, type="jpeg", quality=70)
    assert path.stat().st_size > 0


@pytest.mark.parametrize("width", SIZES)
@pytest.mark.parametrize("name", SCREENS)
def test_screen(page, site_url, tmp_path, name, width):
    prepare_page(page, width=width, height=SIZES[width], tiles="real" if SAVING else "fake")
    page.goto(site_url)
    wait_until_ready(page)
    SCREENS[name](page)
    save(page, name, width, tmp_path)


@pytest.mark.parametrize("width", SIZES)
def test_screen_no_pairs(page, site_url, tmp_path, width):
    prepare_page(page, width=width, height=SIZES[width], tiles="real" if SAVING else "fake")
    empty = json.dumps(read_fixture("empty_pairs.json"))
    page.route("**/sites/mayon/pairs.json", lambda route: route.fulfill(body=empty, content_type="application/json"))
    page.goto(site_url)
    page.locator("#app-message").wait_for()
    save(page, "no-pairs", width, tmp_path)


@pytest.mark.parametrize("width", SIZES)
def test_screen_not_found(page, site_url, tmp_path, width):
    page.set_viewport_size({"width": width, "height": SIZES[width]})
    page.goto(site_url + "no-such-page")
    save(page, "not-found", width, tmp_path)

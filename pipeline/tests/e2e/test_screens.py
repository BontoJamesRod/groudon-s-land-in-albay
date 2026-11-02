"""Open each main screen at 1280 and 360 px, and take a picture of it.

A normal run keeps the pictures in a temporary folder, so running the tests changes no files.
To save them to pipeline/out/screens, which git ignores, with real map tiles, run in PowerShell:
    $env:SAVE_SCREENS = "1"; pytest pipeline/tests/e2e/test_screens.py; Remove-Item Env:SAVE_SCREENS
"""
import json
import os
from pathlib import Path

import pytest

from .conftest import ROOT, close_list_on_a_phone, envelope, open_drawer_if_closed, prepare_page, read_data, read_fixture, wait_until_ready

pytestmark = pytest.mark.e2e

SAVED_FOLDER = ROOT / "pipeline" / "out" / "screens"
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


def open_channel_list(page):
    page.click("#channels-button")
    page.locator("#channel-body .channel-row").first.wait_for()


def opener_for_channel(name):
    def open_channel(page):
        open_channel_list(page)
        page.click(f"#channel-body .channel-row:has-text('{name}')")
        page.locator("#channel-body .channel-bar").first.wait_for()
    return open_channel


def open_channel_with_gap(page):
    opener_for_channel("Mi-isi")(page)
    page.locator("#channel-body .channel-bar-dim").scroll_into_view_if_needed()


def open_gap_pair(page):
    page.select_option("#pair-list", "mayon_A111F008_20260727_20260820")
    page.locator("#pair-gap:not(:empty)").wait_for()
    open_drawer_if_closed(page)


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
    "channels-list": open_channel_list,
    "channel-view": opener_for_channel("Mi-isi"),
    "channel-view-short": opener_for_channel("Basud"),
    "channel-gap": open_channel_with_gap,
    "gap-pair": open_gap_pair,
}


def save(page, name, width, tmp_path, settle=True):
    folder = SAVED_FOLDER if SAVING else tmp_path
    folder.mkdir(parents=True, exist_ok=True)
    if SAVING and settle:
        # The page's first network quiet happens only once, so wait for the tiles on screen now as well.
        page.wait_for_load_state("networkidle")
        page.wait_for_function("document.querySelectorAll('.leaflet-tile:not(.leaflet-tile-loaded)').length === 0")
        page.wait_for_timeout(300)
    path = folder / f"{name}-{width}.jpg"
    page.screenshot(path=path, type="jpeg", quality=70)
    assert path.stat().st_size > 0


@pytest.mark.parametrize("width", SIZES)
@pytest.mark.parametrize("name", SCREENS)
def test_screen(page, site_url, tmp_path, name, width):
    prepare_page(page, width=width, height=SIZES[width], tiles="real" if SAVING else "fake")
    page.goto(site_url)
    wait_until_ready(page)
    # The main screen shows what opens first. The others start from the pass controls.
    if name != "main":
        close_list_on_a_phone(page)
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


def no_radar_data_rows():
    """Mi-isi has no radar value in the latest pair, or in the one before it. The rest is real."""
    rows = read_data("sites/mayon/channel_areas.json")
    missing = {"mayon_A111F008_20261007_20261019", "mayon_D104F082_20261007_20261019"}
    return [{**row, "flagged_area_km2": None, "checked_area_km2": 0} if row["channel_id"] == "mayon_miisi" and row["pair_id"] in missing else row
            for row in rows]


@pytest.mark.parametrize("width", SIZES)
def test_screen_channel_no_data(page, site_url, tmp_path, width):
    prepare_page(page, width=width, height=SIZES[width], tiles="real" if SAVING else "fake")
    page.route("**/sites/mayon/channel_areas.json", lambda route: route.fulfill(body=envelope(no_radar_data_rows()), content_type="application/json"))
    page.goto(site_url)
    wait_until_ready(page)
    open_channel_list(page)
    save(page, "channels-no-data", width, tmp_path)
    page.click("#channel-body .channel-row:has-text('Mi-isi')")
    page.locator("#channel-body .channel-bar").last.scroll_into_view_if_needed()
    save(page, "channel-no-data", width, tmp_path)


@pytest.mark.parametrize("width", SIZES)
def test_screen_channels_empty(page, site_url, tmp_path, width):
    prepare_page(page, width=width, height=SIZES[width], tiles="real" if SAVING else "fake")
    body = json.dumps({"type": "FeatureCollection", "generated_at": "2026-11-01T00:00:00Z", "schema_version": "1.0", "features": []})
    page.route("**/sites/mayon/channels.geojson", lambda route: route.fulfill(body=body, content_type="application/json"))
    page.goto(site_url)
    wait_until_ready(page)
    page.click("#channels-button")
    page.locator("#channel-status:not(:empty)").wait_for()
    save(page, "channels-empty", width, tmp_path)


@pytest.mark.parametrize("width", SIZES)
def test_screen_channels_loading_and_error(page, site_url, tmp_path, width):
    prepare_page(page, width=width, height=SIZES[width], tiles="real" if SAVING else "fake")
    release = []
    # The file doesn't answer until the picture is taken, and then it fails. So this picture can't
    # wait for the network to go quiet: the request would time out, and it would show the error.
    page.route("**/sites/mayon/channel_areas.json", lambda route: release.append(route))
    page.goto(site_url)
    wait_until_ready(page)
    page.locator("#channel-status:has-text('Loading')").wait_for()
    page.wait_for_timeout(300)
    save(page, "channels-loading", width, tmp_path, settle=False)
    release[0].abort()
    page.locator("#channel-retry").wait_for()
    save(page, "channels-error", width, tmp_path)


@pytest.mark.parametrize("width", SIZES)
def test_screen_channels_unavailable(page, site_url, tmp_path, width):
    prepare_page(page, width=width, height=SIZES[width], tiles="real" if SAVING else "fake")
    page.route("**/sites/mayon/channels.geojson", lambda route: route.fulfill(status=404))
    page.goto(site_url)
    wait_until_ready(page)
    open_drawer_if_closed(page)
    page.locator("#channels-unavailable").wait_for()
    save(page, "channels-unavailable", width, tmp_path)

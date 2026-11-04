"""Shared setup for the browser tests: a local copy of the site and a page that opens it.

The tests use Chromium through Playwright. Run only these with: pytest -m e2e
They never touch the real map tile host unless a test asks for it, so they work offline.
"""
import functools
import http.server
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

ROOT = Path(__file__).resolve().parents[3]
SITE = ROOT / "site"
FIXTURES = ROOT / "pipeline" / "tests" / "fixtures"
TILE_HOST = "https://tiles.maps.eox.at/**"
# A 1 x 1 pixel image, sent back instead of real map tiles.
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000002000001e221bc330000000049454e44ae426082"
)
# Lets a test reach the map. It is added only to the test browser's copy of Leaflet.
MAP_HOOK = "\nL.Map.addInitHook(function () { window.testMap = this; });\n"


class SiteHandler(http.server.SimpleHTTPRequestHandler):
    """Serve site/ like the real host: unknown paths get 404.html, and some files can be slow."""

    slow_files = {}  # part of a path -> seconds to wait

    def log_message(self, *args):
        pass

    def do_GET(self):
        for part, seconds in self.slow_files.items():
            if part in self.path:
                time.sleep(seconds)
        super().do_GET()

    def send_error(self, code, message=None, explain=None):
        if code != 404:
            super().send_error(code, message, explain)
            return
        body = (SITE / "404.html").read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class RoomyServer(http.server.ThreadingHTTPServer):
    """Python's default queue holds 5 waiting connections. On a busy computer Windows refuses the
    rest, one of the site's scripts fails to load, and the page never leaves "Loading"."""

    request_queue_size = 128


@pytest.fixture(scope="session")
def site_url():
    """Serve site/ on a free local port for the whole test run."""
    handler = functools.partial(SiteHandler, directory=str(SITE))
    server = RoomyServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}/"
    server.shutdown()
    server.server_close()


@pytest.fixture
def slow_files():
    """Make chosen files slow for one test: slow_files["pair.json"] = 1.5"""
    SiteHandler.slow_files = {}
    yield SiteHandler.slow_files
    SiteHandler.slow_files = {}


def add_map_hook(page):
    """Append the test hook to Leaflet as the browser downloads it."""
    def with_hook(route):
        response = route.fetch()
        route.fulfill(response=response, body=response.text() + MAP_HOOK)
    page.route("**/leaflet.js", with_hook)


def wait_until_ready(page):
    """Wait until the first pair is on screen."""
    page.wait_for_function("document.getElementById('pair-label').textContent !== ''")
    page.wait_for_function("document.getElementById('loading').hidden")


def prepare_page(page, width=1280, height=800, tiles="fake"):
    """Size the window and choose what map tiles do: fake, blocked or real."""
    page.set_viewport_size({"width": width, "height": height})
    add_map_hook(page)
    if tiles == "fake":
        page.route(TILE_HOST, lambda route: route.fulfill(body=TINY_PNG, content_type="image/png"))
    elif tiles == "blocked":
        page.route(TILE_HOST, lambda route: route.abort())
        page.route("**/relief/**", lambda route: route.abort())


def open_channel_list(page):
    """The channel list is always in the side column (FR-094), or in the sheet under the map on a phone,
    where the closed sheet shows the first 3 channels (FR-095)."""
    expect(page.locator("#channel-panel")).to_be_visible()


def open_channel(page, name):
    """Open a channel's page from the list, opening the phone sheet first if its row is hidden."""
    row = page.locator("#channel-body .channel-row", has_text=name).first
    row.wait_for(state="attached")
    if not row.is_visible():
        page.click("#show-all")
    row.click()
    expect(page.locator("#channel-title")).to_have_text(name)


def open_drawer_if_closed(page):
    """On a phone the Compare button is inside the drawer. On a desktop this does nothing."""
    toggle = page.locator("#drawer-toggle")
    if toggle.is_visible() and toggle.get_attribute("aria-expanded") == "false":
        toggle.click()


@pytest.fixture
def app(page, site_url):
    """The app, open at 1280 px with its latest pair on screen."""
    prepare_page(page)
    page.goto(site_url)
    wait_until_ready(page)
    return page


def envelope(data):
    """Wrap data the way the published JSON files are wrapped (docs/06)."""
    return json.dumps({"data": data, "meta": {"generated_at": "2026-10-31T00:00:00Z", "schema_version": "1.0"}})


def read_data(relative_path):
    """Read the data inside a published JSON file."""
    return json.loads((SITE / "data" / relative_path).read_text(encoding="utf-8"))["data"]


def read_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def latest_pair():
    """The pair the site opens on: the newest published pair in the data, whichever it is."""
    return read_data("sites/mayon/pairs.json")[-1]


def local_date(utc_text, zone="Asia/Manila"):
    """A UTC time as the site writes the date in the site's time zone, for example "Oct 8, 2026"."""
    day = datetime.fromisoformat(utc_text.replace("Z", "+00:00")).astimezone(ZoneInfo(zone))
    return f"{day:%b} {day.day}, {day.year}"


def latest_dates():
    """The latest pair's before and after dates, as the site writes them."""
    pair = latest_pair()
    return local_date(pair["before_acquired_start"]), local_date(pair["after_acquired_start"])


DISCLAIMER = "This is not an official warning. Follow PHIVOLCS and your LGU."
SHORT_DISCLAIMER = "Not an official warning · Follow PHIVOLCS"
FOOTER_BUTTONS = ("#sources-button", "#check-button")


def open_footer_link(page, selector):
    """Open "Data sources" or "How we checked this" as a visitor would (FR-090). On a phone they're in
    "What am I looking at?". On a desktop the bottom bar slides up when the pointer reaches the bottom edge."""
    if page.viewport_size["width"] <= 700:
        page.click("#help-button")
        page.click(f'#help-panel .help-more button[data-opens="{selector.lstrip("#")}"]')
        return
    page.mouse.move(page.viewport_size["width"] / 2, page.viewport_size["height"] - 2)
    page.click(selector)


def open_panama_link(page):
    """Open "How we checked this" and follow "Open the Panama test map" (FR-100)."""
    open_footer_link(page, "#check-button")
    page.click("#check-panel a:has-text('Open the Panama test map')")


def go_to_panama(page):
    """Reach the Panama test site the visitor's way, and wait until it shows (FR-099)."""
    open_panama_link(page)
    expect(page.locator("#site-name")).to_have_text("Azuero Peninsula, Panama")
    expect(page.locator("#test-banner")).to_be_visible()


def open_control(page, selector):
    """Click a control, or open a bottom-bar link the way a visitor reaches it."""
    if selector in FOOTER_BUTTONS:
        open_footer_link(page, selector)
    else:
        page.click(selector)

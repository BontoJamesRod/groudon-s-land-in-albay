"""Shared setup for the browser tests: a local copy of the site and a page that opens it.

The tests use Chromium through Playwright. Run only these with: pytest -m e2e
They never touch the real map tile host unless a test asks for it, so they work offline.
"""
import functools
import http.server
import json
import threading
import time
from pathlib import Path

import pytest

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


@pytest.fixture(scope="session")
def site_url():
    """Serve site/ on a free local port for the whole test run."""
    handler = functools.partial(SiteHandler, directory=str(SITE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
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


def close_list_on_a_phone(page):
    """On a phone the channel list opens first, and the pass controls are behind it."""
    if page.viewport_size["width"] <= 700 and page.locator("#channel-panel").is_visible():
        page.click("#channel-close")


def open_drawer_if_closed(page):
    """On a phone the Compare button is inside the drawer. On a desktop this does nothing."""
    close_list_on_a_phone(page)
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

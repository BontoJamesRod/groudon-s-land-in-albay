"""TC-050, measured on the local server: first-view size and load time on Fast 4G.

The test sends fake tiles so that it works offline, which means it doesn't count real
tiles. pipeline/reports/measure_first_view.py measures with real ones.
"""
import pytest

from .conftest import prepare_page, wait_until_ready
from .pipeline_first_view import measure_page

pytestmark = pytest.mark.e2e

# Suggested targets from 08 TC-050. The final NFR-001 target is still [TBD].
MAX_BYTES = 5_000_000
MAX_SECONDS = 5


def test_tc050_first_view_is_within_the_suggested_budget(page, site_url):
    prepare_page(page)
    size, seconds, _ = measure_page(page, site_url, wait_until_ready)
    assert size <= MAX_BYTES
    assert seconds <= MAX_SECONDS


def test_js_and_css_are_requested_with_a_version(page, site_url):
    prepare_page(page)
    urls = []
    page.on("request", lambda request: urls.append(request.url))
    page.goto(site_url)
    wait_until_ready(page)
    assets = [url for url in urls if "/js/" in url or "/css/" in url]
    assert len(assets) >= 12
    assert all("?v=" in url for url in assets), [url for url in assets if "?v=" not in url]

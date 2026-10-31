"""TC-077: the map credit and the Data sources panel follow the selected site (T-086, T-087).

Panama is still a draft, so it's added to the site list in this test's browser only.
"""
import pytest
from playwright.sync_api import expect

from mrw.config import build_sites_row, load_site

from .conftest import envelope, prepare_page, read_data, wait_until_ready

pytestmark = pytest.mark.e2e

MAYON_CREDIT = "Boundaries: NAMRIA and PSA via OCHA COD-AB (CC BY-IGO)"
PANAMA_CREDIT = "Boundaries: geoBoundaries (CC BY-SA 4.0)"


def open_with_panama(page, site_url):
    panama = {**build_sites_row(load_site("panama")), "status": "published"}
    prepare_page(page)
    page.route("**/data/sites.json", lambda route: route.fulfill(body=envelope(read_data("sites.json") + [panama]), content_type="application/json"))
    page.route("**/sites/panama/pairs.json", lambda route: route.fulfill(body=envelope([]), content_type="application/json"))
    page.goto(site_url)
    wait_until_ready(page)


def switch_to_panama(page):
    page.click("#site-name")
    page.click("#picker-panel button:has-text('Azuero Peninsula')")
    expect(page.locator("#site-name")).to_have_text("Azuero Peninsula, Panama")


def open_sources(page):
    page.click("#sources-button")
    expect(page.locator("#sources-panel")).not_to_contain_text("Loading sources")
    return page.locator("#sources-panel")


def test_mayon_shows_its_own_credit_and_sources(app):
    attribution = app.locator(".leaflet-control-attribution")
    expect(attribution).to_contain_text(MAYON_CREDIT)
    expect(attribution).not_to_contain_text("geoBoundaries")
    panel = open_sources(app)
    expect(panel).to_contain_text("Philippine municipal and city boundaries")
    expect(panel).to_contain_text("Esri")
    expect(panel).not_to_contain_text("geoBoundaries")


def test_panama_shows_its_own_credit_and_sources(page, site_url):
    open_with_panama(page, site_url)
    switch_to_panama(page)
    attribution = page.locator(".leaflet-control-attribution")
    expect(attribution).to_contain_text(PANAMA_CREDIT)
    expect(attribution).not_to_contain_text("NAMRIA")
    expect(attribution.locator('a[href="https://www.geoboundaries.org/"]')).to_have_count(1)
    panel = open_sources(page)
    expect(panel).to_contain_text("geoBoundaries")
    expect(panel).to_contain_text("License: CC BY-SA 4.0")
    expect(panel.locator('a[href="https://www.geoboundaries.org/"]')).to_have_count(1)
    expect(panel).to_contain_text("Esri")
    expect(panel).not_to_contain_text("Philippine")


def test_the_credit_changes_back_with_the_site(page, site_url):
    open_with_panama(page, site_url)
    switch_to_panama(page)
    page.click("#site-name")
    page.click("#picker-panel button:has-text('Mayon')")
    attribution = page.locator(".leaflet-control-attribution")
    expect(attribution).to_contain_text(MAYON_CREDIT)
    expect(attribution).not_to_contain_text("geoBoundaries")

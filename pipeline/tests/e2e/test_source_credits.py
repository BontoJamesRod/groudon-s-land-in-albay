"""TC-077: the map credit and the Data sources panel follow the selected site (T-086, T-087)."""
import pytest
from playwright.sync_api import expect

from .conftest import prepare_page, wait_until_ready

pytestmark = pytest.mark.e2e

MAYON_CREDIT = "Boundaries: NAMRIA and PSA via OCHA COD-AB (CC BY-IGO)"
PANAMA_CREDIT = "Boundaries: geoBoundaries (CC BY-SA 4.0)"


def open_with_panama(page, site_url):
    prepare_page(page)
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
    expect(panel).to_contain_text("Copernicus DEM GLO-30")
    expect(panel).not_to_contain_text("Esri")
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

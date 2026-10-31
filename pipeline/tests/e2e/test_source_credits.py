"""The Data sources panel must credit the Panama borders with their license (T-086)."""
import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def test_panel_credits_geoboundaries_with_its_license(app):
    app.click("#sources-button")
    panel = expect(app.locator("#sources-panel"))
    panel.to_contain_text("geoBoundaries")
    panel.to_contain_text("License: CC BY-SA 4.0")
    expect(app.locator('#sources-panel a[href="https://www.geoboundaries.org/"]')).to_have_count(1)

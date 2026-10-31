"""Run axe-core on the rendered page, in each main state of the app.

The page's text is filled in from strings.js when it loads, so only a check of the rendered
page can see it. The vendored copy of axe-core lives next to the tests and is never deployed.
"""
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import open_drawer_if_closed, prepare_page, wait_until_ready

pytestmark = pytest.mark.e2e

AXE = Path(__file__).parent / "vendor" / "axe-core-4.14.0" / "axe.min.js"
FAILING_IMPACTS = {"serious", "critical"}


def problems_on(page):
    """Inject axe-core, check the whole page, and describe each serious or critical problem."""
    page.add_script_tag(path=str(AXE))
    results = page.evaluate("axe.run(document)")
    return [
        f"{rule['id']} ({rule['impact']}): {node['target']} {node['failureSummary']}"
        for rule in results["violations"] if rule["impact"] in FAILING_IMPACTS
        for node in rule["nodes"]
    ]


def open_app(page, site_url, width=1280, height=800):
    prepare_page(page, width=width, height=height)
    page.goto(site_url)
    wait_until_ready(page)


def test_axe_finds_a_planted_problem(page, site_url):
    """If axe-core stopped working, the other tests here would pass without checking anything."""
    open_app(page, site_url)
    page.evaluate("document.getElementById('help-button').textContent = ''")
    assert any(problem.startswith("button-name") for problem in problems_on(page))


def test_main_screen(page, site_url):
    open_app(page, site_url)
    assert problems_on(page) == []


def test_help_panel(page, site_url):
    open_app(page, site_url)
    page.click("#help-button")
    expect(page.locator("#help-panel")).to_be_visible()
    assert problems_on(page) == []


def test_phone_with_the_drawer_closed(page, site_url):
    open_app(page, site_url, width=360, height=740)
    assert problems_on(page) == []


def test_phone_with_the_drawer_open(page, site_url):
    open_app(page, site_url, width=360, height=740)
    open_drawer_if_closed(page)
    expect(page.locator("#drawer-toggle")).to_have_attribute("aria-expanded", "true")
    assert problems_on(page) == []


def test_compare_view(page, site_url):
    open_app(page, site_url)
    page.click("#compare-button")
    expect(page.locator(".leaflet-compare-pane img")).to_have_count(2)
    expect(page.locator("#compare-view")).to_be_visible()
    assert problems_on(page) == []

"""TC-076 and TC-078: Panama has no summit, and its own wording. Mayon's stays as it was."""
import pytest
from playwright.sync_api import expect

from .test_accessibility import problems_on
from .conftest import prepare_page, wait_until_ready
from .test_mvp import card, tap_at

pytestmark = pytest.mark.e2e

EARTHQUAKE = "panama_D141F085_20260927_20261009"
QUIET = "panama_D141F085_20260915_20260927"
LAND_POINT = (7.48, -80.865)


def open_panama(page, site_url, width=1280, height=800):
    prepare_page(page, width=width, height=height)
    page.goto(site_url)
    wait_until_ready(page)
    page.click("#site-name")
    page.click("#picker-panel button:has-text('Azuero Peninsula')")
    expect(page.locator("#pair-list")).to_have_value(EARTHQUAKE)
    expect(page.locator("#legend-title")).to_have_text("Changed after the earthquake")


@pytest.fixture
def panama(page, site_url):
    open_panama(page, site_url)
    return page


def test_tc076_card_has_no_summit_lines(panama):
    tap_at(panama, *LAND_POINT)
    expect(card(panama)).to_contain_text("Confidence:")
    expect(card(panama)).not_to_contain_text("summit")
    expect(card(panama)).not_to_contain_text("Danger Zone")
    expect(card(panama)).not_to_contain_text("new material")


def test_tc078_the_earthquake_pair_says_changed_not_new_material(panama):
    legend = panama.locator(".legend")
    expect(legend).to_contain_text("Possible change (brightness only)")
    expect(legend).to_contain_text("Likely change (brightness and coherence agree)")
    for text in ("new material", "New material", "landslide", "Landslide"):
        expect(legend).not_to_contain_text(text)
    expect(panama.locator("#pair-events")).to_contain_text("Earthquake")


def test_tc078_the_quiet_pair_has_a_plain_title(panama):
    panama.select_option("#pair-list", QUIET)
    expect(panama.locator("#legend-title")).to_have_text("Radar change")


def test_tc078_panama_names_its_own_official_source(panama):
    expect(panama.locator(".disclaimer")).to_have_text("This is not an official warning. Follow SINAPROC and your local authorities.")
    panama.click("#help-button")
    help_panel = panama.locator("#help-panel")
    expect(help_panel).to_contain_text("SINAPROC")
    for text in ("PHIVOLCS", "new material", "Fresh rock", "landslide", "summit"):
        expect(help_panel).not_to_contain_text(text)
    assert help_panel.locator("a", has_text="SINAPROC website").get_attribute("href") == "https://www.sinaproc.gob.pa/"


def test_tc078_the_phone_handle_has_no_summit_limit(page, site_url):
    open_panama(page, site_url, width=360, height=740)
    expect(page.locator("#drawer-toggle")).to_contain_text("PROVISIONAL")
    expect(page.locator("#drawer-toggle")).not_to_contain_text("10 km")


def test_tc078_going_back_to_mayon_restores_its_wording(panama):
    panama.click("#site-name")
    panama.click("#picker-panel button:has-text('Mayon')")
    expect(panama.locator(".disclaimer")).to_have_text("This is not an official warning. Follow PHIVOLCS and your LGU.")
    expect(panama.locator("#legend-title")).to_contain_text("New material")


def test_the_check_summarizes_the_comparison_and_links_the_map(panama):
    panama.click("#check-button")
    panel = panama.locator("#check-panel")
    expect(panel).to_contain_text("University of Panama")
    expect(panel).to_contain_text("It doesn't show that any one colored spot")
    expect(panel).to_contain_text("27%")
    expect(panel.locator("table tr")).to_have_count(3)
    assert panel.locator("a", has_text="Open source").get_attribute("href").startswith("https://www.laestrella.com.pa/")
    assert panel.locator("img").count() == 0


def test_tc080_the_quiet_pair_says_what_it_was_used_for(panama):
    panama.select_option("#pair-list", QUIET)
    expect(panama.locator("#legend-title")).to_have_text("Radar change")
    panama.click("#check-button")
    panel = panama.locator("#check-panel")
    expect(panel).to_contain_text("Used as the 'before' comparison for the earthquake pair")
    expect(panel).not_to_contain_text("Not yet checked")


COAST_LINES = """async () => {
  const { outlinesInsideSite } = await import("./js/map.js");
  const read = async (name) => (await (await fetch(`data/sites/${name}`)).json());
  const site = (await read("../sites.json")).data.find((row) => row.id === "SITE");
  const lines = outlinesInsideSite(await read("SITE/FILE.geojson"), site).coordinates;
  const near = (a, b) => Math.abs(a - b) < 0.00002;
  const edgeSegments = lines.flatMap((line) => line.slice(1).filter((point, i) => {
    const before = line[i];
    return (near(point[0], site.bounds_east) && near(before[0], site.bounds_east))
      || (near(point[0], site.bounds_west) && near(before[0], site.bounds_west))
      || (near(point[1], site.bounds_north) && near(before[1], site.bounds_north))
      || (near(point[1], site.bounds_south) && near(before[1], site.bounds_south));
  })).length;
  return { lines: lines.length, points: lines.flat().length, edgeSegments };
}"""


@pytest.mark.parametrize("site_id", ["panama", "mayon"])
@pytest.mark.parametrize("name", ["land", "towns"])
def test_tc079_lines_leave_out_the_clipped_edges(app, site_id, name):
    result = app.evaluate(COAST_LINES.replace("SITE", site_id).replace("FILE", name))
    assert result["points"] > 100  # the real lines are still there
    assert result["edgeSegments"] == 0


def test_axe_on_panama_with_the_check_open(panama):
    panama.click("#check-button")
    expect(panama.locator("#check-panel table")).to_be_visible()
    assert problems_on(panama) == []

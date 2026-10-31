"""Browser tests for the MVP cases in docs/08 section 3. Each test name carries its TC number.

A case that needs data or a decision we don't have yet is skipped, and the reason says why.
"""
import io
import json
import re

import pytest
from PIL import Image
from playwright.sync_api import expect

from mrw.validation import build_record, load_sheet

from .conftest import envelope, prepare_page, read_data, read_fixture, wait_until_ready

pytestmark = pytest.mark.e2e

JULY_PAIR = "mayon_A111F008_20260703_20260715"
LATEST_PAIR = "mayon_A111F008_20261007_20261019"
SUMMIT = (13.2572, 123.6856)
DISCLAIMER = "This is not an official warning. Follow PHIVOLCS and your LGU."
NO_ERUPTION_PAIR = "No eruption pair: nothing acquired on or after 2026-10-30 may be opened until the thresholds are set."
NO_CHANNELS = "Channels (T-010, T-028) aren't built: they wait for the owner's choice of channel source."


def map_center(page):
    return page.evaluate("(() => { const c = testMap.getCenter(); return [c.lat, c.lng]; })()")


def map_zoom(page):
    return page.evaluate("testMap.getZoom()")


def tap_at(page, lat, lon):
    """Center the map on a point at the closest zoom, then click it with the real mouse."""
    point = page.evaluate(f"""(() => {{
      testMap.setView([{lat}, {lon}], testMap.getMaxZoom(), {{ animate: false }});
      const p = testMap.latLngToContainerPoint([{lat}, {lon}]);
      return [p.x, p.y];
    }})()""")
    box = page.locator("#map").bounding_box()
    page.mouse.click(box["x"] + point[0], box["y"] + point[1])


def cell(value):
    """A grid cell with this value, from the fixture list."""
    return next((row for row in read_fixture("grid_cells.json")["cells"] if row["value"] == value), None)


def card(page):
    return page.locator("#readout-body")


def overlay_offset(page):
    """How far the radar image is from where its map bounds say it should be, in pixels."""
    return page.evaluate("""(() => {
      const image = document.querySelector('.leaflet-radar-pane img');
      const box = image.getBoundingClientRect();
      const area = testMap.getContainer().getBoundingClientRect();
      const corner = testMap.latLngToContainerPoint([13.38, 123.56]);
      return Math.max(Math.abs(box.left - area.left - corner.x), Math.abs(box.top - area.top - corner.y));
    })()""")


def expect_disclaimer_on_screen(page):
    locator = page.locator(".disclaimer")
    expect(locator).to_have_text(DISCLAIMER)
    expect(locator).to_be_in_viewport()


def test_tc001_map_opens_on_mayon(app):
    assert map_center(app) == pytest.approx(SUMMIT, abs=0.001)
    assert map_zoom(app) == read_data("sites.json")[0]["default_zoom"]
    labels = app.locator(".town-label").all_inner_texts()
    assert {"Tabaco City", "Daraga", "Legazpi City"} <= set(labels)
    expect(app.locator(".zone-label")).to_have_text("Permanent Danger Zone (6 km)")
    # Town borders, the coastline and the ring are drawn as vector lines.
    assert app.locator(".leaflet-overlay-pane path").count() >= 3
    expect(app.locator('.leaflet-overlay-pane path[stroke="#fb923c"]')).to_have_count(1)
    expect(app.locator('.leaflet-overlay-pane path[stroke="#7dd3fc"]')).to_have_count(1)


def test_tc002_background_fails_but_our_layers_stay(page, site_url):
    prepare_page(page, tiles="blocked")
    page.goto(site_url)
    wait_until_ready(page)
    expect(page.locator("#background-notice")).to_have_text("Background map unavailable")
    expect(page.locator("#background-notice")).to_be_visible()
    expect(page.locator('.leaflet-overlay-pane path[stroke="#fb923c"]')).to_have_count(1)
    expect(page.locator(".zone-label")).to_be_visible()


def test_tc003_pan_and_zoom_keep_the_layer_on_the_map(app):
    start = map_center(app)
    box = app.locator("#map").bounding_box()
    app.mouse.move(box["x"] + 500, box["y"] + 200)
    app.mouse.down()
    app.mouse.move(box["x"] + 400, box["y"] + 150, steps=5)
    app.mouse.up()
    app.wait_for_timeout(400)
    assert map_center(app) != pytest.approx(start, abs=1e-5)
    assert overlay_offset(app) < 1.5
    zoom = map_zoom(app)
    for _ in range(3):
        app.mouse.wheel(0, -300)
        app.wait_for_timeout(500)
    assert map_zoom(app) > zoom
    assert overlay_offset(app) < 1.5


def test_tc004_zoom_stops_at_the_minimum(app):
    for _ in range(5):
        app.evaluate("testMap.zoomOut(1, { animate: false })")
    minimum = read_data("sites.json")[0]["min_zoom"]
    assert map_zoom(app) == minimum
    expect(app.locator(".leaflet-control-zoom-out")).to_have_class(re.compile("leaflet-disabled"))


def test_tc005_find_tabaco_city(app):
    app.click("#search-button")
    app.fill("#search-input", "Tab")
    app.click("#search-suggestions button:has-text('Tabaco City')")
    expect(card(app)).to_contain_text("Tabaco City")
    town = next(row for row in read_data_towns() if row["name"] == "Tabaco City")
    assert map_center(app) == pytest.approx((town["label_lat"], town["label_lon"]), abs=0.001)


def read_data_towns():
    from .conftest import SITE
    towns = json.loads((SITE / "data/sites/mayon/towns.geojson").read_text(encoding="utf-8"))
    return [feature["properties"] for feature in towns["features"]]


def test_tc006_no_match_message_and_map_stays(app):
    start = map_center(app)
    app.click("#search-button")
    app.fill("#search-input", "Xyz")
    app.press("#search-input", "Enter")
    expect(app.locator("#search-message")).to_have_text("No town found. Try another name or tap the map.")
    assert map_center(app) == pytest.approx(start)


def test_tc007_suggestions_start_at_two_letters(app):
    app.click("#search-button")
    app.fill("#search-input", "T")
    expect(app.locator("#search-suggestions button")).to_have_count(0)
    app.fill("#search-input", "Ta")
    assert app.locator("#search-suggestions button").count() > 0


def test_tc008_land_point_in_daraga(app):
    town = next(row for row in read_data_towns() if row["name"] == "Daraga")
    tap_at(app, town["label_lat"], town["label_lon"])
    expect(card(app)).to_contain_text("Daraga")
    expect(card(app)).to_contain_text(re.compile(r"Distance to summit: \d+\.\d km"))
    expect(card(app)).to_contain_text("Outside the danger zone")
    expect(card(app)).to_contain_text(re.compile(r"Confidence: (none|low|high)"))


@pytest.mark.parametrize("value, confidence", [(0, "none"), (1, "low"), (2, "high")])
def test_tc008_card_reads_each_class_from_the_grid(app, value, confidence):
    row = cell(value)
    tap_at(app, row["lat"], row["lon"])
    expect(card(app)).to_contain_text(f"Confidence: {confidence}")


def test_tc009_sea(app):
    row = cell(254)
    tap_at(app, row["lat"], row["lon"])
    expect(card(app)).to_contain_text("No radar data here")
    expect(card(app)).to_contain_text("sea")


def test_tc010_outside_radar_coverage(app):
    """No published grid has a 255 cell, so this taps just off the grid, which reads as 255."""
    if cell(255):
        pytest.fail("A real 255 cell now exists: use it here")
    bounds = read_data("sites.json")[0]
    tap_at(app, bounds["bounds_north"] + 0.002, bounds["bounds_west"] + 0.1)
    expect(card(app)).to_contain_text("No radar data here")
    expect(card(app)).to_contain_text("outside radar coverage")


def test_tc011_masked_slope(app):
    row = cell(253)
    tap_at(app, row["lat"], row["lon"])
    expect(card(app)).to_contain_text("No radar data here")
    expect(card(app)).to_contain_text("a slope the radar can't see")


def test_tc012_inside_danger_zone(app):
    tap_at(app, SUMMIT[0] + 3 / 111.0, SUMMIT[1])
    expect(card(app)).to_contain_text("Inside the Permanent Danger Zone. Entry is not allowed.")


def test_tc013_pick_an_earlier_pair(app):
    app.select_option("#pair-list", JULY_PAIR)
    label = app.locator("#pair-label")
    expect(label).to_have_text("Jul 4, 2026 to Jul 16, 2026 (Asia/Manila), track 111, frame 8, ascending")
    expect(app.locator(f'.leaflet-radar-pane img[src*="{JULY_PAIR}"]')).to_have_count(1)


def test_tc014_next_on_the_latest_pair(app):
    before = app.input_value("#pair-list")
    app.click("#next")
    expect(app.locator("#timeline-message")).to_have_text("This is the latest pass")
    assert app.input_value("#pair-list") == before


def test_tc015_july_event_is_marked(app):
    option = app.locator(f'#pair-list option[value="{JULY_PAIR}"]')
    expect(option).to_contain_text("Pyroclastic density current")
    app.select_option("#pair-list", JULY_PAIR)
    expect(app.locator("#pair-events")).to_have_text("Event in this period: Pyroclastic density current")


@pytest.mark.skip(reason=NO_ERUPTION_PAIR)
def test_tc015_eruption_is_marked():
    pass


def test_tc016_latest_pair_by_default(app):
    latest = max(read_data("sites/mayon/pairs.json"), key=lambda pair: pair["after_acquired_start"])
    assert app.input_value("#pair-list") == latest["id"]


def test_tc017_site_with_no_pairs(page, site_url):
    prepare_page(page)
    empty = json.dumps(read_fixture("empty_pairs.json"))
    page.route("**/sites/mayon/pairs.json", lambda route: route.fulfill(body=empty, content_type="application/json"))
    page.goto(site_url)
    expect(page.locator("#app-message")).to_have_text("No radar passes processed yet for this site")
    expect(page.locator("#panel")).to_be_hidden()
    expect(page.locator(".zone-label")).to_be_visible()
    expect(page.locator(".leaflet-radar-pane img")).to_have_count(0)


def test_tc020_layer_legend_and_area_on_the_latest_pair(app):
    """The doc asks for the eruption pair, which is off limits for now, so this uses the latest one."""
    pair = read_data(f"sites/mayon/pairs/{LATEST_PAIR}/pair.json")
    expect(app.locator(".leaflet-radar-pane img")).to_have_count(1)
    layer = next(item for item in pair["layers"] if item["kind"] == "new_material")
    rows = [" ".join(row.split()) for row in app.locator("#legend-rows li").all_inner_texts()]
    assert rows == [f"{item['label']}. Confidence: {item['confidence']}" for item in layer["legend"]]
    expect(app.locator("#legend-area")).to_have_text(f"Units: class. Total detected area: {pair['new_material_area_km2']:.2f} km²")
    expect(app.locator("#legend-title")).to_contain_text("PROVISIONAL")


def test_tc021_pair_with_nothing_detected(page, site_url):
    pair = read_data(f"sites/mayon/pairs/{LATEST_PAIR}/pair.json")
    zero = {**pair, "new_material_area_km2": 0, "high_confidence_area_km2": 0, "low_confidence_area_km2": 0}
    prepare_page(page)
    page.route(f"**/{LATEST_PAIR}/pair.json", lambda route: route.fulfill(body=envelope(zero), content_type="application/json"))
    page.goto(site_url)
    expect(page.locator("#summary")).to_have_text("No new material detected between Oct 8, 2026 and Oct 20, 2026")
    expect(page.locator("#legend-area")).to_contain_text("0.00 km²")


def test_tc028_explainer(app):
    app.click("#help-button")
    panel = app.locator("#help-panel")
    for title in ("How radar sees", "What each color means", "Confidence levels", "Limitations"):
        expect(panel.locator("h3", has_text=title)).to_be_visible()
    limits = panel.locator("h3:has-text('Limitations') + ul li")
    assert limits.count() >= 3
    assert panel.locator("a", has_text="PHIVOLCS website").get_attribute("href") == "https://www.phivolcs.dost.gov.ph/"


def test_tc029_disclaimer_stays_on_screen(app):
    expect_disclaimer_on_screen(app)
    app.uncheck("#layer-toggle")
    expect_disclaimer_on_screen(app)
    app.check("#layer-toggle")
    expect_disclaimer_on_screen(app)
    for button, panel in (("#help-button", "#help-panel"), ("#sources-button", "#sources-panel"),
                          ("#check-button", "#check-panel"), ("#site-name", "#picker-panel")):
        app.click(button)
        expect_disclaimer_on_screen(app)
        app.click(f"{panel} [data-close]")
        expect_disclaimer_on_screen(app)
    app.click("#compare-button")
    expect_disclaimer_on_screen(app)


def test_tc030_no_prediction_wording_on_the_screens(app):
    """Also covered for every string and data file by pipeline/tests/test_wording.py."""
    app.click("#help-button")
    text = app.locator("body").inner_text()
    near = re.compile(r"\b(will|expect\w*|forecast\w*|predict\w*)\b[^.]{0,60}\b(lahar|eruption|flood)|"
                      r"\b(lahar|eruption|flood)\w*\b[^.]{0,60}\b(will|expect\w*|forecast\w*|predict\w*)\b", re.I)
    assert near.search(text) is None


def test_tc031_radar_sources_on_the_latest_pair(app):
    """The doc asks for the eruption pair, which is off limits for now, so this uses the latest one."""
    app.click("#sources-button")
    panel = app.locator("#sources-panel")
    expect(panel).to_contain_text("GCOV")
    expect(panel).to_contain_text("GUNW")
    expect(panel).to_contain_text("PROVISIONAL")
    expect(panel).to_contain_text("Acquired: Oct 8, 2026")
    links = panel.locator('a[href*="search.asf.alaska.edu"]')
    assert links.count() >= 3
    for link in links.all():
        assert link.inner_text().startswith("NISAR_L2_PR_")
        assert link.inner_text() in link.get_attribute("href")


def test_tc032_context_sources(app):
    """Channels aren't listed yet, because channels aren't built (see the TC-044 to TC-047 skips)."""
    app.click("#sources-button")
    context = app.locator("#sources-panel h3:has-text('Context data') + ul")
    expect(context).to_be_visible()
    for row in read_data("sources.json"):
        expect(context).to_contain_text(row["name"])
        expect(context).to_contain_text(row["license"])


@pytest.mark.skip(reason="No second site: choosing one is the owner's decision.")
def test_tc033_switch_to_the_second_site():
    pass


def test_tc034_second_site_fails_and_mayon_stays(page, site_url):
    """Uses a made-up second site, on this test's browser only, whose files can't load."""
    sites = read_data("sites.json")
    second = {**sites[0], "id": "test_second", "name": "Test Second Site"}
    prepare_page(page)
    page.route("**/data/sites.json", lambda route: route.fulfill(body=envelope(sites + [second]), content_type="application/json"))
    page.route("**/sites/test_second/**", lambda route: route.fulfill(status=404))
    page.goto(site_url)
    wait_until_ready(page)
    page.click("#site-name")
    page.click("#picker-panel button:has-text('Test Second Site')")
    expect(page.locator("#app-message")).to_have_text("Couldn't load Test Second Site. Try again.")
    expect(page.locator("#app-retry")).to_be_visible()
    expect(page.locator("#site-name")).to_have_text("Mayon Volcano, Albay")
    expect(page.locator(".leaflet-radar-pane img")).to_have_count(1)


def test_tc038_unknown_path(page, site_url):
    response = page.goto(site_url + "no-such-page")
    assert response.status == 404
    expect(page.locator("h1")).to_have_text("Page not found")
    page.route("https://server.arcgisonline.com/**", lambda route: route.abort())
    page.click("#home")
    page.wait_for_selector("#map")


def test_tc040_validation_table_from_a_local_fixture(app):
    """No record is published: the July draft waits for the owner's review, so this is local only."""
    record = build_record(JULY_PAIR, load_sheet(JULY_PAIR), "2026-10-31T00:00:00Z")
    app.route(f"**/{JULY_PAIR}/validation.json", lambda route: route.fulfill(body=envelope(record), content_type="application/json"))
    app.select_option("#pair-list", JULY_PAIR)
    expect(app.locator("#pair-events")).not_to_have_text("")
    app.click("#check-button")
    panel = app.locator("#check-panel")
    expect(panel.locator("table tr")).to_have_count(len(record["items"]) + 1)
    expect(panel).to_contain_text(record["items"][0]["place_name"])
    expect(panel).to_contain_text(record["source_name"])
    assert panel.locator("a", has_text="Open source").get_attribute("href") == record["source_url"]


def test_tc041_no_validation(app):
    app.click("#check-button")
    expect(app.locator("#check-panel")).to_contain_text("Not yet checked against an independent source")


def controls_too_small(page):
    """List each visible control under 44 x 44 px. A checkbox counts with its label."""
    return page.evaluate("""[...document.querySelectorAll('button, select, a, input, [role=slider]')]
      .filter((node) => node.offsetParent !== null || node.getClientRects().length > 0)
      .filter((node) => !node.closest('dialog:not([open])'))
      .map((node) => {
        const box = (node.closest('label') || node).getBoundingClientRect();
        return { name: node.id || node.textContent.trim() || node.className, w: box.width, h: box.height };
      })
      .filter((row) => row.w < 44 - 0.5 || row.h < 44 - 0.5)""")


def test_tc042_phone_layout(page, site_url):
    prepare_page(page, width=360, height=740)
    page.goto(site_url)
    wait_until_ready(page)

    def no_sideways_scroll():
        return page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

    assert no_sideways_scroll()
    too_small = [row for row in controls_too_small(page) if "Leaflet" not in row["name"]]
    assert too_small == []
    # Every control can be reached and used.
    page.locator("#compare-button").scroll_into_view_if_needed()
    page.click("#compare-button")
    expect(page.locator("#compare-view")).to_be_visible()
    assert no_sideways_scroll()
    assert [row for row in controls_too_small(page) if "Leaflet" not in row["name"]] == []
    box = page.locator("#map").bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * 0.3, box["y"] + box["height"] / 2, steps=5)
    page.mouse.up()
    assert page.evaluate("parseFloat(document.getElementById('compare-divider').style.left)") == pytest.approx(box["width"] * 0.3, abs=2)
    page.click("#compare-close")
    for button, panel in (("#search-button", "#search-panel"), ("#help-button", "#help-panel"),
                          ("#sources-button", "#sources-panel"), ("#check-button", "#check-panel"),
                          ("#site-name", "#picker-panel")):
        page.click(button)
        expect(page.locator(panel)).to_be_visible()
        assert no_sideways_scroll()
        page.click(f"{panel} [data-close]" if panel != "#search-panel" else "#search-close")
    expect_disclaimer_on_screen(page)


@pytest.mark.xfail(reason="Known gap for the owner: Leaflet's small credit link in the map's corner is under 44 px.", strict=True)
def test_tc042_attribution_link_is_big_enough(app):
    assert [row for row in controls_too_small(app) if "Leaflet" in row["name"]] == []


def swatch_colors(page):
    """Read the color each legend swatch has on screen right now."""
    colors = []
    for swatch in page.locator("#legend-rows .swatch").all():
        image = Image.open(io.BytesIO(swatch.screenshot())).convert("RGB")
        colors.append(image.getpixel((image.width // 2, image.height // 2)))
    return colors


@pytest.mark.parametrize("deficiency", ["deuteranopia", "protanopia"])
def test_tc043_colors_stay_apart(app, deficiency):
    session = app.context.new_cdp_session(app)
    session.send("Emulation.setEmulatedVisionDeficiency", {"type": deficiency})
    low, high = swatch_colors(app)
    distance = sum((a - b) ** 2 for a, b in zip(low, high)) ** 0.5
    assert distance > 40, f"{low} and {high} are too close"
    for row in app.locator("#legend-rows li").all_inner_texts():
        assert "Confidence:" in row


@pytest.mark.skip(reason=NO_CHANNELS)
@pytest.mark.parametrize("case", ["TC-044", "TC-045", "TC-046", "TC-047"])
def test_tc044_to_047_channels(case):
    pass

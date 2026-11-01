"""TC-089 to TC-092: the Field map design in the browser (F-22)."""
import numpy as np
import pytest
from PIL import Image
from playwright.sync_api import expect

from .conftest import SITE, envelope, open_drawer_if_closed, prepare_page, read_data, wait_until_ready
from .test_accessibility import problems_on

pytestmark = pytest.mark.e2e

LATEST_PAIR = read_data("sites/mayon/pairs.json")[-1]["id"]
RELIEF_FILES = "**/sites/mayon/relief/**"
CREDIT = "Relief: Copernicus DEM GLO-30"


def open_at(page, site_url, width, height=800, **options):
    prepare_page(page, width=width, height=height, **options)
    page.goto(site_url)
    wait_until_ready(page)
    page.wait_for_selector("#channel-body .channel-row")


def switch_to_panama(page):
    page.click("#site-name")
    page.click("#picker-panel button:has-text('Panama')")
    expect(page.locator("#site-name")).to_contain_text("Panama")
    wait_until_ready(page)


def view_inside_relief(page):
    """Is every edge of the view inside the relief's bounds? The map rounds to whole pixels, so allow 2."""
    site = read_data("sites.json")[0]
    view = page.evaluate("""() => { const b = testMap.getBounds();
      return [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()]; }""")
    room = 2 * (view[2] - view[0]) / page.evaluate("testMap.getSize().x")
    return (view[0] >= site["relief_bounds_west"] - room and view[1] >= site["relief_bounds_south"] - room
            and view[2] <= site["relief_bounds_east"] + room and view[3] <= site["relief_bounds_north"] + room)


@pytest.mark.parametrize("width,height", [(360, 740), (1280, 800), (2560, 1440)])
def test_tc089_no_plain_band_at_the_lowest_zoom_or_any_corner(page, site_url, width, height):
    open_at(page, site_url, width, height)
    page.evaluate("testMap.setZoom(testMap.getMinZoom(), { animate: false })")
    assert view_inside_relief(page)
    # Keep the map at the lowest zoom and try to drag it past each corner.
    for lat, lon in ((20, 100), (20, 140), (0, 100), (0, 140)):
        page.evaluate("([lat, lon]) => testMap.panTo([lat, lon], { animate: false })", [lat, lon])
        page.wait_for_timeout(500)  # the map slides back inside its limits
        assert view_inside_relief(page), (lat, lon)


def test_tc089_mayon_uses_its_relief_and_credits_it(page, site_url):
    outside = []
    page.on("request", lambda request: outside.append(request.url) if "arcgisonline" in request.url else None)
    relief = []
    page.on("response", lambda response: relief.append(response.status) if "/relief/" in response.url else None)
    open_at(page, site_url, 1280)
    page.wait_for_function("document.querySelectorAll('.leaflet-tile-loaded').length > 0")
    assert relief and set(relief) == {200}
    assert not outside
    expect(page.locator(".leaflet-control-attribution")).to_contain_text(CREDIT)
    expect(page.locator(".leaflet-control-attribution")).not_to_contain_text("Esri")


def test_tc089_tiles_fail_but_the_lines_stay(page, site_url):
    prepare_page(page)
    page.route(RELIEF_FILES, lambda route: route.abort())
    page.goto(site_url)
    wait_until_ready(page)
    expect(page.locator("#background-notice")).to_be_visible()
    expect(page.locator("path.line-ring")).to_have_count(1)
    expect(page.locator("path.line-coast")).to_have_count(1)


def test_tc089_panama_keeps_its_imagery_and_its_line_colours(page, site_url):
    open_at(page, site_url, 1280)
    switch_to_panama(page)
    expect(page.locator(".leaflet-control-attribution")).to_contain_text("Esri")
    expect(page.locator(".leaflet-control-attribution")).not_to_contain_text(CREDIT)
    assert not page.evaluate("document.body.classList.contains('relief-map')")
    stroke = page.evaluate("getComputedStyle(document.querySelector('path.line-coast')).stroke")
    assert stroke == "rgb(125, 211, 252)"  # the imagery colour, #7dd3fc


def test_tc089_the_lines_change_colour_on_the_relief(app):
    stroke = app.evaluate("getComputedStyle(document.querySelector('path.line-ring')).stroke")
    assert stroke == "rgb(106, 27, 106)"  # the deep purple of the Field map


@pytest.mark.parametrize("width,height", [(360, 740), (1280, 800)])
def test_tc090_the_list_opens_without_taking_the_focus(page, site_url, width, height):
    open_at(page, site_url, width, height)
    expect(page.locator("#channel-panel")).to_be_visible()
    expect(page.locator("#channel-body .channel-row")).to_have_count(4)
    assert page.evaluate("document.activeElement === document.body")
    assert problems_on(page) == []


def test_tc090_on_a_desktop_the_panel_is_beside_the_map(page, site_url):
    open_at(page, site_url, 1280)
    map_box = page.locator("#map").bounding_box()
    for part in ("#channel-panel", "#panel"):
        assert page.locator(part).bounding_box()["x"] >= map_box["x"] + map_box["width"]
    assert map_box["height"] > 600
    assert page.locator(".side").evaluate("(side) => side.getBoundingClientRect().bottom <= innerHeight")
    assert page.evaluate("document.documentElement.scrollHeight <= innerHeight")


def test_tc090_on_a_phone_closing_the_list_brings_the_pass_controls_back(page, site_url):
    open_at(page, site_url, 360, 740)
    expect(page.locator("#pair-list")).to_be_hidden()
    page.click("#channel-close")
    expect(page.locator("#pair-list")).to_be_visible()
    expect(page.locator("#channels-button")).to_be_focused()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert problems_on(page) == []


def test_tc090_the_sites_own_font_is_used_and_nothing_loads_from_a_font_host(page, site_url):
    outside = []
    page.on("request", lambda request: outside.append(request.url) if "font" in request.url and site_url not in request.url else None)
    open_at(page, site_url, 1280)
    page.evaluate("document.fonts.ready")
    assert page.evaluate("document.fonts.check('600 16px \"IBM Plex Sans\"')")
    assert "IBM Plex Sans" in page.evaluate("getComputedStyle(document.body).fontFamily")
    assert "IBM Plex Mono" in page.locator(".channel-row-area").first.evaluate("(area) => getComputedStyle(area).fontFamily")
    assert not outside


def flagged_pixels(pair_id):
    with Image.open(SITE / "data" / "sites" / "mayon" / "pairs" / pair_id / "new_material.png") as image:
        return int(np.count_nonzero(np.array(image.convert("RGBA"))[..., 3] >= 128))


def wait_for_marks(page):
    page.wait_for_selector(".radar-marks")
    page.wait_for_timeout(100)


@pytest.mark.parametrize("width,height", [(360, 740), (1280, 800)])
def test_tc091_one_mark_for_each_flagged_cell_in_the_image(page, site_url, width, height):
    open_at(page, site_url, width, height)
    wait_for_marks(page)
    assert int(page.locator(".radar-marks").get_attribute("data-cells")) == flagged_pixels(LATEST_PAIR)


@pytest.mark.parametrize("zoom,smallest", [(11, 1), (12, 2), (14, 3)])
def test_tc091_a_mark_never_goes_under_the_minimum(app, zoom, smallest):
    wait_for_marks(app)
    app.evaluate("(zoom) => testMap.setView([13.2572, 123.6856], zoom, { animate: false })", zoom)
    app.wait_for_timeout(100)
    assert float(app.locator(".radar-marks").get_attribute("data-mark-width")) >= smallest


def test_tc091_a_mark_has_its_class_colour_inside_a_darker_edge(app):
    wait_for_marks(app)
    # Look along each row of the canvas for a faint dark edge with a solid, brighter mark beside it.
    found = app.evaluate("""() => {
      const canvas = document.querySelector('.radar-marks');
      const { data, width, height } = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height);
      for (let i = 0; i < width * height * 4 - 4; i += 4) {
        const edge = data[i + 3] > 0 && data[i + 3] < 200 && data[i] < 90;
        const next = data[i + 7] === 255 && data[i + 4] > 180;
        if (edge && next) return [data[i + 4], data[i + 5], data[i + 6]];
      }
      return null;
    }""")
    assert found is not None


def painted_km2(page):
    """How much ground the marks cover on screen, counting only solid colour."""
    return page.evaluate("""() => {
      const canvas = document.querySelector('.radar-marks');
      const { data } = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height);
      let solid = 0;
      for (let i = 3; i < data.length; i += 4) if (data[i] > 200) solid += 1;
      const middle = testMap.getSize().divideBy(2);
      const metres = testMap.distance(testMap.containerPointToLatLng(middle), testMap.containerPointToLatLng(middle.add([1, 0])));
      return solid * metres * metres / 1e6;
    }""")


def test_tc091_at_the_default_zoom_the_marks_stay_small_and_visible(app):
    wait_for_marks(app)
    assert 2 < painted_km2(app) < 15  # it was 29 km² at 5 px, for 0.75 km² of flagged ground


def test_tc091_the_legend_says_small_spots_are_drawn_larger(app):
    expect(app.locator(".legend")).to_contain_text("Small spots are drawn larger than life so they can be seen. The areas don't change.")


def test_tc091_no_marks_with_the_layer_off(app):
    wait_for_marks(app)
    app.uncheck("#layer-toggle")
    expect(app.locator(".radar-marks")).to_have_count(0)
    app.check("#layer-toggle")
    expect(app.locator(".radar-marks")).to_have_count(1)


def test_tc091_no_marks_in_the_compare_view(app):
    wait_for_marks(app)
    open_drawer_if_closed(app)
    app.click("#compare-button")
    app.wait_for_selector("#compare-view:not([hidden])")
    expect(app.locator(".radar-marks")).to_be_hidden()
    app.click("#compare-close")
    expect(app.locator(".radar-marks")).to_be_visible()


def test_tc091_the_marks_follow_the_selected_pair(app):
    wait_for_marks(app)
    pairs = read_data("sites/mayon/pairs.json")
    first = pairs[0]["id"]
    app.select_option("#pair-list", first)
    app.wait_for_selector(f'.leaflet-radar-pane img[src*="{first}"]')
    assert int(app.locator(".radar-marks").get_attribute("data-cells")) == flagged_pixels(first)
    expect(app.locator(".radar-marks")).to_have_count(1)


def current_bar_state(page):
    """Which bars are marked as current, the pass on the map, and whether the bar is in view."""
    return page.evaluate("""() => {
      const bars = [...document.querySelectorAll('.channel-bar[aria-current]')];
      const scroller = document.getElementById('channel-panel');
      const box = bars[0].getBoundingClientRect();
      const inView = box.top >= document.querySelector('.channel-header').getBoundingClientRect().bottom - 1
        && box.bottom <= scroller.getBoundingClientRect().bottom + 1;
      return { pairs: bars.map((bar) => bar.dataset.pair), inView,
               shown: document.querySelector('.leaflet-radar-pane img').src.split('/').slice(-2)[0] };
    }""")


def expect_bar_matches_the_map(page, pair=None):
    """Check the bar against the map, once the pass in the list (or `pair`) has reached the map."""
    wanted = pair or page.locator("#pair-list").input_value()
    page.wait_for_selector(f'.leaflet-radar-pane img[src*="{wanted}"]')
    page.wait_for_selector(f'.channel-bar[aria-current][data-pair="{wanted}"]')
    state = current_bar_state(page)
    assert state["shown"] == wanted
    assert state["pairs"] == [state["shown"]]
    assert state["inView"]


@pytest.mark.parametrize("width,height", [(360, 740), (1280, 800)])
def test_tc093_the_highlighted_bar_is_the_pass_on_the_map_and_in_view(page, site_url, width, height):
    open_at(page, site_url, width, height)
    page.wait_for_selector(".radar-marks")
    page.locator("#channel-body .channel-row", has_text="Mi-isi").click()
    expect_bar_matches_the_map(page)
    for bar in (page.locator(".channel-bar").nth(2), page.locator(".channel-bar").last):
        pair = bar.get_attribute("data-pair")
        bar.click()
        expect_bar_matches_the_map(page, pair)


def test_tc093_the_bar_follows_the_pass_buttons(app):
    app.locator("#channel-body .channel-row", has_text="Mi-isi").click()
    expect_bar_matches_the_map(app)
    latest = current_bar_state(app)["shown"]
    for _ in range(4):
        button = app.locator("#previous").bounding_box()
        app.click("#previous")
        expect_bar_matches_the_map(app)
        assert app.locator("#previous").bounding_box()["y"] == pytest.approx(button["y"], abs=1)  # it stays under the finger
    assert current_bar_state(app)["shown"] != latest


def test_tc093_the_bar_under_the_pointer_doesnt_look_selected(app):
    app.locator("#channel-body .channel-row", has_text="Mi-isi").click()
    expect_bar_matches_the_map(app)
    app.locator(".channel-bar").first.hover()
    backgrounds = app.evaluate("""[...document.querySelectorAll('.channel-bar:not([aria-current])')]
      .map((bar) => getComputedStyle(bar).backgroundColor)""")
    assert set(backgrounds) == {"rgba(0, 0, 0, 0)"}


COURTS = [
    (0, "0 basketball courts"),
    (0.0001, "less than 1 basketball court"),
    (0.00042, "about 1 basketball court"),
    (0.03, "about 71 basketball courts"),
    (0.12, "about 286 basketball courts"),
    (1.5, "about 3,571 basketball courts"),
]


def serve_area(page, area):
    rows = [row | {"flagged_area_km2": area, "checked_area_km2": 0 if area is None else 1.0} for row in read_data("sites/mayon/channel_areas.json")]
    page.route("**/sites/mayon/channel_areas.json", lambda route: route.fulfill(body=envelope(rows), content_type="application/json"))


@pytest.mark.parametrize("area,words", COURTS)
def test_tc092_the_list_and_the_bars_show_km2_and_courts(page, site_url, area, words):
    prepare_page(page)
    serve_area(page, area)
    page.goto(site_url)
    wait_until_ready(page)
    row = page.locator("#channel-body .channel-row").first
    expect(row).to_contain_text(f"{area:.3f} km²")
    expect(row.locator(".channel-row-courts")).to_have_text(words)
    row.click()
    bar = page.locator("#channel-body .channel-bar").first
    expect(bar).to_contain_text(f"{area:.3f} km²")
    expect(bar.locator(".channel-bar-courts")).to_have_text(words)


def test_tc092_no_radar_data_has_no_comparison(page, site_url):
    prepare_page(page)
    serve_area(page, None)
    page.goto(site_url)
    wait_until_ready(page)
    row = page.locator("#channel-body .channel-row").first
    expect(row).to_contain_text("No radar data")
    expect(row.locator(".channel-row-courts")).to_have_count(0)
    row.click()
    expect(page.locator("#channel-body .channel-bar-courts")).to_have_count(0)


def test_tc092_both_screens_state_the_courts_size(app):
    size = "1 basketball court = 28 × 15 m = 420 m²."
    expect(app.locator("#channel-panel")).to_contain_text(size)
    app.locator("#channel-body .channel-row").first.click()
    expect(app.locator("#channel-panel")).to_contain_text(size)


@pytest.mark.parametrize("width,height", [(360, 740), (1280, 800)])
def test_tc092_the_channel_view_passes_axe_with_courts(page, site_url, width, height):
    open_at(page, site_url, width, height)
    page.locator("#channel-body .channel-row").first.click()
    assert problems_on(page) == []

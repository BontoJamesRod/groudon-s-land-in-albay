"""TC-089 to TC-092: the Field map design in the browser (F-22)."""
import re

import numpy as np
import pytest
from PIL import Image
from playwright.sync_api import expect

from .conftest import go_to_panama, SITE, TINY_PNG, envelope, latest_dates, latest_pair, open_drawer_if_closed, prepare_page, read_data, wait_until_ready
from .test_accessibility import problems_on

pytestmark = pytest.mark.e2e

LATEST_PAIR = latest_pair()["id"]
# A quiet pair that stays published. Its small flagged area is what these marks are measured against.
QUIET_PAIR = "mayon_A111F008_20261007_20261019"
RELIEF_FILES = "**/sites/mayon/relief/**"
CREDIT = "Relief: Copernicus DEM GLO-30"


def open_at(page, site_url, width, height=800, **options):
    prepare_page(page, width=width, height=height, **options)
    page.goto(site_url)
    wait_until_ready(page)
    page.wait_for_selector("#channel-body .channel-row")


def switch_to_panama(page):
    go_to_panama(page)
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
    page.on("request", lambda request: outside.append(request.url) if "eox.at" in request.url else None)
    relief = []
    page.on("response", lambda response: relief.append(response.status) if "/relief/" in response.url else None)
    open_at(page, site_url, 1280)
    page.wait_for_function("document.querySelectorAll('.leaflet-tile-loaded').length > 0")
    assert relief and set(relief) == {200}
    assert not outside
    expect(page.locator(".leaflet-control-attribution")).to_contain_text(CREDIT)
    expect(page.locator(".leaflet-control-attribution")).not_to_contain_text("EOxCloudless")


def test_tc089_tiles_fail_but_the_lines_stay(page, site_url):
    prepare_page(page)
    page.route(RELIEF_FILES, lambda route: route.abort())
    page.goto(site_url)
    wait_until_ready(page)
    expect(page.locator("#background-notice")).to_be_visible()
    expect(page.locator("path.line-ring")).to_have_count(1)
    expect(page.locator("path.line-coast")).to_have_count(1)


def test_tc089_panama_opens_on_its_own_relief(page, site_url):
    relief = []
    page.on("response", lambda response: relief.append(response.url) if "/sites/panama/relief/" in response.url else None)
    open_at(page, site_url, 1280)
    switch_to_panama(page)
    page.wait_for_function("document.querySelectorAll('.leaflet-tile-loaded').length > 0")
    expect(page.locator(".leaflet-control-attribution")).to_contain_text(CREDIT)
    assert page.evaluate("document.body.classList.contains('relief-map')")
    assert relief


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


def test_tc090_on_a_phone_the_closed_sheet_has_the_pass_and_the_list(page, site_url):
    open_at(page, site_url, 360, 740)
    expect(page.locator("#pair-list")).to_be_visible()
    expect(page.locator("#channel-body .channel-row").first).to_be_visible()
    assert page.evaluate("document.activeElement === document.body")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert problems_on(page) == []


def test_tc090_the_sites_own_font_is_used_and_nothing_loads_from_a_font_host(page, site_url):
    outside = []
    page.on("request", lambda request: outside.append(request.url) if "font" in request.url and site_url not in request.url else None)
    open_at(page, site_url, 1280)
    page.evaluate("document.fonts.ready")
    assert page.evaluate("document.fonts.check('600 16px \"IBM Plex Sans\"')")
    assert "IBM Plex Sans" in page.evaluate("getComputedStyle(document.body).fontFamily")
    # The calm design uses Plex Sans only, with numbers of equal width so they line up (FR-092).
    area = page.locator(".channel-row-area").first
    assert "IBM Plex Sans" in area.evaluate("(node) => getComputedStyle(node).fontFamily")
    assert area.evaluate("(node) => getComputedStyle(node).fontVariantNumeric") == "tabular-nums"
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
    app.select_option("#pair-list", QUIET_PAIR)
    app.wait_for_function(f"document.querySelector('.radar-marks')?.dataset.cells === '{flagged_pixels(QUIET_PAIR)}'")
    wait_for_marks(app)
    assert 2 < painted_km2(app) < 15  # it was 29 km² at 5 px, for 0.75 km² of flagged ground


def test_tc091_the_legend_says_small_spots_are_drawn_larger(app):
    expect(app.locator(".area-line .info-popover")).to_contain_text("Small spots are drawn larger than life so they can be seen. The areas don't change.")


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
      const scroller = document.getElementById('panel');
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
    pairs = [pair["id"] for pair in read_data("sites/mayon/pairs.json")]
    for pair in reversed(pairs[-5:-1]):
        # The channel's page has its own ‹ and ›, which work like the pass buttons it hides.
        button = app.locator("#channel-previous").bounding_box()
        app.click("#channel-previous")
        expect_bar_matches_the_map(app, pair)
        # The list moves last, once the pass has loaded, and the next press counts from it.
        expect(app.locator("#pair-list")).to_have_value(pair)
        assert app.locator("#channel-previous").bounding_box()["y"] == pytest.approx(button["y"], abs=1)  # it stays under the finger


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


PRESSED = '.basemap-button[aria-pressed="true"]'
SATELLITE = '.basemap-button:has-text("Satellite")'
RELIEF = '.basemap-button:has-text("Relief")'
IMAGERY = "EOxCloudless"


def stroke_of(page, line):
    return page.evaluate(f"getComputedStyle(document.querySelector('path.{line}')).stroke")


def label_colours(page, label):
    return page.evaluate(f"""(() => {{ const style = getComputedStyle(document.querySelector('.{label}'));
      return [style.color, style.backgroundColor]; }})()""")


@pytest.mark.parametrize("width,height", [(360, 740), (1280, 800)])
def test_tc094_relief_first_with_44_px_buttons_saying_which_is_on(page, site_url, width, height):
    open_at(page, site_url, width, height)
    expect(page.locator(PRESSED)).to_have_text("Relief")
    expect(page.locator(SATELLITE)).to_have_attribute("aria-pressed", "false")
    for button in (RELIEF, SATELLITE):
        box = page.locator(button).bounding_box()
        assert box["width"] >= 44 and box["height"] >= 44
    expect(page.locator(".basemap-switcher")).to_have_attribute("role", "group")


def test_tc094_the_buttons_work_from_the_keyboard(app):
    app.locator(SATELLITE).focus()
    app.keyboard.press("Enter")
    expect(app.locator(PRESSED)).to_have_text("Satellite")
    app.locator(RELIEF).focus()
    app.keyboard.press("Space")
    expect(app.locator(PRESSED)).to_have_text("Relief")


def test_tc094_a_tap_on_a_button_doesnt_open_the_readout(app):
    app.click(SATELLITE)
    expect(app.locator("#readout-card")).to_be_hidden()


def test_tc094_the_choice_stays_after_a_reload_and_a_change_of_site(app):
    app.click(SATELLITE)
    app.reload()
    wait_until_ready(app)
    expect(app.locator(PRESSED)).to_have_text("Satellite")
    assert not app.evaluate("document.body.classList.contains('relief-map')")
    switch_to_panama(app)
    expect(app.locator(PRESSED)).to_have_text("Satellite")
    expect(app.locator(".basemap-switcher")).to_have_count(1)
    expect(app.locator(".leaflet-control-attribution")).to_contain_text(IMAGERY)


def test_tc094_blocked_storage_opens_on_relief_and_can_still_switch(page, site_url):
    page.add_init_script("""Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked'); } });""")
    errors = []
    page.on("pageerror", lambda problem: errors.append(problem))
    open_at(page, site_url, 1280)
    expect(page.locator(PRESSED)).to_have_text("Relief")
    page.click(SATELLITE)
    expect(page.locator(PRESSED)).to_have_text("Satellite")
    assert not errors


def test_tc095_imagery_is_only_requested_on_satellite_and_its_credit_follows(page, site_url):
    asked = []
    prepare_page(page)
    page.on("request", lambda request: asked.append(request.url) if "tiles.maps.eox.at" in request.url else None)
    page.goto(site_url)
    wait_until_ready(page)
    credits_ = page.locator(".leaflet-control-attribution")
    assert not asked
    expect(credits_).not_to_contain_text(IMAGERY)
    page.click(SATELLITE)
    expect(credits_).to_contain_text("EOxCloudless by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2024)")
    page.wait_for_function("document.querySelectorAll('.leaflet-tile[src*=\"eox.at\"]').length > 0")
    assert asked and all("s2cloudless-2024_3857" in url for url in asked)
    page.click(RELIEF)
    expect(credits_).not_to_contain_text(IMAGERY)
    expect(page.locator('.leaflet-tile[src*="eox.at"]')).to_have_count(0)


def test_tc095_the_colours_follow_the_background(app):
    relief = {line: stroke_of(app, line) for line in ("line-ring", "line-channel", "line-coast")}
    assert relief["line-ring"] == "rgb(106, 27, 106)" and relief["line-channel"] == "rgb(11, 95, 165)"
    assert label_colours(app, "town-label")[0] == "rgb(11, 15, 20)"
    app.click(SATELLITE)
    assert stroke_of(app, "line-ring") == "rgb(251, 146, 60)"  # orange
    assert stroke_of(app, "line-channel") == "rgb(34, 211, 238)"  # bright cyan
    colour, box = label_colours(app, "town-label")
    assert colour == "rgb(255, 255, 255)" and box == "rgba(31, 35, 40, 0.85)"  # white on a dark box
    app.click(RELIEF)
    assert stroke_of(app, "line-ring") == relief["line-ring"]


def test_tc095_marks_stay_on_both_backgrounds(app):
    wait_for_marks(app)
    relief_cells = app.locator(".radar-marks").get_attribute("data-cells")
    relief_painted = painted_km2(app)
    assert app.evaluate("getComputedStyle(document.querySelector('.radar-marks')).filter") == "none"
    app.click(SATELLITE)
    assert app.locator(".radar-marks").get_attribute("data-cells") == relief_cells
    assert painted_km2(app) == pytest.approx(relief_painted)
    assert "drop-shadow" in app.evaluate("getComputedStyle(document.querySelector('.radar-marks')).filter")


def test_tc095_slow_imagery_shows_a_preview_and_a_count(page, site_url):
    prepare_page(page, tiles="none")
    held = []

    def answer(route):
        # Zoom 10 answers at once. Anything sharper waits, as it can on the real service.
        if "/g/10/" in route.request.url:
            route.fulfill(body=TINY_PNG, content_type="image/png")
        else:
            held.append(route)
    page.route("https://tiles.maps.eox.at/**", answer)
    page.goto(site_url)
    wait_until_ready(page)
    page.click(SATELLITE)
    notice = page.locator("#background-notice")
    expect(notice).to_be_visible()
    page.wait_for_selector('.leaflet-tile-loaded[src*="/g/10/"]')
    # Only a few tiles are needed for the preview, far fewer than the sharp ones.
    expect(notice).to_have_text(re.compile(r"^Loading satellite imagery: \d+ tiles to go$"))
    page.wait_for_function("document.querySelectorAll('.leaflet-tile[src*=\"/g/12/\"]').length > 0")
    previews = page.locator('.leaflet-tile[src*="/g/10/"]').count()
    assert 0 < previews < page.locator('.leaflet-tile[src*="/g/12/"]').count()
    for route in list(held):
        route.fulfill(body=TINY_PNG, content_type="image/png")
    expect(notice).to_be_hidden()


def tiles_to_go(page):
    return int(re.search(r"(\d+) tile", page.locator("#background-notice").inner_text()).group(1))


def test_tc095_the_sharp_tiles_wait_for_the_preview(page, site_url):
    prepare_page(page, tiles="none")
    held = []
    page.route("https://tiles.maps.eox.at/**", lambda route: held.append(route))
    page.goto(site_url)
    wait_until_ready(page)
    page.click(SATELLITE)
    page.wait_for_timeout(500)
    assert held and all("/g/10/" in route.request.url for route in held)
    for route in list(held):
        route.fulfill(body=TINY_PNG, content_type="image/png")
    page.wait_for_function("document.querySelectorAll('.leaflet-tile[src*=\"/g/12/\"]').length > 0")


def test_tc095_moving_the_map_doesnt_inflate_the_count(page, site_url):
    prepare_page(page, tiles="none")
    page.route("https://tiles.maps.eox.at/**", lambda route: None)  # never answers
    page.goto(site_url)
    wait_until_ready(page)
    page.click(SATELLITE)
    expect(page.locator("#background-notice")).to_be_visible()
    for zoom in (13, 11, 14, 12, 13, 12, 13, 12):
        page.evaluate("(zoom) => testMap.setZoom(zoom, { animate: false })", zoom)
        page.wait_for_timeout(100)
    on_screen = page.evaluate("document.querySelectorAll('.leaflet-tile[src*=\"eox.at\"]:not(.leaflet-tile-loaded)').length")
    assert tiles_to_go(page) == on_screen
    assert on_screen < 100


def test_tc095_opening_on_a_saved_satellite_counts_only_whats_on_the_map(page, site_url):
    prepare_page(page, tiles="none")
    page.route("https://tiles.maps.eox.at/**", lambda route: None)  # never answers
    page.add_init_script("localStorage.setItem('mayon-radar-basemap', 'satellite')")
    page.goto(site_url)
    wait_until_ready(page)
    expect(page.locator(PRESSED)).to_have_text("Satellite")
    page.wait_for_timeout(300)
    assert tiles_to_go(page) == page.evaluate("document.querySelectorAll('.leaflet-tile[src*=\"eox.at\"]:not(.leaflet-tile-loaded)').length")


def test_tc095_going_back_to_relief_clears_the_count(page, site_url):
    prepare_page(page, tiles="none")
    page.route("https://tiles.maps.eox.at/**", lambda route: None)  # never answers
    page.goto(site_url)
    wait_until_ready(page)
    page.click(SATELLITE)
    expect(page.locator("#background-notice")).to_be_visible()
    page.click(RELIEF)
    expect(page.locator("#background-notice")).to_be_hidden()


def test_tc095_failed_imagery_leaves_the_relief_and_says_so(page, site_url):
    prepare_page(page, tiles="none")
    page.route("https://tiles.maps.eox.at/**", lambda route: route.abort())
    page.goto(site_url)
    wait_until_ready(page)
    expect(page.locator("#background-notice")).to_be_hidden()
    page.click(SATELLITE)
    expect(page.locator("#background-notice")).to_have_text("Satellite map unavailable. Showing the relief map.")
    assert page.locator('.leaflet-tile[src*="/relief/"]').count() > 0
    page.click(RELIEF)
    expect(page.locator("#background-notice")).to_be_hidden()


@pytest.mark.parametrize("width,height", [(360, 740), (1280, 800)])
def test_tc095_axe_passes_on_satellite(page, site_url, width, height):
    open_at(page, site_url, width, height)
    page.click(SATELLITE)
    assert problems_on(page) == []
    page.locator("#channel-body .channel-row").first.click()
    assert problems_on(page) == []


LABEL = ".product-label"
LATEST_LABEL = "NISAR {} · before {} · after {}".format(
    "GCOV + GUNW" if latest_pair()["coherence_used"] else "GCOV", *latest_dates())
PAIR_WITHOUT_COHERENCE = "mayon_A111F008_20260820_20260901"


def assert_label_is_clear(page):
    """The label is on screen, inside the map, readable, and doesn't touch the credits."""
    label = page.locator(LABEL).bounding_box()
    area = page.locator("#map").bounding_box()
    credits = page.locator(".leaflet-control-attribution").bounding_box()
    assert label["x"] >= area["x"] and label["x"] + label["width"] <= area["x"] + area["width"]
    assert label["y"] >= area["y"]
    assert label["y"] + label["height"] <= credits["y"]
    assert page.evaluate("parseFloat(getComputedStyle(document.querySelector('.product-label')).fontSize)") >= 12


def test_tc096_the_label_names_the_products_and_dates(app):
    expect(app.locator(LABEL)).to_have_text(LATEST_LABEL)
    expect(app.locator(LABEL)).to_be_visible()


def test_tc096_a_pair_without_coherence_names_gcov_alone(app):
    app.select_option("#pair-list", PAIR_WITHOUT_COHERENCE)
    expect(app.locator(LABEL)).to_have_text(re.compile(r"^NISAR GCOV · before .+ · after .+$"))
    expect(app.locator(LABEL)).not_to_contain_text("GUNW")


def test_tc096_the_label_stays_while_compare_is_open(app):
    app.click("#compare-button")
    expect(app.locator("#compare-view")).to_be_visible()
    box = app.locator(LABEL).bounding_box()
    # The label itself lets taps through, so ask what's drawn there with that switched off for a moment.
    on_top = app.evaluate("""([x, y]) => {
      const label = document.querySelector('.product-label');
      label.style.pointerEvents = 'auto';
      const found = document.elementFromPoint(x, y);
      label.style.pointerEvents = '';
      return found === label;
    }""", [box["x"] + box["width"] / 2, box["y"] + box["height"] / 2])
    assert on_top


@pytest.mark.parametrize("width, height", [(360, 640), (360, 740), (390, 844), (1280, 500), (1280, 800)])
@pytest.mark.parametrize("background", ["Relief", "Satellite"])
def test_tc096_the_label_is_clear_of_the_credits(page, site_url, width, height, background):
    prepare_page(page, width=width, height=height)
    page.goto(site_url)
    wait_until_ready(page)
    page.click(f'.basemap-button:has-text("{background}")')
    expect(page.locator(LABEL)).to_have_text(LATEST_LABEL)
    assert_label_is_clear(page)


def test_tc096_the_label_is_clear_on_panama_on_a_phone(page, site_url):
    prepare_page(page, width=360, height=740)
    page.goto(site_url)
    wait_until_ready(page)
    go_to_panama(page)
    expect(page.locator(LABEL)).to_have_text("NISAR GCOV + GUNW · before Sep 27, 2026 · after Oct 9, 2026")
    assert_label_is_clear(page)


def test_tc096_a_tap_on_the_label_reaches_the_map(app):
    box = app.locator(LABEL).bounding_box()
    app.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    expect(app.locator("#readout-card")).to_be_visible()


def test_tc096_a_pair_that_fails_keeps_the_label_of_the_pair_on_screen(page, site_url):
    prepare_page(page)
    page.route(f"**/{PAIR_WITHOUT_COHERENCE}/pair.json", lambda route: route.abort())
    page.goto(site_url)
    wait_until_ready(page)
    page.select_option("#pair-list", PAIR_WITHOUT_COHERENCE)
    expect(page.locator("#timeline-message")).not_to_be_empty()
    expect(page.locator(LABEL)).to_have_text(LATEST_LABEL)


@pytest.mark.parametrize("height", [640, 740, 844])
@pytest.mark.parametrize("background", ["Relief", "Satellite"])
def test_tc096_the_label_is_clear_of_the_map_buttons_with_the_drawer_open(page, site_url, height, background):
    prepare_page(page, width=360, height=height)
    page.goto(site_url)
    wait_until_ready(page)
    page.click(f'.basemap-button:has-text("{background}")')
    open_drawer_if_closed(page)
    expect(page.locator(LABEL)).to_have_text(LATEST_LABEL)
    page.wait_for_timeout(400)  # the drawer slides open, and the map shrinks with it
    label = page.locator(LABEL).bounding_box()
    for control in (".basemap-switcher", ".leaflet-control-zoom"):
        box = page.locator(control).bounding_box()
        assert box["y"] + box["height"] <= label["y"]

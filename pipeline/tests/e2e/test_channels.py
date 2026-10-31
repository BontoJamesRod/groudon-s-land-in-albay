"""Browser tests for channels (F-19) and the Channel timeline (F-20). Each test name carries its TC number."""
import json

import numpy as np
import pytest
from playwright.sync_api import expect
from shapely import contains_xy
from shapely.geometry import shape

from .conftest import SITE, envelope, open_drawer_if_closed, prepare_page, read_data, wait_until_ready
from .test_accessibility import problems_on
from .test_mvp import card, controls_too_small, map_center, map_zoom, tap_at

pytestmark = pytest.mark.e2e

MAYON = SITE / "data" / "sites" / "mayon"
LATEST_PAIR = "mayon_A111F008_20261007_20261019"


def channels():
    return json.loads((MAYON / "channels.geojson").read_text(encoding="utf-8"))["features"]


def channel(name):
    return next(item for item in channels() if item["properties"]["name"] == name)


def latest_grid():
    """The latest pair's value grid, with each cell's longitude and latitude."""
    pair = read_data(f"sites/mayon/pairs/{LATEST_PAIR}/pair.json")
    layer = next(item for item in pair["layers"] if item["kind"] == "new_material")
    width, height = layer["grid_width"], layer["grid_height"]
    cells = np.fromfile(MAYON / "pairs" / LATEST_PAIR / "new_material.bin", dtype="uint8").reshape(height, width)
    lons = layer["bounds_west"] + (np.arange(width) + 0.5) * (layer["bounds_east"] - layer["bounds_west"]) / width
    lats = layer["bounds_north"] - (np.arange(height) + 0.5) * (layer["bounds_north"] - layer["bounds_south"]) / height
    return cells, *np.meshgrid(lons, lats)


def inside_strips():
    """Which grid cells are inside each channel's strip."""
    cells, lons, lats = latest_grid()
    return cells, lons, lats, {item["properties"]["name"]: contains_xy(shape(item["properties"]["strip_geometry"]), lons, lats) for item in channels()}


def a_flagged_cell_in(name):
    cells, lons, lats, strips = inside_strips()
    rows, columns = np.nonzero(np.isin(cells, (1, 2)) & strips[name])
    return float(lats[rows[0], columns[0]]), float(lons[rows[0], columns[0]])


def a_flagged_cell_outside_every_strip():
    cells, lons, lats, strips = inside_strips()
    rows, columns = np.nonzero(np.isin(cells, (1, 2)) & ~np.logical_or.reduce(list(strips.values())))
    return float(lats[rows[0], columns[0]]), float(lons[rows[0], columns[0]])


def a_quiet_cell_in(name):
    cells, lons, lats, strips = inside_strips()
    rows, columns = np.nonzero((cells == 0) & strips[name])
    return float(lats[rows[0], columns[0]]), float(lons[rows[0], columns[0]])


def test_tc044_each_channel_is_drawn_with_its_name(app):
    labels = app.locator(".channel-label").all_inner_texts()
    assert sorted(labels) == ["Basud", "Lidong", "Mi-isi", "Padang"]
    assert app.locator('.leaflet-overlay-pane path[stroke="#22d3ee"]').count() == 4


def test_tc044_tapping_a_line_lists_its_towns(app):
    lon, lat = channel("Mi-isi")["properties"]["checked_geometry"]["coordinates"][50]
    tap_at(app, lat, lon)
    expect(card(app).locator(".readout-place")).to_have_text("Mi-isi")
    expect(card(app)).to_contain_text("Towns along this channel: Daraga, Legazpi City")
    # The tap reads the spot too, and the line's click doesn't also count as a tap on the map.
    expect(card(app)).to_contain_text("Distance to summit:")
    expect(card(app)).to_contain_text("Radar passes:")
    expect(card(app).locator(".readout-place")).to_have_text("Mi-isi")


def test_tc044_the_layer_can_be_turned_off(app):
    expect(app.locator(".channel-label")).to_have_count(4)
    app.uncheck("#channel-toggle")
    expect(app.locator(".channel-label")).to_have_count(0)
    app.check("#channel-toggle")
    expect(app.locator(".channel-label")).to_have_count(4)


def test_tc045_a_flagged_spot_in_a_strip_names_the_channel(app):
    lat, lon = a_flagged_cell_in("Mi-isi")
    tap_at(app, lat, lon)
    expect(card(app)).to_contain_text("New material detected in or near Mi-isi")


def test_tc046_a_flagged_spot_away_from_every_strip(app):
    lat, lon = a_flagged_cell_outside_every_strip()
    tap_at(app, lat, lon)
    expect(card(app)).to_contain_text("Not in a named channel on this map")
    expect(card(app)).not_to_contain_text("in or near")


def test_a_quiet_spot_in_a_strip_says_nothing_about_new_material_in_it(app):
    lat, lon = a_quiet_cell_in("Basud")
    tap_at(app, lat, lon)
    expect(card(app)).to_contain_text("No new material detected")
    expect(card(app)).not_to_contain_text("in or near")
    expect(card(app)).not_to_contain_text("named channel")


def test_tc047_legend_and_data_sources_name_the_channel_sources(app):
    open_drawer_if_closed(app)
    legend = app.locator("#channel-sources")
    expect(legend).to_contain_text("PHIVOLCS")
    expect(legend).to_contain_text("OpenStreetMap")
    expect(legend).to_contain_text("ODbL")
    app.click("#sources-button")
    context = app.locator("#sources-panel h3:has-text('Context data') + ul")
    expect(context).to_contain_text("Channel names")
    expect(context).to_contain_text("Channel lines")
    expect(context).to_contain_text("ODbL")


def test_tc047_the_map_credits_openstreetmap(app):
    credit = app.locator(".leaflet-control-attribution")
    expect(credit).to_contain_text("OpenStreetMap contributors")
    expect(credit).to_contain_text("ODbL")
    assert credit.locator("a", has_text="OpenStreetMap").get_attribute("href") == "https://www.openstreetmap.org/copyright"


@pytest.mark.parametrize("status", [404, 500])
def test_a_channel_file_that_fails_leaves_the_rest_working(page, site_url, status):
    prepare_page(page)
    page.route("**/sites/mayon/channels.geojson", lambda route: route.fulfill(status=status, body="no"))
    page.goto(site_url)
    wait_until_ready(page)
    expect(page.locator("#channels-unavailable")).to_have_text("Channels unavailable")
    expect(page.locator("#channel-layer")).to_be_hidden()
    expect(page.locator(".channel-label")).to_have_count(0)
    lat, lon = a_flagged_cell_in("Mi-isi")
    tap_at(page, lat, lon)
    expect(card(page)).to_contain_text("Confidence:")
    expect(card(page)).not_to_contain_text("channel")
    expect(card(page)).not_to_contain_text("in or near")


def test_a_site_with_no_channel_data_says_nothing_about_channels(page, site_url):
    prepare_page(page)
    asked = []
    page.on("request", lambda request: asked.append(request.url))
    page.goto(site_url)
    wait_until_ready(page)
    page.click("#site-name")
    page.click("#picker-panel button:has-text('Azuero Peninsula')")
    expect(page.locator("#pair-list")).to_have_value("panama_D141F085_20260927_20261009")
    expect(page.locator("#channel-legend")).to_be_hidden()
    expect(page.locator(".channel-label")).to_have_count(0)
    expect(page.locator(".leaflet-control-attribution")).not_to_contain_text("OpenStreetMap")
    assert not any("panama/channels" in url for url in asked)


def area_rows(latest_areas):
    """Rows for every channel and pair. `latest_areas` sets the latest pair's flagged area by channel id."""
    rows = []
    for pair in read_data("sites/mayon/pairs.json"):
        for item in channels():
            area = latest_areas.get(item["id"], 0.02) if pair["id"] == LATEST_PAIR else 0.02
            rows.append({"id": f"{item['id']}__{pair['id']}", "site_id": "mayon", "channel_id": item["id"], "pair_id": pair["id"],
                         "flagged_area_km2": area, "checked_area_km2": 0 if area is None else 1.0,
                         "created_at": "2026-11-01T00:00:00Z", "updated_at": "2026-11-01T00:00:00Z"})
    return rows


def serve_areas(page, rows):
    page.route("**/sites/mayon/channel_areas.json", lambda route: route.fulfill(body=envelope(rows), content_type="application/json"))


def list_rows(page):
    return [" ".join(text.split()) for text in page.locator("#channel-body .channel-row").all_inner_texts()]


def test_tc064_the_channels_are_sorted_with_no_data_last(app):
    serve_areas(app, area_rows({"mayon_padang": 0.12, "mayon_miisi": 0.03, "mayon_basud": 0.03, "mayon_lidong": None}))
    app.click("#channels-button")
    expect(app.locator("#channel-body .channel-row")).to_have_count(4)
    assert list_rows(app) == ["Padang 0.12 km²", "Basud 0.03 km²", "Mi-isi 0.03 km²", "Lidong No radar data"]


def test_tc064_the_real_list_is_sorted_by_the_latest_pair(app):
    latest = {row["channel_id"]: row["flagged_area_km2"] for row in read_data("sites/mayon/channel_areas.json") if row["pair_id"] == LATEST_PAIR}
    names = {item["id"]: item["properties"]["name"] for item in channels()}
    wanted = sorted(latest, key=lambda channel_id: (-latest[channel_id], names[channel_id]))
    app.click("#channels-button")
    expect(app.locator("#channel-body .channel-row")).to_have_count(4)
    assert list_rows(app) == [f"{names[channel_id]} {latest[channel_id]:.2f} km²" for channel_id in wanted]
    expect(app.locator(".channel-lead")).to_have_text("Most changed first, since the last pass: Oct 8, 2026 to Oct 20, 2026, track 111")


def test_the_list_says_how_the_area_is_counted_and_what_is_left_out(app):
    app.click("#channels-button")
    panel = app.locator("#channel-panel")
    expect(panel).to_contain_text("200 m on each side of the line, within 10 km of the summit")
    expect(panel).to_contain_text("Only channels the project owner has checked are listed")


def empty_channels(page):
    body = json.dumps({"type": "FeatureCollection", "generated_at": "2026-11-01T00:00:00Z", "schema_version": "1.0", "features": []})
    page.route("**/sites/mayon/channels.geojson", lambda route: route.fulfill(body=body, content_type="application/json"))
    serve_areas(page, [])


def test_tc065_no_confirmed_channels(page, site_url):
    prepare_page(page)
    empty_channels(page)
    page.goto(site_url)
    wait_until_ready(page)
    # With no lines on the map, there's no channel legend and nothing to credit.
    expect(page.locator("#channel-layer")).to_be_hidden()
    expect(page.locator(".leaflet-control-attribution")).not_to_contain_text("OpenStreetMap")
    page.click("#channels-button")
    expect(page.locator("#channel-status")).to_have_text("No confirmed channels yet for this site")
    expect(page.locator("#channel-body .channel-row")).to_have_count(0)
    # Picking another pair must not wipe the message.
    page.select_option("#pair-list", "mayon_A111F008_20260703_20260715")
    expect(page.locator("#pair-list")).to_have_value("mayon_A111F008_20260703_20260715")
    expect(page.locator(".leaflet-radar-pane img[src*='20260703_20260715']")).to_have_count(1)
    expect(page.locator("#channel-status")).to_have_text("No confirmed channels yet for this site")


def test_the_list_says_so_when_a_site_has_no_pairs(page, site_url):
    prepare_page(page)
    empty = json.dumps({"data": [], "meta": {"generated_at": "2026-11-01T00:00:00Z", "schema_version": "1.0"}})
    page.route("**/sites/mayon/pairs.json", lambda route: route.fulfill(body=empty, content_type="application/json"))
    page.goto(site_url)
    expect(page.locator("#app-message")).to_have_text("No radar passes processed yet for this site")
    page.click("#channels-button")
    expect(page.locator("#channel-status")).to_have_text("No radar passes processed yet for this site")
    expect(page.locator("#channel-retry")).to_be_hidden()


def test_tc065_a_site_with_no_channel_data_has_no_button(app):
    expect(app.locator("#channels-button")).to_be_visible()
    app.click("#channels-button")
    expect(app.locator("#channel-panel")).to_be_visible()
    app.click("#site-name")
    app.click("#picker-panel button:has-text('Azuero Peninsula')")
    expect(app.locator("#pair-list")).to_have_value("panama_D141F085_20260927_20261009")
    expect(app.locator("#channels-button")).to_be_hidden()
    expect(app.locator("#channel-panel")).to_be_hidden()


def test_tc066_loading_then_the_list(app, slow_files):
    slow_files["channel_areas.json"] = 1.0
    app.click("#channels-button")
    expect(app.locator("#channel-status")).to_have_text("Loading channel changes…")
    expect(app.locator("#channel-title")).to_have_text("Channels")
    expect(app.locator("#channel-body .channel-row")).to_have_count(4)
    expect(app.locator("#channel-status")).to_have_text("")


def test_tc066_a_failed_load_offers_retry_and_the_map_stays(app):
    center, zoom = map_center(app), map_zoom(app)
    app.route("**/sites/mayon/channel_areas.json", lambda route: route.abort())
    app.click("#channels-button")
    expect(app.locator("#channel-status")).to_have_text("Couldn't load channel changes. Try again.")
    expect(app.locator("#channel-title")).to_have_text("Channels")
    expect(app.locator("#channel-retry")).to_be_visible()
    assert map_center(app) == pytest.approx(center, abs=0.05) and map_zoom(app) == zoom
    expect(app.locator(".leaflet-radar-pane img")).to_have_count(1)
    app.unroute("**/sites/mayon/channel_areas.json")
    app.click("#channel-retry")
    expect(app.locator("#channel-body .channel-row")).to_have_count(4)
    expect(app.locator("#channel-retry")).to_be_hidden()


def test_a_channel_file_that_failed_at_first_is_tried_again_from_the_list(page, site_url):
    prepare_page(page)
    page.route("**/sites/mayon/channels.geojson", lambda route: route.abort())
    page.goto(site_url)
    wait_until_ready(page)
    page.click("#channels-button")
    expect(page.locator("#channel-status")).to_have_text("Couldn't load channel changes. Try again.")
    page.unroute("**/sites/mayon/channels.geojson")
    page.click("#channel-retry")
    expect(page.locator("#channel-body .channel-row")).to_have_count(4)


@pytest.mark.parametrize("change", [{"channel_id": "mayon_nowhere"}, {"pair_id": "mayon_A111F008_20200101_20200113"}, {"flagged_area_km2": None}])
def test_a_broken_areas_file_gives_the_error_state(app, change):
    rows = area_rows({})
    rows[0].update(change)
    serve_areas(app, rows)
    app.click("#channels-button")
    expect(app.locator("#channel-status")).to_have_text("Couldn't load channel changes. Try again.")


def test_closing_the_list_gives_the_map_its_room_back(app):
    width = app.locator("#map").bounding_box()["width"]
    app.click("#channels-button")
    expect(app.locator("#channel-panel")).to_be_visible()
    assert app.locator("#map").bounding_box()["width"] < width
    assert app.evaluate("testMap.getSize().x") == pytest.approx(app.locator("#map").bounding_box()["width"], abs=1)
    app.click("#channel-close")
    expect(app.locator("#channel-panel")).to_be_hidden()
    assert app.locator("#map").bounding_box()["width"] == pytest.approx(width)
    assert app.evaluate("testMap.getSize().x") == pytest.approx(width, abs=1)


def open_phone(page, site_url):
    prepare_page(page, width=360, height=740)
    page.goto(site_url)
    wait_until_ready(page)


def test_the_list_fits_a_phone(page, site_url):
    open_phone(page, site_url)
    assert controls_too_small(page) == []
    assert page.locator("#map").bounding_box()["height"] >= 300
    page.click("#channels-button")
    expect(page.locator("#channel-body .channel-row")).to_have_count(4)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert controls_too_small(page) == []
    assert page.locator("#map").bounding_box()["height"] >= 200
    expect(page.locator("#panel")).to_be_hidden()
    expect(page.locator(".disclaimer")).to_be_in_viewport()
    page.click("#channel-close")
    expect(page.locator("#panel")).to_be_visible()


def test_axe_on_the_list(app):
    app.click("#channels-button")
    expect(app.locator("#channel-body .channel-row")).to_have_count(4)
    assert problems_on(app) == []


def test_axe_on_the_list_on_a_phone(page, site_url):
    open_phone(page, site_url)
    page.click("#channels-button")
    expect(page.locator("#channel-body .channel-row")).to_have_count(4)
    assert problems_on(page) == []


def open_channel(page, name):
    page.click("#channels-button")
    page.click(f"#channel-body .channel-row:has-text('{name}')")
    expect(page.locator("#channel-title")).to_have_text(name)


def bar_rows(page):
    return [" ".join(text.split()) for text in page.locator("#channel-body .channel-bar").all_inner_texts()]


def bar_widths(page):
    """Each bar's width as a share of its row's full width. None where there's no bar."""
    return page.evaluate("""[...document.querySelectorAll('#channel-body .channel-bar')].map((bar) => {
      const fill = bar.querySelector('.channel-bar-fill');
      return fill ? fill.getBoundingClientRect().width / bar.querySelector('.channel-bar-track').getBoundingClientRect().width : null;
    })""")


def strip_paths(page):
    return page.locator(".leaflet-channelStrip-pane path")


def test_tc067_one_bar_per_pair_in_order_with_its_dates_and_value(app):
    open_channel(app, "Mi-isi")
    pairs = read_data("sites/mayon/pairs.json")
    rows = {row["pair_id"]: row for row in read_data("sites/mayon/channel_areas.json") if row["channel_id"] == "mayon_miisi"}
    expect(app.locator("#channel-body .channel-bar")).to_have_count(len(pairs))
    texts = bar_rows(app)
    assert [bar.get_attribute("data-pair") for bar in app.locator("#channel-body .channel-bar").all()] == [pair["id"] for pair in pairs]
    for text, pair in zip(texts, pairs):
        assert f"{rows[pair['id']]['flagged_area_km2']:.2f} km²" in text
        assert f"track {pair['track']}" in text
    assert texts[-1].startswith("Oct 8, 2026 to Oct 20, 2026, track 111")


def test_tc067_every_bar_uses_the_same_scale(app):
    open_channel(app, "Basud")
    rows = read_data("sites/mayon/channel_areas.json")
    largest = max(row["flagged_area_km2"] for row in rows)
    mine = {row["pair_id"]: row["flagged_area_km2"] for row in rows if row["channel_id"] == "mayon_basud"}
    wanted = [mine[pair["id"]] / largest for pair in read_data("sites/mayon/pairs.json")]
    assert bar_widths(app) == pytest.approx(wanted, abs=0.01)


def test_tc068_the_strip_shows_the_map_fits_it_and_back_removes_it(app):
    expect(strip_paths(app)).to_have_count(0)
    open_channel(app, "Mi-isi")
    expect(strip_paths(app)).to_have_count(1)
    props = channel("Mi-isi")["properties"]
    west, south, east, north = shape(props["strip_geometry"]).bounds
    inside = app.evaluate(f"testMap.getBounds().contains(L.latLngBounds([{south}, {west}], [{north}, {east}]))")
    assert inside
    # The map moved to the channel: its center is now the middle of the strip and the part past it.
    west, south, east, north = shape(props["strip_geometry"]).union(shape(props["not_checked_geometry"])).bounds
    assert map_center(app) == pytest.approx(((south + north) / 2, (west + east) / 2), abs=0.002)
    app.click("#channel-back")
    expect(strip_paths(app)).to_have_count(0)
    expect(app.locator("#channel-title")).to_have_text("Channels")
    expect(app.locator("#channel-body .channel-row")).to_have_count(4)
    expect(app.locator("#channel-back")).to_be_hidden()


def test_tc068_closing_the_view_removes_the_strip(app):
    open_channel(app, "Padang")
    expect(strip_paths(app)).to_have_count(1)
    app.click("#channel-close")
    expect(strip_paths(app)).to_have_count(0)
    expect(app.locator("#channel-panel")).to_be_hidden()


def test_tc068_switching_site_closes_the_view(app):
    open_channel(app, "Lidong")
    app.click("#site-name")
    app.click("#picker-panel button:has-text('Azuero Peninsula')")
    expect(app.locator("#pair-list")).to_have_value("panama_D141F085_20260927_20261009")
    expect(app.locator("#channel-panel")).to_be_hidden()
    expect(strip_paths(app)).to_have_count(0)
    expect(app.locator("body")).not_to_have_class("channels-open")


def test_a_strip_is_drawn_under_the_radar_image(app):
    open_channel(app, "Basud")
    order = app.evaluate("""[
      getComputedStyle(document.querySelector('.leaflet-channelStrip-pane')).zIndex,
      getComputedStyle(document.querySelector('.leaflet-radar-pane')).zIndex,
    ].map(Number)""")
    assert order[0] < order[1]


def test_tapping_a_bar_selects_that_pair_on_the_map(app):
    july = "mayon_A111F008_20260703_20260715"
    open_channel(app, "Mi-isi")
    selected = app.locator('#channel-body .channel-bar[aria-current="true"]')
    expect(selected).to_have_attribute("data-pair", LATEST_PAIR)
    app.click(f'#channel-body .channel-bar[data-pair="{july}"]')
    expect(app.locator(f'.leaflet-radar-pane img[src*="{july}"]')).to_have_count(1)
    expect(app.locator("#pair-list")).to_have_value(july)
    expect(selected).to_have_attribute("data-pair", july)
    expect(strip_paths(app)).to_have_count(1)


def test_picking_a_pair_in_the_timeline_moves_the_selected_bar(app):
    july = "mayon_A111F008_20260703_20260715"
    open_channel(app, "Mi-isi")
    app.select_option("#pair-list", july)
    expect(app.locator('#channel-body .channel-bar[aria-current="true"]')).to_have_attribute("data-pair", july)


def test_a_bar_whose_pair_fails_to_load_says_so_in_the_panel(app):
    july = "mayon_A111F008_20260703_20260715"
    open_channel(app, "Mi-isi")
    app.route(f"**/{july}/pair.json", lambda route: route.abort())
    app.click(f'#channel-body .channel-bar[data-pair="{july}"]')
    expect(app.locator("#channel-status")).to_have_text("Couldn't load this pass. Try again.")
    expect(app.locator("#channel-body .channel-bar")).not_to_have_count(0)
    expect(app.locator('#channel-body .channel-bar[aria-current="true"]')).to_have_attribute("data-pair", LATEST_PAIR)
    app.unroute(f"**/{july}/pair.json")
    app.click(f'#channel-body .channel-bar[data-pair="{july}"]')
    expect(app.locator('#channel-body .channel-bar[aria-current="true"]')).to_have_attribute("data-pair", july)
    expect(app.locator("#channel-status")).to_have_text("")


def test_tc069_no_radar_data_replaces_the_bar(app):
    serve_areas(app, area_rows({"mayon_miisi": None}))
    open_channel(app, "Mi-isi")
    last = app.locator("#channel-body .channel-bar").last
    expect(last).to_contain_text("No radar data")
    expect(last).not_to_contain_text("km²")
    assert last.locator(".channel-bar-fill").count() == 0


def test_tc069_a_real_zero_still_shows_as_zero(app):
    serve_areas(app, area_rows({"mayon_miisi": 0}))
    open_channel(app, "Mi-isi")
    last = app.locator("#channel-body .channel-bar").last
    expect(last).to_contain_text("0.00 km²")
    expect(last).not_to_contain_text("No radar data")


def test_the_view_lists_the_channels_towns(app):
    open_channel(app, "Padang")
    expect(app.locator("#channel-body")).to_contain_text("Towns along this channel: Santo Domingo, Legazpi City")


def test_the_view_fits_a_phone(page, site_url):
    open_phone(page, site_url)
    open_channel(page, "Mi-isi")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert controls_too_small(page) == []
    assert page.locator("#map").bounding_box()["height"] >= 200
    expect(strip_paths(page)).to_have_count(1)
    expect(page.locator(".disclaimer")).to_be_in_viewport()


def test_axe_on_the_view(app):
    open_channel(app, "Mi-isi")
    assert problems_on(app) == []


def test_axe_on_the_view_on_a_phone(page, site_url):
    open_phone(page, site_url)
    open_channel(page, "Mi-isi")
    assert problems_on(page) == []


def not_checked_paths(page):
    return page.locator('.leaflet-overlay-pane path[stroke="#ffffff"][stroke-dasharray="6 7"]')


def test_tc081_the_part_past_the_reach_is_dashed_on_the_map(app):
    """Every confirmed line runs at least a little past 10 km. Mi-isi runs about 4 km past it."""
    assert all(item["properties"]["not_checked_geometry"] for item in channels())
    expect(not_checked_paths(app)).to_have_count(4)
    expect(app.locator("#channel-note")).to_contain_text("past the reach of this map, so not checked")


def test_tc081_opening_a_channel_labels_that_part_and_keeps_it_in_view(app):
    open_channel(app, "Mi-isi")
    label = app.locator(".not-checked-label")
    expect(label).to_have_text("Not checked")
    expect(label).to_be_in_viewport()
    expect(app.locator("#channel-body")).to_contain_text("more than 10 km from the summit")
    expect(app.locator("#channel-body")).to_contain_text("doesn't mean that nothing changed there")
    west, south, east, north = shape(channel("Mi-isi")["properties"]["not_checked_geometry"]).bounds
    assert app.evaluate(f"testMap.getBounds().contains(L.latLngBounds([{south}, {west}], [{north}, {east}]))")
    app.click("#channel-back")
    expect(app.locator(".not-checked-label")).to_have_count(0)


def test_tc081_the_strip_stops_at_the_reach_and_nothing_past_it_counts(app):
    """A tap on the dashed part says it wasn't checked, and never that nothing was found."""
    stretch = channel("Mi-isi")["properties"]["not_checked_geometry"]["coordinates"]
    lon, lat = stretch[len(stretch) // 2]
    tap_at(app, lat, lon)
    expect(card(app).locator(".readout-place").first).to_have_text("Mi-isi")
    expect(card(app)).to_contain_text("Not checked: this map only looks within 10 km of the summit")
    expect(card(app)).not_to_contain_text("No new material detected")
    assert not shape(channel("Mi-isi")["properties"]["strip_geometry"]).contains(shape({"type": "Point", "coordinates": [lon, lat]}))


GAP_PAIR = "mayon_A111F008_20260727_20260820"
GAP_NOTE = "24-day gap, not comparable"


def test_tc070_the_24_day_bar_is_dimmed_with_its_note(app):
    open_channel(app, "Mi-isi")
    bars = app.locator("#channel-body .channel-bar")
    dimmed = app.locator("#channel-body .channel-bar-dim")
    expect(dimmed).to_have_count(1)
    assert dimmed.get_attribute("data-pair") == GAP_PAIR
    expect(dimmed).to_contain_text(GAP_NOTE)
    assert sum(GAP_NOTE in text for text in bars.all_inner_texts()) == 1
    opacity = dimmed.locator(".channel-bar-fill").evaluate("(fill) => getComputedStyle(fill).opacity")
    assert float(opacity) < 1
    other = bars.first.locator(".channel-bar-fill").evaluate("(fill) => getComputedStyle(fill).opacity")
    assert float(other) == 1


def test_tc071_the_24_day_pair_is_dimmed_on_the_pass_timeline(app):
    dimmed = app.locator("#pair-list option.pair-dim")
    expect(dimmed).to_have_count(1)
    assert dimmed.get_attribute("value") == GAP_PAIR
    expect(dimmed).to_contain_text(GAP_NOTE)
    assert app.locator("#pair-list option").count() == len(read_data("sites/mayon/pairs.json"))


def test_tc071_selecting_it_shows_the_note_and_dims_the_list(app):
    expect(app.locator("#pair-gap")).to_have_text("")
    expect(app.locator("#pair-list")).not_to_have_class("pair-dim")
    app.select_option("#pair-list", GAP_PAIR)
    expect(app.locator("#pair-gap")).to_have_text(GAP_NOTE)
    expect(app.locator("#pair-list")).to_have_class("pair-dim")
    app.select_option("#pair-list", LATEST_PAIR)
    expect(app.locator("#pair-gap")).to_have_text("")
    expect(app.locator("#pair-list")).not_to_have_class("pair-dim")


def test_tc071_the_note_shows_on_a_phone_with_the_drawer_closed(page, site_url):
    open_phone(page, site_url)
    page.select_option("#pair-list", GAP_PAIR)
    expect(page.locator("#pair-gap")).to_be_visible()
    expect(page.locator("#pair-gap")).to_have_text(GAP_NOTE)


def test_tc071_panamas_pairs_are_all_12_days(app):
    app.click("#site-name")
    app.click("#picker-panel button:has-text('Azuero Peninsula')")
    expect(app.locator("#pair-list")).to_have_value("panama_D141F085_20260927_20261009")
    expect(app.locator("#pair-list option.pair-dim")).to_have_count(0)


def test_the_latest_pair_line_says_when_its_gap_is_unequal(page, site_url):
    """Uses a test browser's own copy of the list, with the 24-day pair last."""
    pairs = read_data("sites/mayon/pairs.json")
    gap = next(pair for pair in pairs if pair["id"] == GAP_PAIR)
    reordered = [pair for pair in pairs if pair["id"] != GAP_PAIR] + [gap]
    prepare_page(page)
    page.route("**/sites/mayon/pairs.json", lambda route: route.fulfill(body=envelope(reordered), content_type="application/json"))
    page.goto(site_url)
    wait_until_ready(page)
    page.click("#channels-button")
    expect(page.locator(".channel-lead")).to_contain_text(GAP_NOTE)


def test_axe_with_the_24_day_pair_selected(app):
    app.select_option("#pair-list", GAP_PAIR)
    expect(app.locator("#pair-gap")).to_have_text(GAP_NOTE)
    open_channel(app, "Basud")
    assert problems_on(app) == []

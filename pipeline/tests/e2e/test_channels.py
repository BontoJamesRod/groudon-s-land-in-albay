"""Browser tests for channels (F-19) and the Channel timeline (F-20). Each test name carries its TC number."""
import json

import numpy as np
import pytest
from playwright.sync_api import expect
from shapely import contains_xy
from shapely.geometry import shape

from .conftest import SITE, open_drawer_if_closed, prepare_page, read_data, wait_until_ready
from .test_mvp import card, tap_at

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

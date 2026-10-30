"""Check that the browser's grid formula reads the same cells as the published grid file.

readout.js finds a cell as floor((lon - west) / (east - west) x width) and
floor((north - lat) / (north - south) x height). Here the same formula, in Python,
is checked against the real published grid and the real land polygon.
"""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Point, shape

SITE_DATA = Path(__file__).resolve().parents[2] / "site" / "data" / "sites" / "mayon"
SEA_CODE = 254


def published_layer():
    pair_files = sorted((SITE_DATA / "pairs").glob("*/pair.json"))
    pair = json.loads(pair_files[-1].read_text(encoding="utf-8"))["data"]
    layer = next(item for item in pair["layers"] if item["kind"] == "new_material")
    cells = np.frombuffer((pair_files[-1].parent / layer["grid_path"]).read_bytes(), dtype="uint8")
    return layer, cells.reshape(layer["grid_height"], layer["grid_width"])


def cell_at(layer, grid, lat, lon):
    width, height = layer["grid_width"], layer["grid_height"]
    column = int(np.floor((lon - layer["bounds_west"]) / (layer["bounds_east"] - layer["bounds_west"]) * width))
    row = int(np.floor((layer["bounds_north"] - lat) / (layer["bounds_north"] - layer["bounds_south"]) * height))
    return grid[row, column]


def test_sample_points_agree_with_the_land_polygon():
    layer, grid = published_layer()
    land = shape(json.loads((SITE_DATA / "land.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"])
    random = np.random.default_rng(0)
    checked = 0
    for lat, lon in zip(random.uniform(13.145, 13.375, 400), random.uniform(123.565, 123.805, 400)):
        # Skip points right on the coast, where one cell can hold both land and sea.
        point = Point(lon, lat)
        if land.boundary.distance(point) < 0.001:
            continue
        assert (cell_at(layer, grid, lat, lon) == SEA_CODE) == (not land.contains(point))
        checked += 1
    assert checked > 300


def test_sea_point_east_of_legazpi_reads_sea():
    layer, grid = published_layer()
    assert cell_at(layer, grid, 13.15, 123.80) == SEA_CODE

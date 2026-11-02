"""TC-088: the relief tiles and the download limit (F-22, FR-076)."""
import json
import math
import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from mrw.contract_check import _check_relief, relief_tile_range
from mrw.relief import DOWNLOAD_LIMIT_BYTES, PAPER, SEA, DownloadTooLarge, check_download_size, contour_cells, dem_names, hillshade, paint

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "site" / "data"


def mayon():
    return json.loads((DATA / "sites.json").read_text(encoding="utf-8"))["data"][0]


def both_sites():
    return json.loads((DATA / "sites.json").read_text(encoding="utf-8"))["data"]


def bounds_of(site):
    return [site[f"relief_bounds_{side}"] for side in ("west", "south", "east", "north")]


def test_a_download_at_the_limit_stops_before_it_starts():
    with pytest.raises(DownloadTooLarge):
        check_download_size({"a": DOWNLOAD_LIMIT_BYTES - 1, "b": 1})


def test_a_download_under_the_limit_goes_ahead():
    assert check_download_size({"a": 10, "b": 5}) == 15


def test_the_owners_limit_is_300_mb():
    assert DOWNLOAD_LIMIT_BYTES == 300_000_000


def test_the_file_names_cover_the_bounds():
    assert dem_names((123.0, 12.6, 124.4, 13.9)) == [
        "Copernicus_DSM_COG_10_N12_00_E123_00_DEM", "Copernicus_DSM_COG_10_N12_00_E124_00_DEM",
        "Copernicus_DSM_COG_10_N13_00_E123_00_DEM", "Copernicus_DSM_COG_10_N13_00_E124_00_DEM"]
    assert dem_names((-81.0, -1.0, -80.5, -0.5)) == ["Copernicus_DSM_COG_10_S01_00_W081_00_DEM"]


def test_a_tile_range_matches_a_known_tile():
    # At zoom 12, Mayon's longitude is in tile (123.6856 + 180) / 360 * 4096 = 3455.3
    x_low, _, x_high, _ = relief_tile_range((123.6856, 13.2, 123.69, 13.3), 12)
    assert x_low == x_high == 3455


def test_an_edge_on_a_tile_line_doesnt_need_the_next_tile():
    assert relief_tile_range((0.0, 0.0, 90.0, 10.0), 2)[2] == 2  # 90 degrees east starts tile 3


def test_flat_ground_is_shaded_evenly():
    shade = hillshade(np.full((5, 5), 100.0), 20.0)
    assert np.allclose(shade, shade[0, 0])


def test_a_slope_facing_the_light_is_brighter_than_one_facing_away():
    rows = np.arange(50.0)[:, None] * np.ones((50, 50))
    # Height rising to the south faces north, toward the light, and rising to the north faces away.
    assert hillshade(rows * 10, 20.0).mean() > hillshade(rows[::-1] * 10, 20.0).mean()


def test_contours_mark_where_the_height_crosses_a_line():
    height = np.array([[90.0, 90.0, 110.0, 110.0]] * 3)
    assert contour_cells(height, 100)[1].tolist()[1:] == [False, True, False]


def test_the_sea_is_blue_and_flat_land_is_near_the_paper_colour():
    height = np.zeros((6, 6))
    height[:, 3:] = 50.0
    picture = paint(height, 20.0, 12)
    assert picture[3, 0].tolist() == SEA.astype("uint8").tolist()
    assert np.abs(picture[3, 5].astype(float) - PAPER).max() < 20


def test_100_m_contours_only_show_when_zoomed_in():
    height = np.tile(np.linspace(50, 150, 40), (40, 1))
    assert (paint(height, 20.0, 12) != paint(height, 20.0, 11)).any()


@pytest.mark.parametrize("site", both_sites(), ids=lambda site: site["id"])
def test_every_tile_the_map_can_show_exists_and_is_a_256_px_webp(site):
    folder = DATA / "sites" / site["id"] / "relief"
    for zoom in range(site["min_zoom"], site["relief_max_native_zoom"] + 1):
        x_low, y_low, x_high, y_high = relief_tile_range(bounds_of(site), zoom)
        for x in range(x_low, x_high + 1):
            for y in range(y_low, y_high + 1):
                assert (folder / str(zoom) / str(x) / f"{y}.webp").is_file()
    with Image.open(next(folder.rglob("*.webp"))) as tile:
        assert tile.format == "WEBP" and tile.size == (256, 256)


def colour_at(lat, lon, zoom=12, site_id="mayon"):
    """The colour of the published relief at a place, read from its tile."""
    count = 2 ** zoom
    x = (lon + 180) / 360 * count
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * count
    with Image.open(DATA / "sites" / site_id / "relief" / str(zoom) / str(int(x)) / f"{int(y)}.webp") as tile:
        return np.array(tile.convert("RGB").getpixel((int(x % 1 * 256), int(y % 1 * 256))), dtype=float)


def test_the_published_tiles_show_the_sea_in_blue_and_the_land_not():
    albay_gulf, inland_near_guinobatan = (13.15, 123.85), (13.19, 123.60)
    assert np.abs(colour_at(*albay_gulf) - SEA).max() < 12
    assert np.abs(colour_at(*inland_near_guinobatan) - SEA).max() > 12


def test_panamas_open_sea_has_no_height_file_and_is_still_blue():
    south_of_the_peninsula = (6.95, -80.7)
    assert np.abs(colour_at(*south_of_the_peninsula, site_id="panama") - SEA).max() < 12


@pytest.mark.parametrize("site", both_sites(), ids=lambda site: site["id"])
def test_the_relief_stays_small_enough_for_the_site(site):
    files = list((DATA / "sites" / site["id"] / "relief").rglob("*.webp"))
    assert sum(path.stat().st_size for path in files) < 20_000_000


@pytest.mark.parametrize("site", both_sites(), ids=lambda site: site["id"])
def test_the_relief_covers_the_whole_site(site):
    assert site["relief_bounds_west"] < site["bounds_west"] and site["relief_bounds_east"] > site["bounds_east"]
    assert site["relief_bounds_south"] < site["bounds_south"] and site["relief_bounds_north"] > site["bounds_north"]


def relief_site(tmp_path):
    """A small site with one zoom of relief tiles copied in, for breaking."""
    site = mayon() | {"min_zoom": 10, "relief_max_native_zoom": 10}
    target = tmp_path / "sites" / "mayon" / "relief"
    shutil.copytree(DATA / "sites" / "mayon" / "relief" / "10", target / "10")
    return site, target


def test_the_contract_accepts_complete_tiles(tmp_path):
    site, _ = relief_site(tmp_path)
    errors = []
    _check_relief(tmp_path, site, errors)
    assert errors == []


def test_the_contract_fails_on_a_missing_tile(tmp_path):
    site, target = relief_site(tmp_path)
    next(target.rglob("*.webp")).unlink()
    errors = []
    _check_relief(tmp_path, site, errors)
    assert len(errors) == 1 and "relief tile is missing" in errors[0]


def test_the_contract_fails_on_half_set_fields(tmp_path):
    errors = []
    _check_relief(tmp_path, mayon() | {"relief_bounds_west": None}, errors)
    assert "needs all four relief bounds" in errors[0]
    errors = []
    _check_relief(tmp_path, mayon() | {"relief_max_native_zoom": None}, errors)
    assert "relief bounds need relief_max_native_zoom" in errors[0]


def test_a_site_with_no_relief_settings_needs_no_tiles(tmp_path):
    no_relief = {f"relief_bounds_{side}": None for side in ("west", "south", "east", "north")}
    errors = []
    _check_relief(tmp_path, mayon() | no_relief | {"relief_max_native_zoom": None}, errors)
    assert errors == []

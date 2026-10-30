"""Tests for the export module on a small fake pair, with no downloads (T-018, TC-023, TC-025, TC-026)."""
import json

import numpy as np
import pytest
from PIL import Image
from pyproj import Transformer

from mrw.classify import HIGH, LOW
from mrw.config import load_site
from mrw.contract_check import check_data_dir
from mrw.export import OUT_FOLDER, run_pair, site_bounds, web_grid_size, write_pair
from mrw.gcov import HAS_VALUE, SEA
from mrw.pairs import PairError
from mrw.search import parse_gcov, parse_gunw

BEFORE = "NISAR_L2_PR_GCOV_032_111_A_008_4005_DHDH_A_20261007T211319_20261007T211354_P05023_N_F_J_001"
AFTER = "NISAR_L2_PR_GCOV_033_111_A_008_4005_DHDH_A_20261019T211319_20261019T211354_P05023_N_F_J_001"
OTHER_TRACK = "NISAR_L2_PR_GCOV_033_104_D_082_4005_DHDH_A_20261019T101646_20261019T101721_P05023_N_F_J_001"
GUNW = "NISAR_L2_PR_GUNW_032_111_A_008_033_4000_SH_20261007T211319_20261007T211354_20261019T211319_20261019T211354_P05023_N_F_J_001"
GUNW_PREVIOUS = "NISAR_L2_PR_GUNW_031_111_A_008_032_4000_SH_20260925T211319_20260925T211354_20261007T211319_20261007T211354_P05023_N_F_J_001"
PREVIOUS_ID = "mayon_A111F008_20260925_20261007"


def fake_gcov_result():
    """A UTM grid over the whole site: 20 m pixels, with one bright square."""
    bounds = site_bounds(load_site("mayon"))
    to_utm = Transformer.from_crs(4326, 32651, always_xy=True)
    x_low, y_low = to_utm.transform(bounds[0], bounds[1])
    x_high, y_high = to_utm.transform(bounds[2], bounds[3])
    x_values = np.arange(x_low - 400, x_high + 400, 20.0)
    y_values = np.arange(y_high + 400, y_low - 400, -20.0)
    shape = (len(y_values), len(x_values))
    change = np.zeros(shape)
    change[500:600, 500:600] = 5.0
    reasons = np.full(shape, HAS_VALUE, dtype="uint8")
    reasons[:, :100] = SEA
    change[reasons != HAS_VALUE] = np.nan
    return {"before_db": np.full(shape, -10.0), "after_db": np.full(shape, -9.0), "change_db": change,
            "reasons": reasons, "x": x_values, "y": y_values, "epsg": 32651,
            "spacing_x_m": 20.0, "spacing_y_m": 20.0}


def write_fake(tmp_path, with_coherence=True):
    result = fake_gcov_result()
    loss = None
    if with_coherence:
        loss = np.zeros(result["change_db"].shape)
        loss[500:550, 500:600] = 0.5
    return write_pair(result, loss, parse_gcov(BEFORE), parse_gcov(AFTER),
                      parse_gunw(GUNW) if with_coherence else None,
                      parse_gunw(GUNW_PREVIOUS) if with_coherence else None,
                      PREVIOUS_ID, load_site("mayon"), tmp_path), tmp_path


def pair_folder(root, pair):
    return root / "sites" / "mayon" / "pairs" / pair["id"]


def test_output_passes_the_contract_check(tmp_path):
    pair, root = write_fake(tmp_path)
    assert check_data_dir(root, published=False) == []
    assert pair["status"] == "ready"
    assert {layer["kind"] for layer in pair["layers"]} == {"before_db", "after_db", "change_db", "coherence_loss", "new_material"}


def test_areas_match_the_fake_square(tmp_path):
    pair, _root = write_fake(tmp_path)
    # 50 x 100 pixels pass both tests and 50 x 100 pass only brightness, at 0.0004 km2 each
    assert pair["high_confidence_area_km2"] == 2.0
    assert pair["low_confidence_area_km2"] == 2.0
    assert pair["new_material_area_km2"] == 4.0


def test_thresholds_are_marked_provisional_in_the_output(tmp_path):
    pair, _root = write_fake(tmp_path)
    layer = next(item for item in pair["layers"] if item["kind"] == "new_material")
    assert "PROVISIONAL" in layer["title"]


def test_tc023_no_gunw_still_processes_with_low_confidence_only(tmp_path):
    pair, root = write_fake(tmp_path, with_coherence=False)
    assert check_data_dir(root, published=False) == []
    assert pair["coherence_used"] is False
    assert pair["coherence_loss_threshold"] is None
    assert pair["gunw_granule_id"] is None
    assert pair["high_confidence_area_km2"] == 0
    assert pair["low_confidence_area_km2"] == 4.0
    grid = (pair_folder(root, pair) / "new_material.bin").read_bytes()
    assert HIGH not in set(grid) and LOW in set(grid)
    assert not (pair_folder(root, pair) / "coherence_loss.png").exists()


def test_grid_and_image_have_north_up_and_the_expected_size(tmp_path):
    pair, root = write_fake(tmp_path)
    width, height = web_grid_size(site_bounds(load_site("mayon")))
    folder = pair_folder(root, pair)
    grid = np.frombuffer((folder / "new_material.bin").read_bytes(), dtype="uint8").reshape(height, width)
    rows = np.flatnonzero((grid == HIGH).any(axis=1))
    # The bright square is at row 500 to 600 of about 1300 from the north, so in the northern half.
    assert rows.max() < height / 2
    with Image.open(folder / "new_material.png") as image:
        assert image.size == (width, height)
        alpha = np.array(image)[..., 3]
    assert ((grid == HIGH) == (alpha > 0))[rows.min()].all()


def test_grid_keeps_the_sea_code(tmp_path):
    pair, root = write_fake(tmp_path)
    assert SEA in set((pair_folder(root, pair) / "new_material.bin").read_bytes())


def test_record_lists_the_granules_for_each_layer(tmp_path):
    pair, root = write_fake(tmp_path)
    saved = json.loads((pair_folder(root, pair) / "pair.json").read_text(encoding="utf-8"))["data"]
    layers = {layer["kind"]: layer for layer in saved["layers"]}
    assert layers["before_db"]["source_granule_ids"] == [BEFORE]
    assert set(layers["new_material"]["source_granule_ids"]) == {BEFORE, AFTER, GUNW, GUNW_PREVIOUS}
    assert saved["previous_pair_id"] == PREVIOUS_ID


def fake_passes(names):
    return lambda _config, _start: [parse_gcov(name) for name in names]


def nothing_written(path):
    return not list(path.rglob("*"))


def test_tc025_mixed_tracks_stop_and_write_no_files(tmp_path):
    with pytest.raises(PairError) as caught:
        run_pair("mayon", BEFORE, OTHER_TRACK, out_folder=tmp_path,
                 search_passes=fake_passes([BEFORE, OTHER_TRACK]), search_products=lambda c, s: [])
    assert str(caught.value) == "Passes are not from the same track, frame and direction"
    assert nothing_written(tmp_path)


def test_tc026_missing_product_stops_and_writes_no_files(tmp_path):
    with pytest.raises(PairError) as caught:
        run_pair("mayon", BEFORE, "FAKE_GRANULE", out_folder=tmp_path,
                 search_passes=fake_passes([BEFORE]), search_products=lambda c, s: [])
    assert str(caught.value) == "Product not available yet: FAKE_GRANULE"
    assert nothing_written(tmp_path)


def test_default_output_folder_is_the_ignored_one():
    assert OUT_FOLDER.parts[-2:] == ("pipeline", "out")

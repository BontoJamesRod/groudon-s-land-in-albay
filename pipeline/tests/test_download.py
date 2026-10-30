"""Tests for the download module, using a small local HDF5 file instead of ASF (T-013)."""
import io

import h5py
import numpy as np
import pytest
from pyproj import Transformer

from mrw import download
from mrw.download import BudgetExceeded, RangedFile, crop_window, read_crop, total_bytes_logged
from mrw.search import BlindnessError

GROUP = "/science/LSAR/GCOV/grids/frequencyA"
SAFE = "NISAR_L2_PR_GCOV_032_111_A_008_4005_DHDH_A_20261007T211319_20261007T211354_P05023_N_F_J_001"
ERUPTION = "NISAR_L2_PR_GCOV_034_111_A_008_4005_DHDH_A_20261031T211319_20261031T211354_P05023_N_F_J_001"
BOUNDS = (123.60, 13.20, 123.62, 13.22)
EPSG = 32651


def make_product_bytes():
    """Build a small HDF5 file in memory, laid out like a real GCOV."""
    to_utm = Transformer.from_crs(4326, EPSG, always_xy=True)
    x0, y0 = to_utm.transform(123.59, 13.23)
    x_values = x0 + np.arange(400) * 10.0
    y_values = y0 - np.arange(400) * 10.0
    buffer = io.BytesIO()
    with h5py.File(buffer, "w") as product:
        group = product.create_group(GROUP)
        group["xCoordinates"] = x_values
        group["yCoordinates"] = y_values
        group["HHHH"] = np.arange(160000, dtype="float32").reshape(400, 400)
        group["projection"] = np.uint32(EPSG)
        group["projection"].attrs["epsg_code"] = EPSG
    return buffer.getvalue()


def local_opener(content, calls):
    """Stand in for ASF: serve ranged reads from bytes, and count how often it opens."""
    def opener(_url, _raw_folder):
        calls.append(1)
        return RangedFile(lambda start, end: content[start:end], len(content))
    return opener


def test_crop_covers_the_bounds_and_second_run_uses_the_cache(tmp_path):
    content, calls = make_product_bytes(), []
    opener = local_opener(content, calls)
    crop = read_crop(SAFE, "url", GROUP, ["HHHH"], BOUNDS, raw_folder=tmp_path, opener=opener)
    to_utm = Transformer.from_crs(4326, EPSG, always_xy=True)
    x_low, y_low = to_utm.transform(BOUNDS[0], BOUNDS[1])
    x_high, y_high = to_utm.transform(BOUNDS[2], BOUNDS[3])
    assert crop["x"].min() <= x_low + 10 and crop["x"].max() >= x_high - 10
    assert crop["y"].min() <= y_low + 10 and crop["y"].max() >= y_high - 10
    assert crop["HHHH"].shape == (len(crop["y"]), len(crop["x"]))
    assert crop["HHHH"].shape[0] < 400 and int(crop["epsg"]) == EPSG

    again = read_crop(SAFE, "url", GROUP, ["HHHH"], BOUNDS, raw_folder=tmp_path, opener=opener)
    assert len(calls) == 1
    assert np.array_equal(again["HHHH"], crop["HHHH"])


def test_bytes_are_logged(tmp_path):
    content = make_product_bytes()
    read_crop(SAFE, "url", GROUP, ["HHHH"], BOUNDS, raw_folder=tmp_path, opener=local_opener(content, []))
    assert 0 < total_bytes_logged(tmp_path) <= len(content)


def test_a_product_from_the_eruption_is_refused_before_opening(tmp_path):
    calls = []
    with pytest.raises(BlindnessError):
        read_crop(ERUPTION, "url", GROUP, ["HHHH"], BOUNDS, raw_folder=tmp_path,
                  opener=local_opener(b"", calls))
    assert calls == []


def test_budget_stops_fetching():
    content = bytes(download.BLOCK_SIZE * 2)
    remote = RangedFile(lambda start, end: content[start:end], len(content), budget=1000)
    with pytest.raises(BudgetExceeded):
        remote.read(10)


def test_ranged_file_reads_across_blocks_and_refetches_nothing():
    content = bytes(range(256)) * 50000
    fetched = []

    def fetch(start, end):
        fetched.append(start)
        return content[start:end]

    remote = RangedFile(fetch, len(content))
    remote.seek(download.BLOCK_SIZE - 3)
    assert remote.read(6) == content[download.BLOCK_SIZE - 3:download.BLOCK_SIZE + 3]
    remote.seek(download.BLOCK_SIZE - 3)
    remote.read(6)
    assert len(fetched) == 2


def test_site_outside_the_product_stops():
    with pytest.raises(ValueError):
        crop_window(np.arange(10.0), np.arange(10.0), BOUNDS, EPSG)

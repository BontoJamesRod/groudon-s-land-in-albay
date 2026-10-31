"""Tests for the coherence module on small test arrays (T-015)."""
import numpy as np
import pytest

from mrw.coherence import coherence_loss, compute_coherence_loss, resample_to_grid

EPSG = 32651


def crop(value, x_values, y_values):
    return {"coherenceMagnitude": np.full((len(y_values), len(x_values)), value, dtype="float32"),
            "x": x_values, "y": y_values, "epsg": np.array(EPSG)}


def test_loss_is_previous_minus_current():
    assert coherence_loss(np.array([0.8]), np.array([0.3]))[0] == pytest.approx(0.5)
    assert coherence_loss(np.array([0.2]), np.array([0.3]))[0] == pytest.approx(-0.1)
    assert np.isnan(coherence_loss(np.array([np.nan]), np.array([0.3]))[0])


def test_resample_takes_the_nearest_coarse_cell():
    source_x = np.array([0.0, 80.0, 160.0])
    source_y = np.array([160.0, 80.0, 0.0])  # north first, as in the products
    values = np.arange(9.0).reshape(3, 3)
    result = resample_to_grid(values, source_x, source_y, np.array([10.0, 70.0, 150.0]), np.array([150.0, 10.0]))
    assert result.tolist() == [[0.0, 1.0, 2.0], [6.0, 7.0, 8.0]]


def test_cells_outside_the_coarse_grid_become_no_data():
    source = np.array([0.0, 80.0])
    result = resample_to_grid(np.ones((2, 2)), source, source[::-1], np.array([40.0, 500.0]), np.array([40.0, -500.0]))
    assert result[0, 0] == 1.0
    assert np.isnan(result[0, 1]) and np.isnan(result[1, 0])


def test_compute_loss_lands_on_the_gcov_grid():
    coarse_x, coarse_y = np.arange(0.0, 800.0, 80.0), np.arange(800.0, 0.0, -80.0)
    target_x, target_y = np.arange(100.0, 300.0, 10.0), np.arange(500.0, 300.0, -10.0)
    loss = compute_coherence_loss(crop(0.9, coarse_x, coarse_y), crop(0.2, coarse_x, coarse_y), target_x, target_y, EPSG)
    assert loss.shape == (20, 20)
    assert np.allclose(loss, 0.7)


@pytest.mark.parametrize("use_previous,use_current", [(False, True), (True, False), (False, False)])
def test_missing_gunw_gives_the_brightness_only_fallback(use_previous, use_current):
    axis = np.arange(0.0, 800.0, 80.0)
    good = crop(0.5, axis, axis[::-1])
    assert compute_coherence_loss(good if use_previous else None, good if use_current else None, axis, axis, EPSG) is None


def test_different_projections_stop():
    axis = np.arange(0.0, 800.0, 80.0)
    good, other = crop(0.5, axis, axis[::-1]), crop(0.5, axis, axis[::-1])
    other["epsg"] = np.array(32650)
    with pytest.raises(ValueError):
        compute_coherence_loss(good, other, axis, axis, EPSG)

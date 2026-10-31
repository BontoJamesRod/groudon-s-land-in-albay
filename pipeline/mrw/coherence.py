"""Task T-015: compute coherence loss from two GUNW products.

Coherence says how alike two radar passes are at a spot, from 0 (nothing alike) to
1 (identical). Ground that stays put keeps its coherence. Fresh material replaces
the old surface, so coherence falls between the passes around the event.

Coherence loss = previous pair's coherence - this pair's coherence (FR-022).
A high value means the ground used to stay alike but no longer does.

Forests and wet ground have low coherence anyway, so one pair alone isn't enough:
that is why the previous pair is the baseline.
"""
import numpy as np

GUNW_GROUP = "/science/LSAR/GUNW/grids/frequencyA/unwrappedInterferogram/HH"
GUNW_DATASETS = ("coherenceMagnitude",)


def coherence_loss(previous, current):
    """Return previous minus current. NaN wherever either one has no value."""
    return previous - current


def _nearest_indexes(wanted, axis):
    """For each wanted coordinate, find the nearest position on an evenly spaced axis.

    Returns the positions and a True/False array saying if each one is inside the axis.
    """
    spacing = axis[1] - axis[0]
    positions = np.rint((wanted - axis[0]) / spacing).astype(int)
    inside = (positions >= 0) & (positions < len(axis))
    return np.clip(positions, 0, len(axis) - 1), inside


def resample_to_grid(values, source_x, source_y, target_x, target_y):
    """Copy values from a coarse grid to a finer one, taking the nearest cell.

    GUNW coherence has pixels of about 80 m and GCOV about 10 m. Nearest cell keeps
    the real values rather than inventing smooth ones in between, so edges look
    blocky at about 80 m (docs/04, ADR-006). Cells outside the source become NaN.
    """
    columns, inside_x = _nearest_indexes(target_x, source_x)
    rows, inside_y = _nearest_indexes(target_y, source_y)
    resampled = values[np.ix_(rows, columns)].astype("float64")
    resampled[~inside_y, :] = np.nan
    resampled[:, ~inside_x] = np.nan
    return resampled


def _on_target(crop, target_x, target_y):
    """Move one GUNW crop's coherence onto the GCOV grid."""
    return resample_to_grid(crop["coherenceMagnitude"], crop["x"], crop["y"], target_x, target_y)


def compute_coherence_loss(previous_crop, current_crop, target_x, target_y, target_epsg):
    """Return coherence loss on the GCOV grid, or None if a GUNW is missing.

    None is the brightness-only fallback: the pair is still processed, but nothing
    can reach high confidence (FR-030).
    """
    if previous_crop is None or current_crop is None:
        return None
    for crop in (previous_crop, current_crop):
        if int(crop["epsg"]) != int(target_epsg):
            raise ValueError("GUNW and GCOV are on different map projections")
    previous = _on_target(previous_crop, target_x, target_y)
    current = _on_target(current_crop, target_x, target_y)
    return coherence_loss(previous, current)

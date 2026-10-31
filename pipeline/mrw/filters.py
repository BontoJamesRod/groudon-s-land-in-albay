"""Optional filters that remove likely false alarms from a class grid.

All of them are OFF unless a site's config turns them on, which is the owner's decision.
Mayon uses max_distance_km only. The study in pipeline/reports/threshold-study-night-1.md
shows what each one removes.

- max_distance_km: only look this far from the summit. Most false alarms further out are
  on farmland. It also means the map can't show anything beyond this distance.
- min_cluster_m2: drop detected patches smaller than this. Speckle and single fields make
  small patches, while a deposit on the ground tends to be a connected patch.
- high_confidence_only: keep only cells where both radar signals changed.
- persist_across_pairs: keep a cell only if the next pair flags it too.
"""
import numpy as np
from scipy import ndimage

from mrw.classify import HIGH, LOW, NONE

FILTERS_OFF = {"max_distance_km": None, "min_cluster_m2": None, "high_confidence_only": False, "persist_across_pairs": False}
# Cells touching at a corner count as one patch.
EIGHT_NEIGHBOURS = np.ones((3, 3), dtype=bool)


class FilterConfigError(Exception):
    """The filter settings can't be used. The message says why."""


def check_filters(filters):
    """Stop on an unknown setting or a bad value. A missing section means all off."""
    filters = filters or {}
    unknown = set(filters) - set(FILTERS_OFF)
    if unknown:
        raise FilterConfigError(f"Unknown filter settings: {sorted(unknown)}")
    for name in ("max_distance_km", "min_cluster_m2"):
        size = filters.get(name)
        if size is not None and (not isinstance(size, (int, float)) or isinstance(size, bool) or size <= 0):
            raise FilterConfigError(f"{name} must be above 0, or null to turn it off")
    for name in ("high_confidence_only", "persist_across_pairs"):
        if not isinstance(filters.get(name, False), bool):
            raise FilterConfigError(f"{name} must be true or false")


def keep_within_distance(classes, distance_km, max_distance_km):
    """Clear detections beyond the distance. No-data codes stay as they are."""
    result = classes.copy()
    result[np.isin(classes, (LOW, HIGH)) & (distance_km > max_distance_km)] = NONE
    return result


def remove_small_clusters(classes, min_cluster_m2, cell_m2):
    """Clear detected patches smaller than the given area. No-data codes stay as they are."""
    detected = np.isin(classes, (LOW, HIGH))
    labels, count = ndimage.label(detected, structure=EIGHT_NEIGHBOURS)
    if count == 0:
        return classes.copy()
    # sizes[n] is how many cells patch n has. Label 0 is the background.
    sizes = np.bincount(labels.ravel(), minlength=count + 1)
    too_small = sizes * cell_m2 < min_cluster_m2
    too_small[0] = False
    result = classes.copy()
    result[too_small[labels]] = NONE
    return result


def keep_high_only(classes):
    """Clear low-confidence cells. A pair without coherence data has no high cells at all."""
    result = classes.copy()
    result[classes == LOW] = NONE
    return result


def keep_persistent(classes, next_classes):
    """Clear cells the next pair doesn't flag too. Both grids must be the same size."""
    if classes.shape != next_classes.shape:
        raise FilterConfigError("The two pairs' grids must be the same size")
    result = classes.copy()
    result[np.isin(classes, (LOW, HIGH)) & ~np.isin(next_classes, (LOW, HIGH))] = NONE
    return result


def apply_filters(classes, filters, cell_m2, next_classes=None, distance_km=None):
    """Apply the filters that are on. With everything off, the grid comes back unchanged.

    `distance_km` is each cell's distance from the summit, needed for max_distance_km.
    """
    settings = {**FILTERS_OFF, **(filters or {})}
    check_filters(settings)
    result = classes.copy()
    if settings["max_distance_km"] is not None:
        if distance_km is None:
            raise FilterConfigError("max_distance_km needs each cell's distance from the summit")
        result = keep_within_distance(result, distance_km, settings["max_distance_km"])
    if settings["persist_across_pairs"]:
        # The next pass doesn't exist yet when a pair is first processed.
        if next_classes is None:
            raise FilterConfigError("persist_across_pairs needs the next pair's grid, so a single-pair run can't use it")
        result = keep_persistent(result, next_classes)
    if settings["high_confidence_only"]:
        result = keep_high_only(result)
    if settings["min_cluster_m2"] is not None:
        result = remove_small_clusters(result, settings["min_cluster_m2"], cell_m2)
    return result

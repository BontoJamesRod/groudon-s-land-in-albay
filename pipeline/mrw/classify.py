"""Task T-017: decide which pixels show new material, and how sure we are (FR-023).

- High confidence (2): brightness change AND coherence loss both pass their thresholds.
- Low confidence (1): only one passes.
- None (0): neither passes.

Brightness alone can also change after rain or wind, which is why one signal is
only low confidence. Without coherence data, nothing can reach high (FR-030).

The thresholds are not set here. They come from the site config and stay
PROVISIONAL until the owner chooses the final values.
"""
import numpy as np

from mrw.gcov import HAS_VALUE

NONE = 0
LOW = 1
HIGH = 2
SQUARE_METRES_PER_KM2 = 1_000_000


def classify(change_db, loss, reasons, brightness_threshold_db, coherence_loss_threshold):
    """Return the class grid. Pixels with no value keep their no-data code.

    `loss` is None when there is no coherence data. A brightness drop counts as
    well as a rise, because the threshold applies to the absolute change.
    """
    has_value = reasons == HAS_VALUE
    # Comparing with NaN gives False, so pixels with no value never pass.
    with np.errstate(invalid="ignore"):
        bright = np.abs(change_db) >= brightness_threshold_db
        if loss is None:
            decorrelated = np.zeros(change_db.shape, dtype=bool)
        else:
            decorrelated = loss >= coherence_loss_threshold
    classes = np.array(reasons, dtype="uint8")
    classes[has_value] = NONE
    classes[has_value & (bright | decorrelated)] = LOW
    classes[has_value & bright & decorrelated] = HIGH
    return classes


def areas_km2(classes, spacing_x_m, spacing_y_m):
    """Add up the area of each class, in km2 rounded to 2 decimals.

    The total is the sum of the two rounded numbers, so that it always matches what
    the legend shows (new_material_area_km2 = high + low).
    """
    cell_km2 = spacing_x_m * spacing_y_m / SQUARE_METRES_PER_KM2
    high = round(float(np.count_nonzero(classes == HIGH)) * cell_km2, 2)
    low = round(float(np.count_nonzero(classes == LOW)) * cell_km2, 2)
    return {"high_confidence_area_km2": high, "low_confidence_area_km2": low,
            "new_material_area_km2": round(high + low, 2)}

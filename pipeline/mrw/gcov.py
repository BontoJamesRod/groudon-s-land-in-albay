"""Task T-014: turn two GCOV passes into a map of brightness change.

The radar steps, in order:
1. Read HH backscatter: how strongly the ground sent the radar signal back. The
   values are "linear power" (gamma-0), so one value can be millions of times another.
2. Speckle filter: radar images look grainy because each pixel adds up many small
   echoes. Averaging each pixel with its neighbours (5 x 5) removes most of that.
3. Convert to decibels (dB), a scale that makes those huge ranges easy to compare.
4. Brightness change = after minus before in dB, the same as 10 x log10(after / before)
   (FR-021). New rock or ash changes how the ground reflects, so its brightness changes.
5. Masks: mark the pixels with no usable value, each with its reason (FR-024).
"""
import numpy as np
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.transform import from_origin
from scipy.ndimage import uniform_filter
from shapely import transform as transform_points

GCOV_GROUP = "/science/LSAR/GCOV/grids/frequencyA"
GCOV_DATASETS = ("HHHH", "mask")
SPECKLE_WINDOW = 5

# Values in the product's own `mask` dataset (read from its description)
PRODUCT_MASK_INVALID = 0  # partially focused or invalid radar samples
PRODUCT_MASK_OUTSIDE = 255  # outside the radar acquisition

# No-data codes of the published grid (docs/05 section 5). 0 here means "has a value".
HAS_VALUE = 0
MASKED_BY_PRODUCT = 253
SEA = 254
OUTSIDE_COVERAGE = 255


def valid_power(power):
    """Mark which pixels hold a real power value. NaN, zero and negative are not real."""
    return np.isfinite(power) & (power > 0)


def speckle_filter(power, window=SPECKLE_WINDOW):
    """Average each pixel with its neighbours, ignoring pixels with no value.

    Dividing the sum of good values by the count of good values means a missing
    neighbour can't drag a pixel down. Pixels that had no value stay NaN.
    """
    good = valid_power(power)
    values = np.where(good, power, 0.0).astype("float64")
    average_value = uniform_filter(values, size=window, mode="nearest")
    share_good = uniform_filter(good.astype("float64"), size=window, mode="nearest")
    filtered = np.full(power.shape, np.nan)
    filtered[good] = average_value[good] / share_good[good]
    return filtered


def to_db(power):
    """Convert linear power to dB. Anything that isn't real power becomes NaN."""
    decibels = np.full(np.shape(power), np.nan)
    good = valid_power(np.asarray(power))
    decibels[good] = 10.0 * np.log10(np.asarray(power)[good])
    return decibels


def brightness_change(before_db, after_db):
    """Return after minus before in dB. NaN wherever either pass has no value."""
    return after_db - before_db


def land_mask(land_geometry, x_values, y_values, epsg):
    """Mark which pixels of a UTM grid are on land, from the site's land polygon."""
    to_utm = Transformer.from_crs(4326, epsg, always_xy=True)

    def project(points):
        xs, ys = to_utm.transform(points[:, 0], points[:, 1])
        return np.column_stack([xs, ys])

    projected = transform_points(land_geometry, project)
    spacing_x = abs(x_values[1] - x_values[0])
    spacing_y = abs(y_values[1] - y_values[0])
    corner = from_origin(x_values[0] - spacing_x / 2, y_values[0] + spacing_y / 2, spacing_x, spacing_y)
    burned = rasterize([(projected, 1)], out_shape=(len(y_values), len(x_values)),
                       transform=corner, fill=0, dtype="uint8")
    return burned.astype(bool)


def no_data_reasons(before_mask, after_mask, change_db, is_land):
    """Give every pixel its reason for having no value, or HAS_VALUE (FR-024).

    Sea comes first, so a sea pixel always says "sea". Next is outside coverage, and
    anything else without a value was flagged by the product or has no valid power.
    """
    reasons = np.full(change_db.shape, HAS_VALUE, dtype="uint8")
    flagged = (before_mask == PRODUCT_MASK_INVALID) | (after_mask == PRODUCT_MASK_INVALID)
    reasons[flagged | ~np.isfinite(change_db)] = MASKED_BY_PRODUCT
    outside = (before_mask == PRODUCT_MASK_OUTSIDE) | (after_mask == PRODUCT_MASK_OUTSIDE)
    reasons[outside] = OUTSIDE_COVERAGE
    reasons[~is_land] = SEA
    return reasons


def check_same_grid(before, after):
    """Both passes must sit on the same pixel grid, or the subtraction means nothing."""
    same = (before["x"].shape == after["x"].shape and before["y"].shape == after["y"].shape
            and int(before["epsg"]) == int(after["epsg"])
            and np.allclose(before["x"], after["x"]) and np.allclose(before["y"], after["y"]))
    if not same:
        raise ValueError("The two passes are not on the same pixel grid")


def process_gcov(before, after, land_geometry):
    """Run all the steps on two cropped passes and return the results as a dictionary."""
    check_same_grid(before, after)
    before_db = to_db(speckle_filter(before["HHHH"]))
    after_db = to_db(speckle_filter(after["HHHH"]))
    change_db = brightness_change(before_db, after_db)
    epsg = int(before["epsg"])
    is_land = land_mask(land_geometry, before["x"], before["y"], epsg)
    reasons = no_data_reasons(before["mask"], after["mask"], change_db, is_land)
    change_db[reasons != HAS_VALUE] = np.nan
    return {
        "before_db": before_db,
        "after_db": after_db,
        "change_db": change_db,
        "reasons": reasons,
        "x": before["x"],
        "y": before["y"],
        "epsg": epsg,
        "spacing_x_m": float(abs(before["x"][1] - before["x"][0])),
        "spacing_y_m": float(abs(before["y"][1] - before["y"][0])),
    }

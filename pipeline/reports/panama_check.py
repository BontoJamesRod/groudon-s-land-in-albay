"""Compare the Panama earthquake pair with a published landslide map (T-088).

Run from the project folder, after saving the reference files in the folder named below:
    python -I pipeline/reports/panama_check.py

Reference 1: the Institute of Geosciences, University of Panama, published a map of 9,553
landslides as an image, not a data file. So this reads the black landslide dots from the image.
Reference 2: the USGS ground-failure model, which is a forecast of where landslides are likely.

The map's dots are wider than a radar pixel, so the comparison uses cells a few km across and
says nothing about single landslides. The pair is compared with the quiet pair before it, using
the same steps: if the quiet pair matched the map as well, the match would mean nothing.
Writes panama-check.json here and a picture to pipeline/out/. It publishes nothing.
"""
import json
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject
from scipy.ndimage import binary_dilation, binary_opening, label
from scipy.stats import spearmanr
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "raw" / "context_download" / "panama"
MAP_IMAGE = CACHE / "igc_up_landslides_20261028.jpg"
USGS_MODEL = CACHE / "usgs_jessee_2018_model.tif"
PAIRS = ROOT / "pipeline" / "out" / "sites" / "panama" / "pairs"
EARTHQUAKE_PAIR = "panama_D141F085_20260927_20261009"
QUIET_PAIR = "panama_D141F085_20260915_20260927"
LAND = ROOT / "site" / "data" / "sites" / "panama" / "land.geojson"
OUTPUT = Path(__file__).with_name("panama-check.json")
PICTURE = ROOT / "pipeline" / "out" / "panama-check.png"

# Fixed before the comparison was run.
CELL_KM_MAIN = 2
CELL_KM_OTHERS = (1, 3)
MIN_LAND_SHARE = 0.5  # a cell counts only if at least this share has a radar value
SUPPORTS = {"rho": 0.5, "rho_above_quiet": 0.2, "dense_ratio": 3.0}
WEAK = {"rho": 0.3, "rho_above_quiet": 0.1, "dense_ratio": 1.5}
# Places where the map's own symbols cover the landslide dots.
EPICENTRE = (-80.769, 7.5868)
SYMBOL_RADIUS_DEG = 0.035
REPORTED_CLUSTER = (-80.86495, 7.47737)  # the Eos Landslide Blog's "very dense area"
CLUSTER_RADIUS_KM = 3
KM_PER_DEG = 110.6
# Axis ticks on the image: the longitude and latitude labels printed on the map.
LON_TICKS = [-81.6, -81.4, -81.2, -81.0, -80.8, -80.6, -80.4, -80.2]
LAT_TICKS = [8.0, 7.8, 7.6, 7.4, 7.2]


def tick_centres(strip):
    """Find the middle of each dark tick mark in a line of pixels."""
    centres, start = [], None
    for index, dark in enumerate(list(strip) + [False]):
        if dark and start is None:
            start = index
        if not dark and start is not None:
            centres.append((start + index - 1) / 2)
            start = None
    return centres


def georeference(gray):
    """Fit pixel to degree from the tick marks just outside the map's frame."""
    frame_rows = [y for y in range(gray.shape[0]) if (gray[y] < 110).mean() > 0.5]
    frame_cols = [x for x in range(gray.shape[1]) if (gray[:, x] < 110).mean() > 0.5]
    left, right, bottom = frame_cols[0], frame_cols[-1], frame_rows[-1]
    x_ticks = tick_centres(gray[bottom + 4, left:right + 1] < 140)
    y_ticks = tick_centres(gray[frame_rows[0]:bottom + 1, left - 4] < 140)
    x_ticks = [x + left for x in x_ticks]
    y_ticks = [y + frame_rows[0] for y in y_ticks]
    if len(x_ticks) != len(LON_TICKS) or len(y_ticks) != len(LAT_TICKS):
        raise RuntimeError(f"Expected {len(LON_TICKS)} and {len(LAT_TICKS)} ticks, found {x_ticks} and {y_ticks}")
    lon = np.polyfit(x_ticks, LON_TICKS, 1)
    lat = np.polyfit(y_ticks, LAT_TICKS, 1)
    residual = max(np.abs(np.polyval(lon, x_ticks) - LON_TICKS).max(), np.abs(np.polyval(lat, y_ticks) - LAT_TICKS).max())
    return lon, lat, float(residual)


def read_grid(pair_id):
    """Read a pair's class grid and bounds. Row 0 is the northern edge (docs/06, API-010)."""
    pair = json.loads((PAIRS / pair_id / "pair.json").read_text(encoding="utf-8"))["data"]
    layer = next(item for item in pair["layers"] if item["kind"] == "new_material")
    grid = np.fromfile(PAIRS / pair_id / layer["grid_path"], dtype="uint8").reshape(layer["grid_height"], layer["grid_width"])
    return grid, (layer["bounds_west"], layer["bounds_south"], layer["bounds_east"], layer["bounds_north"])


def landslide_mask(rgb, lon, lat, bounds, shape_out):
    """Read the black dots and put them on the radar grid's rows and columns."""
    dots = (rgb.max(axis=2) < 70)
    # Dots are about 5 pixels wide. Fault lines, borders and text are thinner, so this removes them.
    dots = binary_opening(dots, structure=np.ones((4, 4), dtype=bool))
    west, south, east, north = bounds
    height, width = shape_out
    lons = west + (np.arange(width) + 0.5) * (east - west) / width
    lats = north - (np.arange(height) + 0.5) * (north - south) / height
    # Turn degrees back into image pixels.
    columns = np.rint((lons - lon[1]) / lon[0]).astype(int)
    rows = np.rint((lats - lat[1]) / lat[0]).astype(int)
    result = dots[np.ix_(rows, columns)]
    grid_lon, grid_lat = np.meshgrid(lons, lats)
    covered = np.hypot(grid_lon - EPICENTRE[0], grid_lat - EPICENTRE[1]) < SYMBOL_RADIUS_DEG
    return result, covered, grid_lon, grid_lat


def coast_check(rgb, lon, lat, bounds):
    """Test the georeferencing: slide the map over our land shape and find the best fit."""
    west, south, east, north = bounds
    land_shape = shape(json.loads(LAND.read_text(encoding="utf-8"))["features"][0]["geometry"])
    size = 400
    land = rasterize([land_shape], out_shape=(size, size), transform=from_bounds(west, south, east, north, size, size)).astype(bool)
    lons = west + (np.arange(size) + 0.5) * (east - west) / size
    lats = north - (np.arange(size) + 0.5) * (north - south) / size
    # The map paints the sea pale blue.
    sea = (rgb[..., 2].astype(int) > 220) & (rgb[..., 0].astype(int) > 190) & (rgb[..., 1].astype(int) > 210)
    best = None
    scores = {}
    for shift_x in range(-12, 13):
        for shift_y in range(-12, 13):
            columns = np.rint((lons - lon[1]) / lon[0]).astype(int) + shift_x
            rows = np.rint((lats - lat[1]) / lat[0]).astype(int) + shift_y
            score = float(((~sea[np.ix_(rows, columns)]) == land).mean())
            scores[(shift_x, shift_y)] = score
            if best is None or score > best[0]:
                best = (score, shift_x, shift_y)
    return {"agreement_as_fitted": round(scores[(0, 0)], 4), "best_agreement": round(best[0], 4), "best_shift_pixels": [best[1], best[2]],
            "pixel_m": round(abs(lon[0]) * KM_PER_DEG * 1000)}


def cells(values, weights, grid_lon, grid_lat, bounds, cell_km):
    """Share of `values` among `weights` pixels in each square cell, as a flat array."""
    west, south, _, north = bounds
    step = cell_km / KM_PER_DEG
    x = ((grid_lon - west) / step).astype(int)
    y = ((north - grid_lat) / step).astype(int)
    key = y * 10000 + x
    ids, inverse = np.unique(key, return_inverse=True)
    inverse = inverse.ravel()
    total = np.bincount(inverse, minlength=len(ids)).astype(float)
    good = np.bincount(inverse, weights=weights.ravel(), minlength=len(ids)).astype(float)
    hits = np.bincount(inverse, weights=(values & weights).ravel(), minlength=len(ids)).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        share = hits / good
    return share, good / total, inverse.reshape(key.shape), good


def compare(grid, slides, usable, usgs, grid_lon, grid_lat, bounds, cell_km):
    """Compare a pair's flagged cells with the map's landslides, cell by cell."""
    flagged = np.isin(grid, (1, 2))
    high = grid == 2
    flagged_share, enough, _, _ = cells(flagged, usable, grid_lon, grid_lat, bounds, cell_km)
    high_share, _, _, _ = cells(high, usable, grid_lon, grid_lat, bounds, cell_km)
    slide_share, _, _, good = cells(slides, usable, grid_lon, grid_lat, bounds, cell_km)
    with np.errstate(invalid="ignore", divide="ignore"):
        usgs_share = np.bincount(cells(flagged, usable, grid_lon, grid_lat, bounds, cell_km)[2].ravel(), weights=(np.nan_to_num(usgs) * usable).ravel()) / good
    keep = enough >= MIN_LAND_SHARE
    flagged_share, high_share, slide_share, usgs_share = flagged_share[keep], high_share[keep], slide_share[keep], usgs_share[keep]
    dense = slide_share >= np.quantile(slide_share, 0.75)
    none = slide_share == 0
    def mean(values):
        return float(values.mean()) if len(values) else None
    dense_mean, rest_mean = mean(flagged_share[dense]), mean(flagged_share[~dense])
    return {
        "cells": int(keep.sum()), "cells_dense": int(dense.sum()), "cells_no_landslides": int(none.sum()),
        "rho_map": round(float(spearmanr(flagged_share, slide_share)[0]), 3),
        "rho_map_high_only": round(float(spearmanr(high_share, slide_share)[0]), 3),
        "rho_usgs": round(float(spearmanr(flagged_share, usgs_share)[0]), 3),
        "flagged_share_dense_cells": round(dense_mean, 4), "flagged_share_other_cells": round(rest_mean, 4),
        "flagged_share_no_landslide_cells": round(mean(flagged_share[none]), 4) if none.any() else None,
        "dense_ratio": round(dense_mean / rest_mean, 2) if rest_mean else None,
        "share_of_flagged_in_dense_cells": round(float(flagged_share[dense].sum() / flagged_share.sum()), 3),
        "share_of_flagged_in_no_landslide_cells": round(float(flagged_share[none].sum() / flagged_share.sum()), 3),
    }


def pixel_overlap(grid, slides, usable):
    """Flagged share on the map's dots against everywhere else. Dots are wider than landslides."""
    flagged = np.isin(grid, (1, 2))
    on_dots, off_dots = usable & slides, usable & ~slides
    return {"flagged_share_on_dots": round(float(flagged[on_dots].mean()), 4), "flagged_share_off_dots": round(float(flagged[off_dots].mean()), 4),
            "share_of_flagged_on_dots": round(float((flagged & on_dots).sum() / (flagged & usable).sum()), 3),
            "share_of_usable_land_on_dots": round(float(on_dots.sum() / usable.sum()), 3)}


def around_reported_cluster(grid, usable, grid_lon, grid_lat):
    """Flagged share within a few km of the place the Eos Landslide Blog names."""
    near = np.hypot(grid_lon - REPORTED_CLUSTER[0], grid_lat - REPORTED_CLUSTER[1]) * KM_PER_DEG <= CLUSTER_RADIUS_KM
    flagged = np.isin(grid, (1, 2))
    return {"within_km": CLUSTER_RADIUS_KM, "flagged_share_near": round(float(flagged[near & usable].mean()), 4), "flagged_share_elsewhere": round(float(flagged[~near & usable].mean()), 4)}


def largest_patches_off_the_map(grid, slides, usable, grid_lon, grid_lat, bounds, count=6):
    """The biggest flagged patches with no landslide dot nearby: places to check by eye."""
    flagged = np.isin(grid, (1, 2)) & usable
    near_dots = binary_dilation(slides, iterations=25)
    labels, found = label(flagged)
    sizes = np.bincount(labels.ravel(), minlength=found + 1)
    sizes[0] = 0
    cell_km2 = ((bounds[2] - bounds[0]) * KM_PER_DEG / grid.shape[1]) * ((bounds[3] - bounds[1]) * KM_PER_DEG / grid.shape[0])
    patches = []
    for number in np.argsort(sizes)[::-1]:
        if sizes[number] == 0 or len(patches) == count:
            break
        cells_here = labels == number
        if near_dots[cells_here].any():
            continue
        patches.append({"lat": round(float(grid_lat[cells_here].mean()), 4), "lon": round(float(grid_lon[cells_here].mean()), 4),
                        "area_km2": round(float(sizes[number]) * cell_km2, 3), "high_share": round(float((grid[cells_here] == 2).mean()), 2)})
    return patches


def verdict(result):
    """Apply the fixed criteria to the main cell size."""
    quake, quiet = result["earthquake"], result["quiet"]
    above = quake["rho_map"] - quiet["rho_map"]
    for name, limits in (("SUPPORTS", SUPPORTS), ("WEAK SUPPORT", WEAK)):
        if quake["rho_map"] >= limits["rho"] and above >= limits["rho_above_quiet"] and (quake["dense_ratio"] or 0) >= limits["dense_ratio"]:
            return name
    return "DOES NOT SUPPORT"


def save_picture(grid, slides, usable, bounds):
    """A picture to check by eye. It stays in pipeline/out, because it copies the published map's dots."""
    picture = np.full(grid.shape + (3,), 235, dtype="uint8")
    picture[~usable] = (190, 215, 235)
    picture[slides & usable] = (160, 160, 160)
    picture[np.isin(grid, (1, 2))] = (213, 94, 0)
    Image.fromarray(picture).resize((grid.shape[1] // 2, grid.shape[0] // 2), Image.NEAREST).save(PICTURE)


def main():
    rgb = np.array(Image.open(MAP_IMAGE).convert("RGB"))
    lon, lat, residual = georeference(np.array(Image.open(MAP_IMAGE).convert("L")).astype(int))
    quake_grid, bounds = read_grid(EARTHQUAKE_PAIR)
    quiet_grid, quiet_bounds = read_grid(QUIET_PAIR)
    if quiet_bounds != bounds or quiet_grid.shape != quake_grid.shape:
        raise RuntimeError("The two pairs must share a grid")
    slides, covered, grid_lon, grid_lat = landslide_mask(rgb, lon, lat, bounds, quake_grid.shape)
    # Class values 0, 1 and 2 have a radar value in both pairs. No-data codes are 253 and up.
    usable = (quake_grid <= 2) & (quiet_grid <= 2) & ~covered
    usgs = np.zeros(quake_grid.shape, dtype="float64")
    with rasterio.open(USGS_MODEL) as source:
        reproject(rasterio.band(source, 1), usgs, dst_transform=from_bounds(*bounds, quake_grid.shape[1], quake_grid.shape[0]), dst_crs="EPSG:4326", resampling=Resampling.bilinear)
    result = {"tick_fit_residual_deg": round(residual, 5), "coast_check": coast_check(rgb, lon, lat, bounds),
              "usable_land_km2": round(float(usable.sum()) * ((bounds[2] - bounds[0]) * KM_PER_DEG / quake_grid.shape[1]) * ((bounds[3] - bounds[1]) * KM_PER_DEG / quake_grid.shape[0]), 1),
              "dots_share_of_usable_land": round(float((slides & usable).sum() / usable.sum()), 3)}
    for cell_km in (CELL_KM_MAIN, *CELL_KM_OTHERS):
        one = {name: compare(grid, slides, usable, usgs, grid_lon, grid_lat, bounds, cell_km) for name, grid in (("earthquake", quake_grid), ("quiet", quiet_grid))}
        if cell_km == CELL_KM_MAIN:
            result.update(one)
            result["verdict"] = verdict(one)
        else:
            result[f"sensitivity_{cell_km}_km"] = {"verdict": verdict(one), "earthquake": one["earthquake"], "quiet": one["quiet"]}
    result["pixel_overlap"] = {"earthquake": pixel_overlap(quake_grid, slides, usable), "quiet": pixel_overlap(quiet_grid, slides, usable)}
    result["reported_cluster"] = {"earthquake": around_reported_cluster(quake_grid, usable, grid_lon, grid_lat), "quiet": around_reported_cluster(quiet_grid, usable, grid_lon, grid_lat)}
    result["largest_patches_off_the_map"] = largest_patches_off_the_map(quake_grid, slides, usable, grid_lon, grid_lat, bounds)
    OUTPUT.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    save_picture(quake_grid, slides, usable, bounds)
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()

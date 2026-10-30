"""Tests for the data contract check (T-006, TC-048, TC-059)."""
import copy
import json

import pytest
from PIL import Image

from mrw.contract_check import check_data_dir, main

STAMP = "2026-11-04T09:00:00Z"
META = {"generated_at": STAMP, "schema_version": "1.0"}
PAIR_ID = "mayon_A111F008_20261007_20261019"
RING = [[[123.70, 13.33], [123.76, 13.33], [123.76, 13.38], [123.70, 13.38], [123.70, 13.33]]]
LOOPS = (("before_db", "before_db.png"), ("after_db", "after_db.png"),
         ("change_db", "change_db.png"), ("coherence_loss", "coherence_loss.png"),
         ("new_material", "new_material.png"))


def site_row():
    return {
        "id": "mayon", "name": "Mayon Volcano, Albay", "country": "Philippines",
        "status": "published", "time_zone": "Asia/Manila",
        "center_lat": 13.2572, "center_lon": 123.6856,
        "bounds_west": 123.56, "bounds_south": 13.14, "bounds_east": 123.81, "bounds_north": 13.38,
        "default_zoom": 12, "min_zoom": 10, "max_zoom": 16,
        "summit_lat": 13.2572, "summit_lon": 123.6856, "danger_zone_radius_km": 6,
        "danger_zone_label": "Permanent Danger Zone (6 km)", "change_types": ["new_material"],
        "created_at": STAMP, "updated_at": STAMP,
    }


def source_row():
    return {
        "id": "ph_admin_boundaries", "name": "Boundaries", "provider": "OCHA",
        "used_for": "boundaries", "url": "https://github.com/x", "license": "CC BY-IGO",
        "retrieved_on": "2026-10-31", "created_at": STAMP, "updated_at": STAMP,
    }


def pass_row(stamp, iso):
    return {
        "id": f"A111F008_{stamp}", "site_id": "mayon", "mission": "NISAR", "product_type": "GCOV",
        "granule_id": f"GRANULE_{stamp}", "track": 111, "frame": 8,
        "orbit_direction": "ascending", "cycle": 32,
        "acquired_start": iso, "acquired_end": iso, "polarizations": ["HHHH"],
        "pixel_spacing_m": 10, "maturity": "PROVISIONAL", "vertex_url": "https://search.asf.alaska.edu/x",
        "created_at": STAMP, "updated_at": STAMP,
    }


def layer_row(kind, image_path):
    is_class = kind == "new_material"
    return {
        "id": f"{PAIR_ID}_{kind}", "pair_id": PAIR_ID, "kind": kind, "title": kind, "units": "class",
        "image_path": image_path, "image_format": "png",
        "bounds_west": 123.56, "bounds_south": 13.14, "bounds_east": 123.81, "bounds_north": 13.38,
        "image_width": 4, "image_height": 3,
        "grid_path": "new_material.bin" if is_class else None,
        "grid_dtype": "uint8" if is_class else None,
        "grid_scale": 1 if is_class else None,
        "grid_nodata": None,
        "no_data_codes": {"253": "masked_by_product", "254": "sea", "255": "outside_coverage"} if is_class else None,
        "grid_width": 4 if is_class else None,
        "grid_height": 3 if is_class else None,
        "color_scale_min": None, "color_scale_max": None,
        "legend": [{"value": 1, "label": "Low", "color": "#E69F00", "confidence": "low"}],
        "source_granule_ids": ["GRANULE"],
        "created_at": STAMP, "updated_at": STAMP,
    }


def pair_row():
    return {
        "id": PAIR_ID, "site_id": "mayon", "status": "published", "track": 111, "frame": 8,
        "orbit_direction": "ascending",
        "before_pass_id": "A111F008_20261007T211319", "after_pass_id": "A111F008_20261019T211319",
        "before_acquired_start": "2026-10-07T21:13:19Z",
        "after_acquired_start": "2026-10-19T21:13:19Z",
        "previous_pair_id": "mayon_A111F008_20260925_20261007",
        "gunw_granule_id": "GUNW", "gunw_vertex_url": "https://search.asf.alaska.edu/y",
        "coherence_used": True, "brightness_threshold_db": 3.0, "coherence_loss_threshold": 0.3,
        "high_confidence_area_km2": 0.05, "low_confidence_area_km2": 0.21,
        "new_material_area_km2": 0.26, "pipeline_version": "0.1.0", "error_message": None,
        "published_at": STAMP, "created_at": STAMP, "updated_at": STAMP,
    }


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content), encoding="utf-8")


def envelope(data):
    return {"data": data, "meta": META}


def collection(features):
    return {"type": "FeatureCollection", "generated_at": STAMP, "schema_version": "1.0",
            "features": features}


def town_feature():
    return {
        "type": "Feature", "id": "mayon_tabaco_city",
        "properties": {"id": "mayon_tabaco_city", "site_id": "mayon", "name": "Tabaco City",
                       "kind": "city", "label_lat": 13.35, "label_lon": 123.73,
                       "source_code": None, "source_id": "ph_admin_boundaries"},
        "geometry": {"type": "Polygon", "coordinates": RING},
    }


def land_feature():
    return {
        "type": "Feature", "id": "mayon_land",
        "properties": {"id": "mayon_land", "site_id": "mayon", "source_id": "ph_admin_boundaries"},
        "geometry": {"type": "MultiPolygon", "coordinates": [RING]},
    }


@pytest.fixture
def data_dir(tmp_path):
    """Build one small data folder that fully follows the contract."""
    root = tmp_path / "data"
    write(root / "sites.json", envelope([site_row()]))
    write(root / "sources.json", envelope([source_row()]))
    site = root / "sites" / "mayon"
    write(site / "towns.geojson", collection([town_feature()]))
    write(site / "land.geojson", collection([land_feature()]))
    write(site / "events.json", envelope([]))
    write(site / "pairs.json", envelope([pair_row()]))
    folder = site / "pairs" / PAIR_ID
    full = pair_row()
    full["passes"] = [pass_row("20261007T211319", "2026-10-07T21:13:19Z"),
                      pass_row("20261019T211319", "2026-10-19T21:13:19Z")]
    full["layers"] = [layer_row(kind, path) for kind, path in LOOPS]
    write(folder / "pair.json", envelope(full))
    for _kind, path in LOOPS:
        Image.new("RGBA", (4, 3)).save(folder / path)
    (folder / "new_material.bin").write_bytes(bytes([0, 1, 2, 253, 254, 255, 0, 0, 0, 0, 0, 0]))
    return root


def edit_json(path, change):
    """Load a JSON file, let a test break it, and save it again."""
    content = json.loads(path.read_text(encoding="utf-8"))
    change(content)
    path.write_text(json.dumps(content), encoding="utf-8")


def pair_path(root):
    return root / "sites" / "mayon" / "pairs" / PAIR_ID / "pair.json"


def test_correct_files_pass(data_dir):
    assert check_data_dir(data_dir) == []


def test_empty_folder_fails_when_published(tmp_path):
    assert any("required file is missing" in e for e in check_data_dir(tmp_path))


def test_empty_folder_is_fine_for_unpublished_output(tmp_path):
    assert check_data_dir(tmp_path, published=False) == []


@pytest.mark.parametrize("name", ["sources.json", "sites.json", "sites/mayon/towns.geojson", "sites/mayon/land.geojson", "sites/mayon/pairs.json"])
def test_missing_required_file_fails(data_dir, name):
    (data_dir / name).unlink()
    assert any("is missing" in e or "not listed" in e for e in check_data_dir(data_dir))


def test_row_must_match_its_pair_file(data_dir):
    def change(content):
        content["data"][0].update(high_confidence_area_km2=1.0, low_confidence_area_km2=1.0, new_material_area_km2=2.0)
    edit_json(data_dir / "sites" / "mayon" / "pairs.json", change)
    assert any("differs from pair.json" in e for e in check_data_dir(data_dir))


def test_nan_in_json_fails(data_dir):
    path = data_dir / "sources.json"
    path.write_text(path.read_text(encoding="utf-8").replace("[{", "[{\"x\": NaN, "), encoding="utf-8")
    assert any("can't be read as JSON" in e for e in check_data_dir(data_dir))


def test_unknown_time_zone_fails(data_dir):
    edit_json(data_dir / "sites.json", lambda c: c["data"][0].update(time_zone="Foo/Bar"))
    assert any("unknown time zone" in e for e in check_data_dir(data_dir))


def test_area_off_by_one_hundredth_fails(data_dir):
    edit_json(pair_path(data_dir), lambda c: c["data"].update(new_material_area_km2=0.27))
    assert any("high + low" in e for e in check_data_dir(data_dir))


def test_coherence_needs_its_products(data_dir):
    edit_json(pair_path(data_dir), lambda c: c["data"].update(gunw_granule_id=None))
    assert any("coherence needs" in e for e in check_data_dir(data_dir))


def test_same_granule_twice_fails(data_dir):
    def change(content):
        content["data"]["passes"][1]["granule_id"] = content["data"]["passes"][0]["granule_id"]
    edit_json(pair_path(data_dir), change)
    assert any("different granule_id" in e for e in check_data_dir(data_dir))


def test_new_material_needs_no_data_codes(data_dir):
    def change(content):
        next(l for l in content["data"]["layers"] if l["kind"] == "new_material")["no_data_codes"] = None
    edit_json(pair_path(data_dir), change)
    assert any("no_data_codes" in e for e in check_data_dir(data_dir))


def test_high_cells_without_coherence_fail(data_dir):
    def change(content):
        content["data"].update(coherence_used=False, coherence_loss_threshold=None, high_confidence_area_km2=0, new_material_area_km2=0.21)
    edit_json(pair_path(data_dir), change)
    assert any("without coherence" in e for e in check_data_dir(data_dir))


def test_broken_json_fails(data_dir):
    (data_dir / "sources.json").write_text("{not json", encoding="utf-8")
    assert any("can't be read as JSON" in e for e in check_data_dir(data_dir))


def test_missing_envelope_fails(data_dir):
    write(data_dir / "sources.json", [source_row()])
    assert any("envelope" in e for e in check_data_dir(data_dir))


def test_wrong_schema_version_fails(data_dir):
    edit_json(data_dir / "sources.json", lambda c: c["meta"].update(schema_version="9.9"))
    assert any("schema_version" in e for e in check_data_dir(data_dir))


def test_unlisted_file_fails(data_dir):
    write(data_dir / "extra.json", envelope([]))
    assert any("not part of the data contract" in e for e in check_data_dir(data_dir))


@pytest.mark.parametrize("name,value,message", [
    ("status", "draft", "only published sites"),
    ("bounds_west", 124.0, "reversed"),
    ("default_zoom", 3, "zooms"),
    ("center_lat", "north", "should be number"),
    ("center_lat", 95, "above 90"),
    ("id", "Mayon Site", "invalid format"),
    ("danger_zone_label", None, "danger_zone_label"),
    ("change_types", ["lava"], "change_types"),
])
def test_bad_site_values_fail(data_dir, name, value, message):
    edit_json(data_dir / "sites.json", lambda c: c["data"][0].update({name: value}))
    assert any(message in e for e in check_data_dir(data_dir))


def test_unknown_and_missing_fields_fail(data_dir):
    def change(content):
        content["data"][0]["colour"] = "red"
        del content["data"][0]["country"]
    edit_json(data_dir / "sites.json", change)
    errors = check_data_dir(data_dir)
    assert any("unknown field 'colour'" in e for e in errors)
    assert any("missing required field 'country'" in e for e in errors)


def test_label_outside_polygon_fails(data_dir):
    path = data_dir / "sites" / "mayon" / "towns.geojson"
    edit_json(path, lambda c: c["features"][0]["properties"].update(label_lat=10.0))
    assert any("label point" in e for e in check_data_dir(data_dir))


def test_invalid_geometry_fails(data_dir):
    bow_tie = [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]
    path = data_dir / "sites" / "mayon" / "land.geojson"
    edit_json(path, lambda c: c["features"][0]["geometry"].update(type="Polygon", coordinates=bow_tie))
    assert any("empty or invalid" in e for e in check_data_dir(data_dir))


def test_unknown_source_fails(data_dir):
    path = data_dir / "sites" / "mayon" / "land.geojson"
    edit_json(path, lambda c: c["features"][0]["properties"].update(source_id="nope"))
    assert any("not in sources.json" in e for e in check_data_dir(data_dir))


def test_unpublished_pair_in_list_fails(data_dir):
    path = data_dir / "sites" / "mayon" / "pairs.json"
    edit_json(path, lambda c: c["data"][0].update(status="ready"))
    assert any("FR-059" in e for e in check_data_dir(data_dir))


def test_unlisted_pair_folder_fails(data_dir):
    write(data_dir / "sites" / "mayon" / "pairs.json", envelope([]))
    assert any("not listed in pairs.json" in e for e in check_data_dir(data_dir))


def test_area_sum_mismatch_fails(data_dir):
    edit_json(pair_path(data_dir), lambda c: c["data"].update(new_material_area_km2=5.0))
    assert any("high + low" in e for e in check_data_dir(data_dir))


def test_no_coherence_cannot_have_threshold_or_high_area(data_dir):
    edit_json(pair_path(data_dir), lambda c: c["data"].update(coherence_used=False))
    errors = check_data_dir(data_dir)
    assert any("must be null without coherence" in e for e in errors)
    assert any("FR-030" in e for e in errors)


def test_wrong_pass_count_fails(data_dir):
    edit_json(pair_path(data_dir), lambda c: c["data"]["passes"].pop())
    assert any("exactly 2 passes" in e for e in check_data_dir(data_dir))


def test_mixed_track_pass_fails(data_dir):
    edit_json(pair_path(data_dir), lambda c: c["data"]["passes"][0].update(track=104))
    assert any("FR-027" in e for e in check_data_dir(data_dir))


def test_bad_maturity_fails(data_dir):
    edit_json(pair_path(data_dir), lambda c: c["data"]["passes"][0].update(maturity="FINAL"))
    assert any("maturity" in e for e in check_data_dir(data_dir))


def test_layer_without_legend_fails(data_dir):
    edit_json(pair_path(data_dir), lambda c: c["data"]["layers"][0].pop("legend"))
    assert any("'legend'" in e for e in check_data_dir(data_dir))


def test_missing_layer_kind_fails(data_dir):
    edit_json(pair_path(data_dir), lambda c: c["data"]["layers"].pop(0))
    assert any("layers missing" in e for e in check_data_dir(data_dir))


def test_wrong_image_size_fails(data_dir):
    folder = pair_path(data_dir).parent
    Image.new("RGBA", (9, 9)).save(folder / "before_db.png")
    assert any("image is 9 x 9" in e for e in check_data_dir(data_dir))


def test_missing_image_fails(data_dir):
    (pair_path(data_dir).parent / "before_db.png").unlink()
    assert any("image file before_db.png is missing" in e for e in check_data_dir(data_dir))


def test_wrong_grid_size_fails(data_dir):
    (pair_path(data_dir).parent / "new_material.bin").write_bytes(b"\x00" * 5)
    assert any("grid has 5 bytes" in e for e in check_data_dir(data_dir))


def test_invalid_grid_value_fails(data_dir):
    (pair_path(data_dir).parent / "new_material.bin").write_bytes(bytes([7]) * 12)
    assert any("invalid cell values" in e for e in check_data_dir(data_dir))


def test_ready_pair_allowed_only_when_unpublished_mode(data_dir):
    def make_ready(content):
        content["data"].update(status="ready", published_at=None)
    write(data_dir / "sites" / "mayon" / "pairs.json", envelope([]))
    edit_json(pair_path(data_dir), make_ready)
    assert check_data_dir(data_dir, published=False) == []
    assert any("FR-059" in e for e in check_data_dir(data_dir, published=True))


def test_command_line_exit_codes(data_dir, capsys):
    assert main([str(data_dir)]) == 0
    (data_dir / "sources.json").write_text("broken", encoding="utf-8")
    assert main([str(data_dir)]) == 1
    assert "error(s)" in capsys.readouterr().out


def test_fixture_builders_are_independent():
    first = site_row()
    second = copy.deepcopy(first)
    second["id"] = "other"
    assert first["id"] == "mayon"

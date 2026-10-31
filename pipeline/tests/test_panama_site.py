"""Tests for the Panama site files (T-036, T-037, T-086, T-089)."""
import json
from pathlib import Path

from mrw.config import load_site
from mrw.publish import rebuild_sites_list

DATA = Path(__file__).resolve().parents[2] / "site" / "data"
LICENSE = "CC BY-SA 4.0"
QUIET = "panama_D141F085_20260915_20260927"
EARTHQUAKE = "panama_D141F085_20260927_20261009"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_panama_uses_the_same_final_rule_with_no_tuning():
    assert load_site("panama")["thresholds"] == load_site("mayon")["thresholds"]
    assert load_site("panama")["thresholds"]["status"] == "FINAL"


def test_each_site_only_has_its_own_boundary_source():
    rows = {row["id"]: row for row in read(DATA / "sources.json")["data"]}
    assert rows["pa_admin_boundaries"]["site_id"] == "panama"
    assert rows["ph_admin_boundaries"]["site_id"] == "mayon"
    assert "site_id" not in rows["esri_world_imagery"]


def test_panama_has_no_channels_summit_or_reach():
    config = load_site("panama")
    assert config["summit_lat"] is None and "filters" not in config and "channel_strip_half_width_m" not in config
    assert not (DATA / "sites" / "panama" / "channels.geojson").exists()


def test_both_border_files_carry_the_license_of_their_source():
    source = next(row for row in read(DATA / "sources.json")["data"] if row["id"] == "pa_admin_boundaries")
    assert source["license"] == LICENSE and "geoBoundaries" in source["provider"]
    for name in ("towns.geojson", "land.geojson"):
        content = read(DATA / "sites" / "panama" / name)
        assert content["license"] == LICENSE
        assert {feature["properties"]["source_id"] for feature in content["features"]} == {"pa_admin_boundaries"}


def test_a_draft_site_stays_out_of_the_site_list(tmp_path):
    config = {**load_site("panama"), "status": "draft"}
    folder = tmp_path / "configs"
    folder.mkdir()
    (folder / "panama.json").write_text(json.dumps(config), encoding="utf-8")
    (tmp_path / "sites" / "panama").mkdir(parents=True)
    rebuild_sites_list(tmp_path, "2026-11-01T00:00:00Z", sites_folder=folder)
    assert read(tmp_path / "sites.json")["data"] == []


def test_both_pairs_are_published_and_the_earthquake_pair_is_last():
    pairs = read(DATA / "sites" / "panama" / "pairs.json")["data"]
    assert [pair["id"] for pair in pairs] == [QUIET, EARTHQUAKE]
    assert pairs[1]["previous_pair_id"] == QUIET


def test_the_earthquake_pair_says_changed_and_never_landslides():
    for pair_id, title in ((QUIET, "Radar change"), (EARTHQUAKE, "Changed after the earthquake")):
        record = read(DATA / "sites" / "panama" / "pairs" / pair_id / "pair.json")
        layer = next(item for item in record["data"]["layers"] if item["kind"] == "new_material")
        assert layer["title"] == title
        assert "landslide" not in json.dumps(record).lower() and "new material" not in json.dumps(record).lower()


def test_the_check_cites_the_map_and_states_its_limits():
    record = read(DATA / "sites" / "panama" / "pairs" / EARTHQUAKE / "validation.json")["data"]
    assert "University of Panama" in record["source_name"] and record["source_url"].startswith("https://www.laestrella.com.pa/")
    assert "doesn't show that any one colored spot" in record["method"] and "27%" in record["method"] and "Oct 23" in record["method"]
    assert not list((DATA / "sites" / "panama").rglob("*.jpg"))

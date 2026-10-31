"""Tests for the Panama site files (T-036, T-086). Panama stays a draft until T-037."""
import json
from pathlib import Path

from mrw.config import load_site
from mrw.publish import rebuild_sites_list

DATA = Path(__file__).resolve().parents[2] / "site" / "data"
LICENSE = "CC BY-SA 4.0"


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
    (tmp_path / "sites" / "panama").mkdir(parents=True)
    rebuild_sites_list(tmp_path, "2026-11-01T00:00:00Z")
    assert read(tmp_path / "sites.json")["data"] == []
    assert [row["id"] for row in read(DATA / "sites.json")["data"]] == ["mayon"]

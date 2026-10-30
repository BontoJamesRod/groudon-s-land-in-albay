"""Tests for the publish module (T-019, TC-049)."""
import json
import shutil

import pytest

from mrw.config import SITES_FOLDER
from mrw.contract_check import check_data_dir
from mrw.context import DATA_FOLDER
from mrw.publish import PublishError, publish_pair
from test_export import write_fake

PAIR = "mayon_A111F008_20261007_20261019"


def read_data(path):
    return json.loads(path.read_text(encoding="utf-8"))["data"]


@pytest.fixture
def folders(tmp_path):
    """A processed pair in out/, and a data folder holding only the context files."""
    out, data = tmp_path / "out", tmp_path / "data"
    out.mkdir()
    write_fake(out)
    (data / "sites" / "mayon").mkdir(parents=True)
    shutil.copy(DATA_FOLDER / "sources.json", data / "sources.json")
    for name in ("towns.geojson", "land.geojson"):
        shutil.copy(DATA_FOLDER / "sites" / "mayon" / name, data / "sites" / "mayon" / name)
    return out, data


def run(out, data, pair=PAIR):
    return publish_pair("mayon", pair, out_folder=out, data_folder=data, sites_folder=SITES_FOLDER)


def test_publish_sets_status_and_lists_the_pair(folders):
    out, data = folders
    pair = run(out, data)
    assert pair["status"] == "published" and pair["published_at"]
    assert check_data_dir(data) == []
    listed = read_data(data / "sites" / "mayon" / "pairs.json")
    assert [row["id"] for row in listed] == [PAIR]
    assert "passes" not in listed[0] and "layers" not in listed[0]
    assert read_data(data / "sites.json")[0]["id"] == "mayon"


def test_output_copy_stays_ready(folders):
    out, data = folders
    run(out, data)
    assert read_data(out / "sites" / "mayon" / "pairs" / PAIR / "pair.json")["status"] == "ready"


def test_tc049_unpublished_pairs_stay_out_of_the_data_folder(folders, tmp_path):
    out, data = folders
    other = out / "sites" / "mayon" / "pairs" / "mayon_A111F008_20260925_20261007"
    assert not other.exists()
    run(out, data)
    assert [p.name for p in (data / "sites" / "mayon" / "pairs").iterdir()] == [PAIR]


def test_publishing_again_replaces_the_pair_and_keeps_created_at(folders):
    out, data = folders
    run(out, data)
    first = read_data(data / "sites.json")[0]["created_at"]
    run(out, data)
    assert read_data(data / "sites.json")[0]["created_at"] == first
    assert len(read_data(data / "sites" / "mayon" / "pairs.json")) == 1
    assert check_data_dir(data) == []


def test_missing_pair_stops(folders):
    out, data = folders
    with pytest.raises(PublishError):
        run(out, data, "mayon_A111F008_20200101_20200113")


def test_invalid_output_stops_and_changes_nothing(folders):
    out, data = folders
    (out / "sites" / "mayon" / "pairs" / PAIR / "new_material.bin").write_bytes(b"short")
    with pytest.raises(PublishError):
        run(out, data)
    assert not list((data / "sites" / "mayon").glob("pairs/*"))
    assert not (data / "sites.json").exists()

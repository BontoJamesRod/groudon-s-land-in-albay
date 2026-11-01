"""Tests for the publish module (T-019, TC-049)."""
import json
import shutil

import pytest

from mrw.config import SITES_FOLDER
from mrw.contract_check import check_data_dir, relief_tile_range
from mrw.context import DATA_FOLDER
from mrw.publish import PublishError, publish_pair
from test_export import write_fake

PAIR = "mayon_A111F008_20261007_20261019"


def read_data(path):
    return json.loads(path.read_text(encoding="utf-8"))["data"]


def add_empty_relief_tiles(data):
    """The contract wants Mayon's relief tiles to be there, and publishing never touches them."""
    site = json.loads((SITES_FOLDER / "mayon.json").read_text(encoding="utf-8"))
    bounds = [site[f"relief_bounds_{side}"] for side in ("west", "south", "east", "north")]
    for zoom in range(site["min_zoom"], site["relief_max_native_zoom"] + 1):
        x_low, y_low, x_high, y_high = relief_tile_range(bounds, zoom)
        for x in range(x_low, x_high + 1):
            folder = data / "sites" / "mayon" / "relief" / str(zoom) / str(x)
            folder.mkdir(parents=True)
            for y in range(y_low, y_high + 1):
                (folder / f"{y}.webp").touch()


@pytest.fixture
def folders(tmp_path):
    """A processed pair in out/, and a data folder holding only the context files."""
    out, data = tmp_path / "out", tmp_path / "data"
    out.mkdir()
    write_fake(out)
    (data / "sites" / "mayon").mkdir(parents=True)
    shutil.copytree(DATA_FOLDER / "sites" / "panama", data / "sites" / "panama")  # the other published site
    shutil.copy(DATA_FOLDER / "sources.json", data / "sources.json")
    for name in ("towns.geojson", "land.geojson", "channels.geojson"):
        shutil.copy(DATA_FOLDER / "sites" / "mayon" / name, data / "sites" / "mayon" / name)
    add_empty_relief_tiles(data)
    return out, data


def run(out, data, pair=PAIR):
    return publish_pair("mayon", pair, out_folder=out, data_folder=data, sites_folder=SITES_FOLDER)


def test_us026_publishing_adds_the_pairs_channel_rows(folders):
    out, data = folders
    run(out, data)
    rows = read_data(data / "sites" / "mayon" / "channel_areas.json")
    assert sorted(row["channel_id"] for row in rows) == ["mayon_basud", "mayon_lidong", "mayon_miisi", "mayon_padang"]
    assert {row["pair_id"] for row in rows} == {PAIR}
    assert check_data_dir(data) == []


def test_a_failed_publish_puts_the_channel_rows_back(folders):
    out, data = folders
    run(out, data)
    areas = data / "sites" / "mayon" / "channel_areas.json"
    before = areas.read_bytes()
    sources = json.loads((data / "sources.json").read_text(encoding="utf-8"))
    sources["data"][0]["license"] = None
    (data / "sources.json").write_text(json.dumps(sources), encoding="utf-8")
    with pytest.raises(PublishError):
        run(out, data)
    assert areas.read_bytes() == before


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


def test_a_validation_in_the_output_is_never_published_with_the_pair(folders):
    out, data = folders
    (out / "sites" / "mayon" / "pairs" / PAIR / "validation.json").write_text("{}", encoding="utf-8")
    (out / "sites" / "mayon" / "pairs" / PAIR / "validation.json").unlink()
    (out / "sites" / "mayon" / "pairs" / PAIR / "validation.json").write_text("draft", encoding="utf-8")
    try:
        run(out, data)
    except PublishError:
        pass
    assert not (data / "sites" / "mayon" / "pairs" / PAIR / "validation.json").exists()


def test_publishing_again_keeps_a_reviewed_validation(folders):
    out, data = folders
    run(out, data)
    target = data / "sites" / "mayon" / "pairs" / PAIR / "validation.json"
    record = {"data": {"id": f"val_{PAIR}", "pair_id": PAIR, "source_name": "s", "source_url": "https://x.org",
                       "source_date": "2026-07-13", "method": "Checked.", "items": [],
                       "created_at": "2026-11-01T00:00:00Z", "updated_at": "2026-11-01T00:00:00Z"},
              "meta": {"generated_at": "2026-11-01T00:00:00Z", "schema_version": "1.0"}}
    target.write_text(json.dumps(record), encoding="utf-8")
    run(out, data)
    assert target.is_file()


def test_a_later_pair_can_finish_the_check(folders):
    out, data = folders
    (data / "sources.json").unlink()
    publish_pair("mayon", PAIR, out_folder=out, data_folder=data, sites_folder=SITES_FOLDER, more_to_come=True)
    assert (data / "sites" / "mayon" / "pairs" / PAIR / "pair.json").is_file()


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

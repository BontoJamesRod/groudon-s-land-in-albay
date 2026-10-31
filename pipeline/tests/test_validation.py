"""Tests for the validation module (T-035, TC-040, TC-041)."""
import json

import pytest

from mrw.contract_check import check_validation
from mrw.validation import ValidationError, build_record, publish_record, write_record

PAIR = "mayon_A111F008_20260703_20260715"


def sheet(draft=True, detected="no"):
    return {"draft": draft, "source_name": "PHIVOLCS via GMA News", "source_url": "https://example.org/a",
            "source_date": "2026-07-13", "method": "DRAFT, owner must review. Compared by flank.",
            "other_sources": ["https://example.org/b"],
            "items": [{"place_name": "Basud Gully", "channel_id": None, "reported_in_source": True,
                       "detected": detected, "note": "Test note"}]}


@pytest.fixture
def folders(tmp_path):
    sheets = tmp_path / "sheets"
    sheets.mkdir()
    return tmp_path / "out", tmp_path / "data", sheets


def save(sheets, content):
    (sheets / f"{PAIR}.json").write_text(json.dumps(content), encoding="utf-8")


def test_record_follows_docs_05():
    record = build_record(PAIR, sheet(), "2026-11-01T00:00:00Z")
    assert record["id"] == f"val_{PAIR}"
    assert record["items"][0]["id"] == "item_01"
    assert record["items"][0]["validation_id"] == record["id"]
    assert "draft" not in record and "other_sources" not in record


def test_written_record_passes_the_contract_check(folders):
    out, _data, sheets = folders
    save(sheets, sheet())
    path = write_record("mayon", PAIR, out, sheets)
    errors = []
    check_validation(path, PAIR, errors)
    assert errors == []


@pytest.mark.parametrize("draft", [True, None])
def test_a_draft_can_never_be_published(folders, draft):
    out, data, sheets = folders
    content = sheet()
    if draft is None:
        del content["draft"]
    save(sheets, content)
    with pytest.raises(ValidationError):
        publish_record("mayon", PAIR, out, data, sheets)
    assert not list(data.rglob("validation.json")) if data.exists() else True


def test_draft_text_left_in_a_reviewed_sheet_stops(folders):
    out, data, sheets = folders
    save(sheets, sheet(draft=False))
    with pytest.raises(ValidationError):
        publish_record("mayon", PAIR, out, data, sheets)


def test_the_draft_is_written_away_from_the_pair_folders(folders):
    out, _data, sheets = folders
    save(sheets, sheet())
    assert "pairs" not in write_record("mayon", PAIR, out, sheets).parts


def test_a_reviewed_sheet_is_published(folders):
    out, data, sheets = folders
    reviewed = sheet(draft=False)
    reviewed["method"] = "Compared by flank."
    save(sheets, reviewed)
    (data / "sites" / "mayon" / "pairs" / PAIR).mkdir(parents=True)
    publish_record("mayon", PAIR, out, data, sheets)
    assert (data / "sites" / "mayon" / "pairs" / PAIR / "validation.json").is_file()


def test_invalid_detection_value_stops(folders):
    out, _data, sheets = folders
    save(sheets, sheet(detected="maybe"))
    with pytest.raises(ValidationError):
        write_record("mayon", PAIR, out, sheets)


def test_missing_sheet_stops(folders):
    out, _data, sheets = folders
    with pytest.raises(ValidationError):
        write_record("mayon", PAIR, out, sheets)

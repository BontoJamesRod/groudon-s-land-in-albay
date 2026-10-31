"""Task T-035: turn a hand-filled validation sheet into a validation record (docs/05 TBL-08, TBL-09).

Run from the project folder:
    python pipeline/mrw/validation.py mayon <pair id>

    python pipeline/mrw/validation.py mayon <pair id> --publish

A sheet lives in pipeline/context/validation_sheets/<pair id>.json. The record is written
to pipeline/out/validation_drafts/, away from the pair folders that the publish step copies.
A draft can never reach the public site. To publish, the owner reviews the sheet, removes
"DRAFT" from its text, and sets "draft" to false.
"""
import json
import shutil
import sys
from pathlib import Path

# Lets this file run as a script from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mrw.config import utc_now_text
from mrw.context import DATA_FOLDER, write_json
from mrw.contract_check import DETECTION_RESULT, check_validation

REPO_ROOT = Path(__file__).resolve().parents[2]
SHEET_FOLDER = REPO_ROOT / "pipeline" / "context" / "validation_sheets"
OUT_FOLDER = REPO_ROOT / "pipeline" / "out"
RECORD_COLUMNS = ("source_name", "source_url", "source_date", "method")
ITEM_COLUMNS = ("place_name", "channel_id", "reported_in_source", "detected", "note")


class ValidationError(Exception):
    """The sheet can't be used, or a draft was about to be published."""


def load_sheet(pair_id, sheet_folder=SHEET_FOLDER):
    """Read a pair's sheet and check each place has a real detection result."""
    path = Path(sheet_folder) / f"{pair_id}.json"
    if not path.is_file():
        raise ValidationError(f"No validation sheet at {path}")
    sheet = json.loads(path.read_text(encoding="utf-8"))
    for item in sheet["items"]:
        if item["detected"] not in DETECTION_RESULT:
            raise ValidationError(f"Invalid detected value: {item['detected']}")
    return sheet


def build_record(pair_id, sheet, now):
    """Build the validation record. Only columns in docs/05 are copied from the sheet."""
    record_id = f"val_{pair_id}"
    items = [{"id": f"item_{number:02d}", "validation_id": record_id,
              **{name: item.get(name) for name in ITEM_COLUMNS}, "created_at": now, "updated_at": now}
             for number, item in enumerate(sheet["items"], start=1)]
    return {"id": record_id, "pair_id": pair_id, **{name: sheet[name] for name in RECORD_COLUMNS},
            "created_at": now, "updated_at": now, "items": items}


def write_record(site_id, pair_id, out_folder=OUT_FOLDER, sheet_folder=SHEET_FOLDER):
    """Write the record to pipeline/out/ and check it. Drafts are allowed here."""
    record = build_record(pair_id, load_sheet(pair_id, sheet_folder), utc_now_text())
    path = Path(out_folder) / "validation_drafts" / f"{pair_id}.json"
    write_json(path, record, record["created_at"])
    errors = []
    check_validation(path, pair_id, errors)
    if errors:
        path.unlink()
        raise ValidationError(errors[0])
    return path


def publish_record(site_id, pair_id, out_folder=OUT_FOLDER, data_folder=DATA_FOLDER, sheet_folder=SHEET_FOLDER):
    """Copy a reviewed record to site/data/. A draft stops here."""
    sheet = load_sheet(pair_id, sheet_folder)
    if sheet.get("draft") is not False or "DRAFT" in json.dumps(build_record(pair_id, sheet, "")):
        raise ValidationError("This validation sheet is a draft: the owner must review it before it is published")
    source = write_record(site_id, pair_id, out_folder, sheet_folder)
    target = Path(data_folder) / "sites" / site_id / "pairs" / pair_id
    if not target.is_dir():
        raise ValidationError(f"The pair isn't published yet: {pair_id}")
    shutil.copy(source, target / "validation.json")


if __name__ == "__main__":
    if "--publish" in sys.argv:
        publish_record(sys.argv[1], sys.argv[2])
        print(f"Published the validation of {sys.argv[2]}")
    else:
        print(f"Wrote {write_record(sys.argv[1], sys.argv[2])}")

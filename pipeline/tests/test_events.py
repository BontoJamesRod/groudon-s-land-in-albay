"""Tests for the events list (docs/EVENTS_PLAN.md)."""
import json
from datetime import date
from pathlib import Path

EVENTS_FILE = Path(__file__).parents[1] / "context" / "events_2026.json"
REQUIRED_FIELDS = {"date_start", "date_end", "type", "title", "channels", "towns",
                   "source_name", "source_url", "confidence"}
ALLOWED_TYPES = {"eruption", "activity", "lahar", "storm", "heavy_rain", "quarry_action"}


def load_events():
    return json.loads(EVENTS_FILE.read_text(encoding="utf-8"))


def test_the_file_holds_a_list_of_events():
    events = load_events()
    assert isinstance(events, list)
    assert events


def test_every_event_has_the_required_fields():
    for event in load_events():
        assert REQUIRED_FIELDS <= set(event), event["title"]


def test_dates_are_iso_and_the_end_is_not_before_the_start():
    for event in load_events():
        # fromisoformat raises an error if the date isn't written as YYYY-MM-DD.
        start = date.fromisoformat(event["date_start"])
        end = date.fromisoformat(event["date_end"])
        assert end >= start, event["title"]


def test_types_are_allowed():
    for event in load_events():
        assert event["type"] in ALLOWED_TYPES, event["title"]


def test_every_event_has_a_source_and_a_confidence():
    for event in load_events():
        assert event["source_url"].startswith("https://"), event["title"]
        assert event["confidence"] in {"confirmed", "unconfirmed"}, event["title"]

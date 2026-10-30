"""FR-038, TC-030: no interface text may state that a lahar, eruption or flood will happen.

Reads all the text a visitor can see: site/js/strings.js, the HTML pages, and the
published events and legends. It splits the text into sentences, and a sentence
fails if it has both a hazard word and a word about the future.
"""
import json
import re
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[2] / "site"
HAZARD = re.compile(r"\b(lahars?|eruptions?|erupts?|erupting|floods?|flooding)\b", re.IGNORECASE)
FUTURE = re.compile(r"\b(will|shall|expect\w*|forecast\w*|predict\w*|going to|about to|imminent|likely|soon|upcoming)\b",
                    re.IGNORECASE)


def predicts_a_hazard(text):
    """Return the sentences that mention a hazard together with the future."""
    sentences = re.split(r"(?<=[.!?])\s+|\n", text)
    return [s for s in sentences if HAZARD.search(s) and FUTURE.search(s)]


def visible_text_files():
    files = [SITE / "js" / "strings.js", SITE / "index.html", SITE / "404.html"]
    data = SITE / "data"
    files += sorted(data.glob("sites/*/events.json")) + sorted(data.glob("sites/*/pairs/*/pair.json"))
    return files


@pytest.mark.parametrize("path", visible_text_files(), ids=lambda p: p.name)
def test_no_visible_text_predicts_a_hazard(path):
    assert predicts_a_hazard(path.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("text", [
    "A lahar will happen tonight.",
    "An eruption is expected next week",
    "Flooding is likely in Daraga.",
    "We forecast a flood.",
])
def test_the_check_catches_predictions(text):
    assert predicts_a_hazard(text)


@pytest.mark.parametrize("text", [
    "Moderately explosive eruption",
    "This is not an official warning. Follow PHIVOLCS and your LGU.",
    "A flood changed the channel. The next pass will come soon.",
])
def test_the_check_allows_plain_statements(text):
    assert predicts_a_hazard(text) == []


def test_every_page_string_key_exists():
    """Each data-text and data-label in the page must have a matching string."""
    strings = (SITE / "js" / "strings.js").read_text(encoding="utf-8")
    page = (SITE / "index.html").read_text(encoding="utf-8")
    keys = set(re.findall(r'data-(?:text|label)="(\w+)"', page))
    assert keys
    missing = [key for key in keys if not re.search(rf"^\s*{key}:", strings, re.MULTILINE)]
    assert missing == []


def test_exact_messages_from_the_prd_are_present():
    strings = (SITE / "js" / "strings.js").read_text(encoding="utf-8")
    for message in ("Background map unavailable", "No town found. Try another name or tap the map.",
                    "No radar data here", "Inside the Permanent Danger Zone. Entry is not allowed.",
                    "This is the latest pass", "No radar passes processed yet for this site",
                    "Before/after images not available for this pair",
                    "This is not an official warning. Follow PHIVOLCS and your LGU.",
                    "Not yet checked against an independent source"):
        assert message in strings

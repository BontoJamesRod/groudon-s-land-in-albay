"""FR-038, TC-030: no interface text may state that a lahar, eruption or flood will happen.

Reads the text a visitor can see: every string in site/js, the HTML pages, and every
published JSON value. It splits the text into sentences, and a sentence fails if it has
both a hazard word and a word about the future. A word list can't catch everything,
so a person still reads the wording before release (TC-030).
"""
import json
import re
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[2] / "site"
SHEETS = SITE.parent / "pipeline" / "context" / "validation_sheets"
HAZARD = re.compile(r"\b(lahars?|mudflows?|eruptions?|erupts?|erupting|floods?|flooding|inundat\w*)\b", re.IGNORECASE)
FUTURE = re.compile(r"\b(will|shall|expect\w*|forecast\w*|predict\w*|going to|about to|imminent|likely|soon|upcoming|"
                    r"coming|may|might|could|tonight|tomorrow|faces?|next (week|month|rain|days?)|within (days|hours|weeks))\b",
                    re.IGNORECASE)


def predicts_a_hazard(text):
    """Return the sentences that mention a hazard together with the future."""
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    return [s for s in sentences if HAZARD.search(s) and FUTURE.search(s)]


def json_strings(value):
    """Yield every text value inside a JSON document."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from json_strings(item)


def visible_strings(path):
    """Return the separate pieces of text in a file, so unrelated text isn't read as one sentence."""
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".json", ".geojson"):
        return list(json_strings(json.loads(text)))
    if path.suffix == ".js":
        pairs = re.findall(r'"((?:[^"\\]|\\.)*)"|`([^`]*)`', text)
        return [first or second for first, second in pairs]
    return re.split(r"<[^>]+>", text)


def visible_text_files():
    data = SITE / "data"
    return (sorted((SITE / "js").glob("*.js")) + [SITE / "index.html", SITE / "404.html"]
            + sorted(data.glob("*.json")) + sorted(data.glob("sites/*/*.json"))
            + sorted(data.glob("sites/*/channels.geojson"))
            + sorted(data.glob("sites/*/pairs/*/*.json")) + sorted(SHEETS.glob("*.json")))


@pytest.mark.parametrize("path", visible_text_files(), ids=lambda p: p.name)
def test_no_visible_text_predicts_a_hazard(path):
    found = [sentence for text in visible_strings(path) for sentence in predicts_a_hazard(text)]
    assert found == []


@pytest.mark.parametrize("text", [
    "A lahar will happen tonight.",
    "An eruption is expected next week",
    "Flooding is likely in Daraga.",
    "We forecast a flood.",
    "A lahar is coming tonight.",
    "An eruption could happen within days.",
    "Lahars may reach Daraga after the next rain.",
    "Daraga faces flooding next week.",
    "An eruption\nwill happen",
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

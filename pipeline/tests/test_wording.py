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


# FR-068, TC-075: no change is ever labelled in legal terms, anywhere in the site.
LEGAL_WORDS = ("illegal", "unpermitted", "violation")
# Pictures, radar grids and fonts hold no words a visitor can read.
NOT_TEXT = {".png", ".webp", ".jpg", ".jpeg", ".gif", ".ico", ".bin", ".woff", ".woff2"}
# The check panel may say what its source maps, so only these fields can use the word "landslide".
PANAMA_CHECK_FIELDS = ("source_name", "method", "place_name")
# "Tested in Panama", on Mayon's check panel, names the map our result matches (FR-100). Only this exact
# sentence may say "landslide" in the shared code, so the change itself is never called landslides.
TESTED_MATCH = "Our result matches the University of Panama's landslide map at a scale of a few km."


def text_files(folder):
    """List every file in a folder, however deep, except pictures, grids and fonts."""
    return [path for path in sorted(Path(folder).rglob("*")) if path.is_file() and path.suffix.lower() not in NOT_TEXT]


def legal_words_in(folder):
    """Return (file, word) for each legal word in a file's name or its text."""
    found = []
    for path in text_files(folder):
        text = (path.name + " " + path.read_text(encoding="utf-8", errors="replace")).lower()
        found += [(path.name, word) for word in LEGAL_WORDS if word in text]
    return found


def check_panel_strings_outside_its_fields(value):
    """Yield the text in a validation file that isn't in one of the allowed fields."""
    if isinstance(value, dict):
        for name, item in value.items():
            if name not in PANAMA_CHECK_FIELDS:
                yield from check_panel_strings_outside_its_fields(item)
    elif isinstance(value, list):
        for item in value:
            yield from check_panel_strings_outside_its_fields(item)
    elif isinstance(value, str):
        yield value


def panama_landslide_hits(site_folder):
    """Find "landslide" in Panama's pairs, legend, card and help text. Returns where it was found."""
    site_folder = Path(site_folder)
    hits = []
    shared = sorted((site_folder / "js").glob("*.js")) + sorted(site_folder.glob("*.html"))
    panama = [path for path in text_files(site_folder / "data" / "sites" / "panama") if path.name != "validation.json"]
    for path in shared + panama:
        if "landslide" in path.read_text(encoding="utf-8", errors="replace").replace(TESTED_MATCH, "").lower():
            hits.append(path.name)
    rows = json.loads((site_folder / "data" / "sites.json").read_text(encoding="utf-8"))["data"]
    if any("landslide" in text.lower() for row in rows if row["id"] == "panama" for text in json_strings(row)):
        hits.append("sites.json")
    for path in sorted((site_folder / "data" / "sites" / "panama").rglob("validation.json")):
        content = json.loads(path.read_text(encoding="utf-8"))
        if any("landslide" in text.lower() for text in check_panel_strings_outside_its_fields(content)):
            hits.append(path.name)
    return hits


def make_small_site(folder):
    """Build the few files the two checks read, all with clean wording."""
    pair = folder / "data" / "sites" / "panama" / "pairs" / "one"
    pair.mkdir(parents=True)
    (folder / "js").mkdir()
    (folder / "js" / "strings.js").write_text('const help = "How radar sees";', encoding="utf-8")
    (folder / "index.html").write_text("<p>Radar change</p>", encoding="utf-8")
    (folder / "data" / "sites.json").write_text('{"data": [{"id": "panama", "name": "Azuero"}]}', encoding="utf-8")
    (pair / "pair.json").write_text('{"data": {"title": "Radar change"}}', encoding="utf-8")
    (pair / "validation.json").write_text('{"data": {"source_name": "A landslide map", "items": [{"note": "Change"}]}}', encoding="utf-8")
    return folder


def test_tc075_no_legal_words_anywhere_in_the_site():
    assert legal_words_in(SITE) == []


def test_tc075_the_search_really_covers_the_site():
    names = {path.name for path in text_files(SITE)}
    assert {"strings.js", "index.html", "404.html", "app.css", "leaflet.js", "sites.json", "pairs.json", "validation.json"} <= names
    assert not any(path.suffix == ".webp" for path in text_files(SITE))


def test_tc075_no_landslide_label_on_panama():
    assert panama_landslide_hits(SITE) == []


@pytest.mark.parametrize("word", ["illegal", "Unpermitted", "VIOLATION"])
def test_tc075_a_legal_word_is_caught_deep_in_the_data(tmp_path, word):
    site = make_small_site(tmp_path)
    assert legal_words_in(site) == []
    (site / "data" / "sites" / "panama" / "pairs" / "one" / "pair.json").write_text(f'{{"note": "{word} change"}}', encoding="utf-8")
    assert legal_words_in(site) == [("pair.json", word.lower())]


@pytest.mark.parametrize("relative_path, content, expected", [
    ("data/sites/panama/pairs/one/pair.json", '{"data": {"title": "Landslides"}}', "pair.json"),
    ("js/strings.js", 'const legend = "Landslide";', "strings.js"),
    ("index.html", "<p>Landslide</p>", "index.html"),
    ("data/sites.json", '{"data": [{"id": "panama", "name": "Landslides"}]}', "sites.json"),
    ("data/sites/panama/pairs/one/validation.json", '{"data": {"source_name": "A map", "items": [{"note": "A landslide"}]}}', "validation.json"),
])
def test_tc075_landslide_is_caught_outside_the_check_panels_source(tmp_path, relative_path, content, expected):
    site = make_small_site(tmp_path)
    assert panama_landslide_hits(site) == []
    (site / relative_path).write_text(content, encoding="utf-8")
    assert panama_landslide_hits(site) == [expected]


def test_tc075_another_sites_data_may_use_the_word_landslide(tmp_path):
    site = make_small_site(tmp_path)
    other = site / "data" / "sites" / "mayon"
    other.mkdir()
    (other / "events.json").write_text('{"data": "A landslide in the news"}', encoding="utf-8")
    assert panama_landslide_hits(site) == []


def test_tc075_only_the_tested_in_panama_sentence_names_landslides_in_the_code():
    """The allowed sentence is used once, in strings.js, and nowhere else in the shared code."""
    shared = sorted((SITE / "js").glob("*.js")) + sorted(SITE.glob("*.html"))
    uses = {path.name: path.read_text(encoding="utf-8").count(TESTED_MATCH) for path in shared}
    assert {name: count for name, count in uses.items() if count} == {"strings.js": 1}
    assert "testedMatch: \"" + TESTED_MATCH in (SITE / "js" / "strings.js").read_text(encoding="utf-8")

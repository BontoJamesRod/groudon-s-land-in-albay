"""TC-032's other half: the license files exist, and CREDITS.md says the same as sources.json."""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CREDITS = (REPO / "CREDITS.md").read_text(encoding="utf-8")
README = (REPO / "README.md").read_text(encoding="utf-8")


def rows(path):
    content = json.loads(path.read_text(encoding="utf-8"))
    return content["data"] if isinstance(content, dict) else content


def published_sources():
    return rows(REPO / "site" / "data" / "sources.json")


def test_license_is_the_apache_text():
    text = (REPO / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in text and "Version 2.0, January 2004" in text
    assert "END OF TERMS AND CONDITIONS" in text
    assert len(text.split()) > 1500


def test_the_readme_links_both_files():
    assert "(LICENSE)" in README and "(CREDITS.md)" in README


def test_credits_say_data_is_not_under_the_code_license():
    assert "Apache-2.0 doesn't cover data files under ODbL, CC BY-SA 4.0" in CREDITS


def test_every_source_is_in_the_credits_with_its_license():
    for row in published_sources():
        line = next((text for text in CREDITS.splitlines() if f"`{row['id']}`" in text), None)
        assert line, row["id"]
        assert row["license"] in line, row["id"]


def test_the_credits_list_no_source_that_is_not_in_the_file():
    listed = set(re.findall(r"\| `([a-z0-9_]+)` \|$", CREDITS, re.MULTILINE))
    assert listed == {row["id"] for row in published_sources()}


def test_the_published_sources_match_the_pipelines():
    # The published rows also carry the time they were written.
    written = published_sources()
    for published, original in zip(written, rows(REPO / "pipeline" / "context" / "sources.json"), strict=True):
        assert {key: published[key] for key in original} == original


def test_the_sources_the_owner_named_are_all_there():
    ids = {row["id"]: row for row in published_sources()}
    assert ids["channel_lines"]["license"] == "ODbL 1.0"
    assert ids["pa_admin_boundaries"]["license"] == "CC BY-SA 4.0"
    assert ids["ph_admin_boundaries"]["license"] == "CC BY-IGO"
    assert {"nisar_asf", "gpm_imerg", "esa_worldcover_2021", "copernicus_dem_glo30"} <= set(ids)


def test_every_required_python_package_is_credited():
    names = [line.strip() for line in (REPO / "pipeline" / "requirements.txt").read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")]
    table = {line.split("|")[1].strip().lower().replace("_", "-") for line in CREDITS.splitlines() if line.startswith("| ")}
    for name in names:
        assert name.lower().replace("_", "-") in table, name


def test_the_vendored_libraries_keep_their_licenses():
    assert "BSD 2-Clause" in (REPO / "site" / "vendor" / "leaflet-1.9.4" / "LICENSE").read_text(encoding="utf-8")
    axe = REPO / "pipeline" / "tests" / "e2e" / "vendor" / "axe-core-4.14.0" / "LICENSE"
    assert "Mozilla Public License" in axe.read_text(encoding="utf-8")
    assert "| [axe-core](https://github.com/dequelabs/axe-core) | 4.14.0 | MPL-2.0 |" in CREDITS

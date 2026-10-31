"""Put a version on each JS and CSS link in site/index.html, so visitors don't get stale code.

Run from the project folder after changing anything in site/js or site/css:
    python pipeline/mrw/stamp_assets.py

The version is a short hash of the file, so it only changes when the file does, and a test
fails if someone forgets to run this. JavaScript modules import each other by plain names,
so the page's import map says which version each name means.
"""
import hashlib
import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"
INDEX = SITE / "index.html"
MAP_START = '<script type="importmap">'
MAP_PATTERN = re.compile(r'[ \t]*<script type="importmap">.*?</script>\r?\n', re.DOTALL)


def version_of(path):
    """Return a short hash of a file, ignoring line endings, which differ between computers."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:10]


def versioned(relative_path, site=SITE):
    return f"{relative_path}?v={version_of(site / relative_path)}"


def stamped_page(text, site=SITE):
    """Return the page's text with up-to-date links and import map."""
    text = re.sub(r'href="css/app\.css[^"]*"', f'href="{versioned("css/app.css", site)}"', text)
    text = re.sub(r'src="js/main\.js[^"]*"', f'src="{versioned("js/main.js", site)}"', text)
    names = sorted(path.name for path in (site / "js").glob("*.js"))
    imports = {f"./js/{name}": f"./{versioned(f'js/{name}', site)}" for name in names}
    block = f"  {MAP_START}\n{json.dumps({'imports': imports}, indent=2)}\n  </script>\n"
    text = MAP_PATTERN.sub("", text)
    return text.replace('  <script type="module"', block + '  <script type="module"')


if __name__ == "__main__":
    raw = INDEX.read_bytes().decode("utf-8")
    INDEX.write_bytes(stamped_page(raw.replace("\r\n", "\n")).encode("utf-8"))
    print("Stamped", INDEX)

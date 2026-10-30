"""Task T-019: copy a checked pair from pipeline/out/ to the public site's data folder.

Run from the project folder:
    python pipeline/mrw/publish.py mayon mayon_A111F008_20261007_20261019

Only this step puts radar results into site/data/ (docs/04, ADR-009). It changes
files on your computer: they reach the public site when you push them to main.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

# Lets this file run as a script from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mrw.config import SITES_FOLDER, build_sites_row, load_site_config, utc_now_text
from mrw.context import DATA_FOLDER, write_json
from mrw.contract_check import check_data_dir
from mrw.export import OUT_FOLDER


class PublishError(Exception):
    """The pair can't be published. Nothing in site/data/ was changed."""


def _read_data(path):
    """Return the 'data' member of a JSON data file."""
    return json.loads(path.read_text(encoding="utf-8"))["data"]


def _pair_row(pair):
    """A row of pairs.json holds the pair's columns, without its passes and layers."""
    return {name: value for name, value in pair.items() if name not in ("passes", "layers")}


def rebuild_pairs_list(site_folder, now):
    """Rewrite pairs.json from the pair folders, oldest first (docs/06, API-007)."""
    pairs = [_read_data(path) for path in sorted((site_folder / "pairs").glob("*/pair.json"))]
    rows = sorted((_pair_row(pair) for pair in pairs), key=lambda row: row["after_acquired_start"])
    write_json(site_folder / "pairs.json", rows, now)


def rebuild_sites_list(data_folder, now, sites_folder=SITES_FOLDER):
    """Rewrite sites.json from the site configs, keeping each site's created_at."""
    path = data_folder / "sites.json"
    old_rows = {row["id"]: row for row in _read_data(path)} if path.is_file() else {}
    rows = []
    for config_path in sorted(Path(sites_folder).glob("*.json")):
        config = load_site_config(config_path)
        if config["status"] != "published" or not (data_folder / "sites" / config["id"]).is_dir():
            continue
        row = build_sites_row(config, now)
        if config["id"] in old_rows:
            row["created_at"] = old_rows[config["id"]]["created_at"]
        rows.append(row)
    write_json(path, rows, now)


def _check_ready(out_pair_folder):
    """Stop unless the pair exists, has status 'ready', and its output is valid."""
    path = out_pair_folder / "pair.json"
    if not path.is_file():
        raise PublishError(f"No processed pair at {out_pair_folder}")
    status = _read_data(path)["status"]
    if status != "ready":
        raise PublishError(f"Only a 'ready' pair can be published. This one is '{status}'.")


def _restore(target, backup, lists):
    """Put back site/data/ as it was before a failed publish."""
    shutil.rmtree(target, ignore_errors=True)
    if backup.is_dir():
        shutil.move(str(backup), str(target))
    for path, content in lists.items():
        if content is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(content)


def publish_pair(site_id, pair_key, out_folder=OUT_FOLDER, data_folder=DATA_FOLDER, sites_folder=SITES_FOLDER):
    """Publish one pair, and undo everything if the result fails the contract check."""
    out_folder, data_folder = Path(out_folder), Path(data_folder)
    source = out_folder / "sites" / site_id / "pairs" / pair_key
    _check_ready(source)
    errors = check_data_dir(out_folder, published=False)
    if errors:
        raise PublishError(f"Output fails the contract check: {errors[0]}")
    site_folder = data_folder / "sites" / site_id
    target = site_folder / "pairs" / pair_key
    # The backup sits outside the data folder, so it can't be mistaken for a pair.
    backup = Path(tempfile.mkdtemp()) / pair_key
    pairs_path, sites_path = site_folder / "pairs.json", data_folder / "sites.json"
    lists = {p: p.read_bytes() if p.is_file() else None for p in (pairs_path, sites_path)}
    if target.is_dir():
        shutil.move(str(target), str(backup))
    now = utc_now_text()
    try:
        shutil.copytree(source, target)
        content = json.loads((target / "pair.json").read_text(encoding="utf-8"))
        pair = content["data"]
        pair.update(status="published", published_at=now, updated_at=now)
        write_json(target / "pair.json", pair, now)
        rebuild_pairs_list(site_folder, now)
        rebuild_sites_list(data_folder, now, sites_folder)
        errors = check_data_dir(data_folder)
    except Exception:
        _restore(target, backup, lists)
        raise
    if errors:
        _restore(target, backup, lists)
        raise PublishError(f"Result fails the contract check: {errors[0]}")
    shutil.rmtree(backup.parent, ignore_errors=True)
    return pair


if __name__ == "__main__":
    published = publish_pair(sys.argv[1], sys.argv[2])
    print(f"Published {published['id']} at {published['published_at']}")

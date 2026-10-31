"""Task T-008: read and check one site's config file, and build its `sites` row.

Each site has one file, pipeline/sites/<id>.json, so a new site needs no code
changes (FR-043). The file uses the column names of the `sites` table in
docs/05-database-design.md, plus four pipeline-only settings that are never
published:

- thresholds: the values that decide what counts as new material. They are
  PROVISIONAL until the owner sets the final values (docs/05, Open Question 2).
- provisional_fields: which settings are still PROVISIONAL.
- tracks: the radar tracks that cover the site.
- filters: optional false-alarm filters (mrw/filters.py). All off unless the owner turns them on.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from mrw.contract_check import SITES, check_row
from mrw.filters import FilterConfigError, check_filters

SITES_FOLDER = Path(__file__).resolve().parents[1] / "sites"
PIPELINE_ONLY = ("thresholds", "provisional_fields", "tracks", "filters")
TIMESTAMPS = ("created_at", "updated_at")


class SiteConfigError(Exception):
    """The site config can't be used. The message says why."""


def utc_now_text():
    """Return the current UTC time in the format the data files use."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_bounds(config, path):
    """Stop with the exact FR-044 message if west >= east or south >= north."""
    try:
        reversed_bounds = (config["bounds_west"] >= config["bounds_east"]
                           or config["bounds_south"] >= config["bounds_north"])
    except (KeyError, TypeError) as problem:
        raise SiteConfigError(f"Missing or bad bounds in site config: {path}") from problem
    if reversed_bounds:
        raise SiteConfigError(f"Invalid bounds in site config: {path}")


def _check_columns(config, path):
    """Check the `sites` columns with the same rules as the contract check."""
    table = {name: rule for name, rule in SITES.items() if name not in TIMESTAMPS}
    row = {name: value for name, value in config.items() if name not in PIPELINE_ONLY}
    errors = []
    check_row(row, table, str(path), errors)
    low, default, high = (config.get(k) for k in ("min_zoom", "default_zoom", "max_zoom"))
    if not errors and not low <= default <= high:
        errors.append(f"{path}: zooms must be min_zoom <= default_zoom <= max_zoom")
    if errors:
        raise SiteConfigError("; ".join(errors))


def _check_thresholds(config, path):
    """Thresholds must exist and be in range. Their values are the owner's decision."""
    values = config.get("thresholds")
    if not isinstance(values, dict):
        raise SiteConfigError(f"Missing thresholds in site config: {path}")
    if values.get("status") not in ("PROVISIONAL", "FINAL"):
        raise SiteConfigError(f"thresholds.status must be PROVISIONAL or FINAL in site config: {path}")
    brightness = values.get("brightness_threshold_db")
    loss = values.get("coherence_loss_threshold")
    if not isinstance(brightness, (int, float)) or brightness <= 0:
        raise SiteConfigError(f"brightness_threshold_db must be above 0 in site config: {path}")
    if not isinstance(loss, (int, float)) or not 0 <= loss <= 1:
        raise SiteConfigError(f"coherence_loss_threshold must be 0 to 1 in site config: {path}")
    if values.get("rule", "either_signal") not in ("either_signal", "brightness_leads"):
        raise SiteConfigError(f"thresholds.rule must be either_signal or brightness_leads in site config: {path}")


def load_site_config(path):
    """Read a site config file, check it, and return it as a dictionary."""
    path = Path(path)
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as problem:
        raise SiteConfigError(f"Can't read site config: {path} ({problem})") from problem
    _check_bounds(config, path)
    _check_columns(config, path)
    _check_thresholds(config, path)
    try:
        check_filters(config.get("filters"))
    except FilterConfigError as problem:
        raise SiteConfigError(f"{problem} in site config: {path}") from problem
    return config


def load_site(site_id):
    """Read the config of a site by its id, for example 'mayon'."""
    return load_site_config(SITES_FOLDER / f"{site_id}.json")


def build_sites_row(config, now=None):
    """Build the row for site/data/sites.json: only the columns in docs/05."""
    now = now or utc_now_text()
    row = {name: config.get(name) for name in SITES if name not in TIMESTAMPS}
    row["created_at"] = now
    row["updated_at"] = now
    return row


def thresholds_are_provisional(config):
    """Return True while the owner has not set the final thresholds."""
    return config["thresholds"].get("status") == "PROVISIONAL"

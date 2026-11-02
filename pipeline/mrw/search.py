"""Task T-012: find NISAR GCOV and GUNW products for a site on ASF.

What the two product types are:
- GCOV is one radar pass turned into a map of brightness (backscatter).
- GUNW compares two passes. We use its coherence: how alike the two passes are.

Staying blind to the eruption: until the owner sets the final thresholds, no
product acquired on or after BLIND_CUTOFF may be searched for or opened. A GUNW
holds two dates, and its first date alone can look safe while its second is not,
so the check below looks at EVERY date in a product's name.
"""
import re
from datetime import datetime, timedelta, timezone

BLIND_CUTOFF = datetime(2026, 11, 1, tzinfo=timezone.utc)

# Examples of the names, from docs/06:
# NISAR_L2_PR_GCOV_032_111_A_008_4005_DHDH_A_<start>_<end>_P05023_N_F_J_001
# NISAR_L2_PR_GUNW_032_111_A_008_033_4000_SH_<start1>_<end1>_<start2>_<end2>_P05023_N_F_J_001
GCOV_NAME = re.compile(
    r"^NISAR_L2_[A-Z]{2}_GCOV_(?P<cycle>\d{3})_(?P<track>\d{3})_(?P<direction>[AD])_(?P<frame>\d{3})_"
    r"\w+?_(?P<start>\d{8}T\d{6})_(?P<end>\d{8}T\d{6})_\w+$")
GUNW_NAME = re.compile(
    r"^NISAR_L2_[A-Z]{2}_GUNW_\d{3}_(?P<track>\d{3})_(?P<direction>[AD])_(?P<frame>\d{3})_\d{3}_"
    r"\w+?_(?P<start1>\d{8}T\d{6})_\d{8}T\d{6}_(?P<start2>\d{8}T\d{6})_\d{8}T\d{6}_\w+$")
ANY_TIME = re.compile(r"\d{8}T\d{6}")
VERTEX_URL = "https://search.asf.alaska.edu/#/?dataset=NISAR&searchType=List%20Search&searchList="
DIRECTIONS = {"A": "ascending", "D": "descending"}


class BlindnessError(Exception):
    """Something tried to use a product acquired on or after the blind cutoff."""


def _parse_time(text):
    """Turn 20261007T211319 into a UTC datetime."""
    return datetime.strptime(text, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)


def iso_time(text):
    """Turn 20261007T211319 into 2026-10-07T21:13:19Z, the format of the data files."""
    return _parse_time(text).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_before_cutoff(granule_id, cutoff=BLIND_CUTOFF):
    """Return True only if the name has dates and all of them are before the cutoff.

    A name with no dates can't be checked, so it counts as not safe.
    """
    times = ANY_TIME.findall(granule_id)
    return bool(times) and all(_parse_time(t) < cutoff for t in times)


def require_before_cutoff(granule_id, cutoff=BLIND_CUTOFF):
    """Stop if this product may contain eruption data. Called before any download."""
    if not is_before_cutoff(granule_id, cutoff):
        raise BlindnessError("Refusing a product at or after the blind cutoff, or with no "
                             f"readable dates. Cutoff: {cutoff:%Y-%m-%d}")


def vertex_url(granule_id):
    """Build the link to a product in ASF Vertex (format from docs/06, still to verify)."""
    return VERTEX_URL + granule_id


def site_polygon(config):
    """Write the site's bounds as the polygon text that ASF search expects."""
    w, s, e, n = (config[k] for k in ("bounds_west", "bounds_south", "bounds_east", "bounds_north"))
    return f"POLYGON(({w} {s}, {e} {s}, {e} {n}, {w} {n}, {w} {s}))"


def parse_gcov(granule_id, maturity="PROVISIONAL", url=None):
    """Read track, frame, direction, cycle and times from a GCOV name. None if no match."""
    match = GCOV_NAME.match(granule_id)
    if not match:
        return None
    return {
        "granule_id": granule_id,
        "track": int(match["track"]),
        "frame": int(match["frame"]),
        "orbit_direction": DIRECTIONS[match["direction"]],
        "cycle": int(match["cycle"]),
        "acquired_start": iso_time(match["start"]),
        "acquired_end": iso_time(match["end"]),
        "maturity": maturity,
        "url": url,
    }


def parse_gunw(granule_id, url=None):
    """Read track, frame, direction and both dates from a GUNW name. None if no match."""
    match = GUNW_NAME.match(granule_id)
    if not match:
        return None
    return {
        "granule_id": granule_id,
        "track": int(match["track"]),
        "frame": int(match["frame"]),
        "orbit_direction": DIRECTIONS[match["direction"]],
        "before_acquired_start": iso_time(match["start1"]),
        "after_acquired_start": iso_time(match["start2"]),
        "url": url,
    }


def _asf_search(**options):
    """Call ASF. Imported here so that tests and CI never need the network."""
    import asf_search
    return asf_search.search(dataset=asf_search.DATASET.NISAR, **options)


def _safe_results(results, cutoff):
    """Drop every result that has a date at or after the cutoff, before anything reads it."""
    safe = []
    for result in results:
        props = result.properties
        name = props.get("sceneName") or props.get("fileID") or ""
        name = re.sub(r"\.h5$", "", name)
        if is_before_cutoff(name, cutoff):
            safe.append((name, props))
    return safe


def _keep_newest_versions(products, key_names):
    """If ASF lists a product twice (reprocessed), keep the last version by name."""
    best = {}
    for product in sorted(products, key=lambda p: p["granule_id"]):
        best[tuple(product[k] for k in key_names)] = product
    return list(best.values())


def maturity_of(props):
    """Read the maturity from the product's collection or link, e.g. ..._PROVISIONAL_V1.

    Returns None for anything else, such as Urgent Response products (_UR_ in the name).
    docs/05 only allows BETA, PROVISIONAL and VALIDATED, so those products are left out of the list.
    """
    text = f"{props.get('collectionName')} {props.get('url')}"
    for maturity in ("BETA", "PROVISIONAL", "VALIDATED"):
        if maturity in text:
            return maturity
    return None


def maturity_label(name, props):
    """Name a product's maturity for a list, including kinds the pipeline doesn't use."""
    text = f"{name} {props.get('collectionName')} {props.get('url')}"
    if "_UR_" in text:
        return "URGENT RESPONSE"
    return maturity_of(props) or f"OTHER ({props.get('collectionName')})"


def list_all_maturities(config, start, tracks, searcher=_asf_search, cutoff=BLIND_CUTOFF):
    """List GCOV and GUNW products of every maturity on these tracks. Names only, nothing is opened.

    The cutoff still applies. These rows are for reading: the pipeline's own searches stay as
    they are, so an Urgent Response product can't reach processing from here.
    """
    rows = []
    for level, parse in (("GCOV", parse_gcov), ("GUNW", parse_gunw)):
        results = searcher(processingLevel=level, intersectsWith=site_polygon(config), start=start,
                           end=cutoff - timedelta(seconds=1))
        for name, props in _safe_results(results, cutoff):
            parsed = parse(name)
            if parsed and parsed["track"] in tracks:
                rows.append({"level": level, "track": parsed["track"], "frame": parsed["frame"], "granule_id": name,
                             "maturity": maturity_label(name, props),
                             "acquired": parsed.get("acquired_start") or parsed["after_acquired_start"]})
    return rows


def search_gcov(config, start, searcher=_asf_search, cutoff=BLIND_CUTOFF):
    """List GCOV passes over a site, oldest first, all from before the cutoff."""
    results = searcher(processingLevel="GCOV", intersectsWith=site_polygon(config), start=start,
                       end=cutoff - timedelta(seconds=1))
    passes = []
    for name, props in _safe_results(results, cutoff):
        maturity = maturity_of(props)
        parsed = parse_gcov(name, maturity, props.get("url")) if maturity else None
        if parsed:
            passes.append(parsed)
    passes = _keep_newest_versions(passes, ("track", "frame", "orbit_direction", "acquired_start"))
    return sorted(passes, key=lambda p: p["acquired_start"])


def search_gunw(config, start, searcher=_asf_search, cutoff=BLIND_CUTOFF):
    """List GUNW products over a site, keeping only those with both dates before the cutoff."""
    results = searcher(processingLevel="GUNW", intersectsWith=site_polygon(config), start=start,
                       end=cutoff - timedelta(seconds=1))
    products = []
    for name, props in _safe_results(results, cutoff):
        parsed = parse_gunw(name, props.get("url")) if maturity_of(props) else None
        if parsed:
            products.append(parsed)
    return _keep_newest_versions(products, ("track", "frame", "orbit_direction",
                                            "before_acquired_start", "after_acquired_start"))

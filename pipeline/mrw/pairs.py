"""Task T-012: build pairs of radar passes that can fairly be compared.

Radar brightness depends on the viewing angle, so two passes can only be compared
if they come from the same track, frame and direction. A pair is two consecutive
passes like that. The stop messages are the exact ones from docs/01 (FR-027, FR-028).
"""

SAME_TRACK_FIELDS = ("track", "frame", "orbit_direction")
MIXED_PASSES_MESSAGE = "Passes are not from the same track, frame and direction"


class PairError(Exception):
    """The pair can't be processed. The pipeline stops and writes no files."""


def check_same_track(before, after):
    """Stop with the FR-027 message if two passes can't be compared."""
    if any(before[name] != after[name] for name in SAME_TRACK_FIELDS):
        raise PairError(MIXED_PASSES_MESSAGE)


def require_product(granule_id, available_ids):
    """Stop with the FR-028 message if a needed product isn't on ASF."""
    if granule_id not in available_ids:
        raise PairError(f"Product not available yet: {granule_id}")


def pass_id(one_pass):
    """Make a pass id such as A111F008_20261007T211319 (docs/05, TBL-04)."""
    letter = "A" if one_pass["orbit_direction"] == "ascending" else "D"
    stamp = one_pass["acquired_start"].replace("-", "").replace(":", "").rstrip("Z")
    return f"{letter}{one_pass['track']:03d}F{one_pass['frame']:03d}_{stamp}"


def pair_id(site_id, before, after):
    """Make a pair id such as mayon_A111F008_20261007_20261019 (docs/05, TBL-05)."""
    check_same_track(before, after)
    letter = "A" if before["orbit_direction"] == "ascending" else "D"
    first = before["acquired_start"][:10].replace("-", "")
    second = after["acquired_start"][:10].replace("-", "")
    return f"{site_id}_{letter}{before['track']:03d}F{before['frame']:03d}_{first}_{second}"


def find_gunw(before, after, gunw_products):
    """Return the GUNW made from exactly these two passes, or None if there isn't one."""
    for product in gunw_products:
        if (all(product[name] == before[name] for name in SAME_TRACK_FIELDS)
                and product["before_acquired_start"] == before["acquired_start"]
                and product["after_acquired_start"] == after["acquired_start"]):
            return product
    return None


def build_track_pairs(site_id, passes, gunw_products=()):
    """Build consecutive pairs for each track, frame and direction.

    Each pair records its previous pair on the same track, because coherence
    loss compares this pair's coherence with the previous pair's (FR-022).
    """
    groups = {}
    for one_pass in passes:
        groups.setdefault(tuple(one_pass[n] for n in SAME_TRACK_FIELDS), []).append(one_pass)
    pairs = []
    for group in groups.values():
        group = sorted(group, key=lambda p: p["acquired_start"])
        previous = None
        for before, after in zip(group, group[1:]):
            pair = {
                "id": pair_id(site_id, before, after),
                "before": before,
                "after": after,
                "gunw": find_gunw(before, after, gunw_products),
                "previous": previous,
            }
            pairs.append(pair)
            previous = pair
    return sorted(pairs, key=lambda p: p["after"]["acquired_start"])


def find_pair(pairs, track_id):
    """Return the pair with this id. Stop with FR-028 if it can't be built from ASF's list."""
    for pair in pairs:
        if pair["id"] == track_id:
            return pair
    raise PairError(f"Product not available yet: {track_id}")

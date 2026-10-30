"""Decision prep for T-036: which candidate events have NISAR passes before and after?

Run from the project folder:
    python pipeline/reports/second_site_search.py

Reads ASF's product list only, so it downloads no radar data. Searches and results
are limited to before the blind cutoff by search.py. It doesn't choose a site.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

REPORTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPORTS.parent))

from mrw.pairs import build_track_pairs
from mrw.search import search_gcov, search_gunw

# name: (west, south, east, north, date of the event, UTC)
CANDIDATES = {
    "Azuero Peninsula landslides, Panama": (-81.05, 7.30, -80.65, 7.70, "2026-10-09"),
    "Fuego, Guatemala": (-90.98, 14.38, -90.78, 14.56, "2026-08-03"),
    "Nyamulagira, DR Congo": (29.05, -1.55, 29.35, -1.30, "2026-08-09"),
    "Kilauea, Hawaii, USA": (-155.35, 19.35, -155.20, 19.47, "2026-08-12"),
}
START = "2026-06-01"


def candidate_config(box):
    west, south, east, north = box[:4]
    return {"bounds_west": west, "bounds_south": south, "bounds_east": east, "bounds_north": north}


def spanning_pairs(pairs, event_date):
    """Find the pairs whose two dates fall on either side of the event."""
    found = []
    for pair in pairs:
        before, after = pair["before"]["acquired_start"][:10], pair["after"]["acquired_start"][:10]
        if before < event_date <= after:
            found.append(pair)
    return found


def describe(pair):
    has_baseline = bool(pair["previous"] and pair["previous"]["gunw"])
    gap = (datetime.fromisoformat(pair["after"]["acquired_start"][:10])
           - datetime.fromisoformat(pair["before"]["acquired_start"][:10])).days
    return {"id": pair["id"].removeprefix("x_"), "track": pair["before"]["track"], "frame": pair["before"]["frame"],
            "direction": pair["before"]["orbit_direction"], "before": pair["before"]["acquired_start"],
            "after": pair["after"]["acquired_start"], "gap_days": gap, "gunw": bool(pair["gunw"]),
            "previous_gunw": has_baseline, "maturity": pair["before"]["maturity"],
            "before_granule": pair["before"]["granule_id"], "after_granule": pair["after"]["granule_id"]}


def main():
    results = {}
    for name, box in CANDIDATES.items():
        config = candidate_config(box)
        passes = search_gcov(config, START)
        pairs = build_track_pairs("x", passes, search_gunw(config, START))
        results[name] = {"event_date": box[4], "bounds": box[:4], "gcov_passes": len(passes),
                         "tracks": sorted({(p["track"], p["frame"], p["orbit_direction"]) for p in passes}),
                         "pairs_spanning_event": [describe(p) for p in spanning_pairs(pairs, box[4])]}
    (REPORTS / "second-site-search.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    for name, result in results.items():
        print(name, result["gcov_passes"], "passes", result["tracks"])
        for pair in result["pairs_spanning_event"]:
            print("  ", pair["id"], pair["before"][:10], pair["after"][:10], f"{pair['gap_days']}d",
                  "GUNW" if pair["gunw"] else "noGUNW", "baseline" if pair["previous_gunw"] else "nobaseline", pair["maturity"])


if __name__ == "__main__":
    main()

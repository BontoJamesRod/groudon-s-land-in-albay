"""Find and process the first passes after the eruption. See pipeline/RUNBOOK-eruption.md.

Run from the project folder:
    python pipeline/mrw/eruption_run.py check       list the new passes, reading names only
    python pipeline/mrw/eruption_run.py process     process them into pipeline/out/
    python pipeline/mrw/eruption_run.py republish   redo the published pairs with the final values

Staying blind: thresholds must be chosen before anyone sees eruption data. So every command
stops, before it contacts ASF, unless the owner has set the thresholds to FINAL and lifted
BLIND_CUTOFF in mrw/search.py. Nothing here reaches the public site without publish.py.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

# Lets this file run as a script from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mrw.config import load_site, thresholds_are_provisional
from mrw.context import DATA_FOLDER
from mrw.export import OUT_FOLDER, SEARCH_START, print_summary, run_pair
from mrw.pairs import build_track_pairs, same_gap
from mrw.publish import publish_pair
from mrw.search import BLIND_CUTOFF, search_gcov, search_gunw

SITE_ID = "mayon"
ERUPTION_START = "2026-10-30"
ERUPTION_TRACKS = (104, 111)


class NotReady(Exception):
    """The owner hasn't opened the way to eruption data yet. The message says what's missing."""


def require_owner_go_ahead(config, cutoff=BLIND_CUTOFF):
    """Stop unless the thresholds are final and the blind cutoff has been lifted."""
    if thresholds_are_provisional(config):
        raise NotReady("Stopped: the thresholds are still PROVISIONAL. The owner must set them to FINAL first.")
    if cutoff <= datetime(2026, 10, 30, tzinfo=timezone.utc):
        raise NotReady("Stopped: BLIND_CUTOFF hasn't been lifted. See step 3 of pipeline/RUNBOOK-eruption.md.")


def eruption_pairs(pairs):
    """Keep the pairs on the watched tracks whose after pass is on or after the eruption."""
    return [pair for pair in pairs if pair["after"]["track"] in ERUPTION_TRACKS
            and pair["after"]["acquired_start"][:10] >= ERUPTION_START]


def has_coherence(pair):
    """Coherence needs this pair's GUNW and a previous pair's GUNW over an equal time gap."""
    previous = pair["previous"]
    return bool(pair["gunw"] and previous and previous["gunw"]
                and same_gap(previous["before"], pair["before"], pair["after"]))


def find_pairs(config):
    """Search ASF and return the eruption pairs."""
    return eruption_pairs(build_track_pairs(SITE_ID, search_gcov(config, SEARCH_START), search_gunw(config, SEARCH_START)))


def check(pairs):
    """Print what is available. This reads product names only, not radar data."""
    for track in ERUPTION_TRACKS:
        if not any(pair["after"]["track"] == track for pair in pairs):
            print(f"Track {track}: no new pass on ASF yet. Try again later.")
    for pair in pairs:
        note = "coherence ready" if has_coherence(pair) else "NO COHERENCE YET: wait for the GUNW"
        print(f"{pair['id']}: {note}")


def process(pairs, config, runner=run_pair):
    """Process the pairs that have coherence. A brightness-only result can't be high confidence."""
    done = []
    for pair in pairs:
        if not has_coherence(pair):
            print(f"Skipped {pair['id']}: no coherence yet. Run this again when its GUNW is on ASF.")
            continue
        print_summary(runner(SITE_ID, pair["before"]["granule_id"], pair["after"]["granule_id"]), config)
        done.append(pair["id"])
    return done


def republish(config, pairs, data_folder=DATA_FOLDER, out_folder=OUT_FOLDER, runner=run_pair, publisher=publish_pair):
    """Redo every published pair, so the whole timeline uses the final thresholds."""
    published = {path.name for path in (Path(data_folder) / "sites" / SITE_ID / "pairs").iterdir() if path.is_dir()}
    chosen = [pair for pair in pairs if pair["id"] in published]
    missing = published - {pair["id"] for pair in chosen}
    if missing:
        raise NotReady(f"Stopped: these published pairs weren't found on ASF: {sorted(missing)}")
    for pair in chosen:
        print_summary(runner(SITE_ID, pair["before"]["granule_id"], pair["after"]["granule_id"]), config)
    for pair in chosen:
        publisher(SITE_ID, pair["id"], more_to_come=True)
    print("Republished", len(chosen), "pairs. Now run the contract check on site/data.")


def main(argv):
    """Command-line entry point. Returns 1 if it had to stop."""
    if len(argv) != 1 or argv[0] not in ("check", "process", "republish"):
        print(__doc__)
        return 1
    config = load_site(SITE_ID)
    try:
        require_owner_go_ahead(config)
        if argv[0] == "republish":
            republish(config, build_track_pairs(SITE_ID, search_gcov(config, SEARCH_START), search_gunw(config, SEARCH_START)))
        elif argv[0] == "process":
            process(find_pairs(config), config)
        else:
            check(find_pairs(config))
    except NotReady as problem:
        print(problem)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

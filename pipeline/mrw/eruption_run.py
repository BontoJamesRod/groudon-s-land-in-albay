"""Find and process the first passes after the eruption. See pipeline/RUNBOOK-eruption.md.

Run from the project folder:
    python pipeline/mrw/eruption_run.py check       list the new passes, reading names only
    python pipeline/mrw/eruption_run.py check-all   list every product maturity on Mayon's tracks, names only
    python pipeline/mrw/eruption_run.py process     process them into pipeline/out/
    python pipeline/mrw/eruption_run.py process --drill <older pair id>
                                                    practise on an older pair: cached data only, into pipeline/out/drill/
    python pipeline/mrw/eruption_run.py review [--drill] <pair id> [<pair id>]
                                                    print the numbers for the hold rule (docs/04, ADR-014)
    python pipeline/mrw/eruption_run.py preview [--drill] <pair id> [<pair id>]
                                                    serve a copy of the site with these pairs, on this computer only
    python pipeline/mrw/eruption_run.py baseline    save the published pairs' numbers for the hold rule
    python pipeline/mrw/eruption_run.py republish   redo the published pairs with the final values

Staying blind: thresholds must be chosen before anyone sees eruption data. So every command
stops, before it contacts ASF, unless the owner has set the thresholds to FINAL and lifted
BLIND_CUTOFF in mrw/search.py. Nothing here reaches the public site without publish.py.
"""
import functools
import http.server
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Lets this file run as a script from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mrw.config import load_site, thresholds_are_provisional
from mrw.context import DATA_FOLDER
from mrw.export import OUT_FOLDER, SEARCH_START, load_land, print_summary, run_pair
from mrw.hold_check import BASELINE_PATH, build_baseline, cached_crop, hold_reasons, measure_pair, print_review, read_pair, track_agreement
from mrw.pairs import build_track_pairs, same_gap
from mrw.publish import publish_pair
from mrw.search import BLIND_CUTOFF, list_all_maturities, search_gcov, search_gunw

SITE_ID = "mayon"
ERUPTION_START = "2026-10-30"
ERUPTION_TRACKS = (104, 111)
MAYON_TRACKS = (39, 104, 111)
DRILL_FOLDER = OUT_FOLDER / "drill"
PREVIEW_FOLDER = OUT_FOLDER / "preview"
SITE_FOLDER = Path(DATA_FOLDER).parent
PREVIEW_PORT = 8001


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


def newest_passes(passes):
    """Find the newest pass for each track and frame, sorted by track and then frame."""
    newest = {}
    for one_pass in passes:
        key = (one_pass["track"], one_pass["frame"])
        if key not in newest or one_pass["acquired_start"] > newest[key]["acquired_start"]:
            newest[key] = one_pass
    return [newest[key] for key in sorted(newest)]


def check(pairs, passes):
    """Print what is available. This reads product names only, not radar data."""
    print(f"Newest pass on ASF for each track and frame (only passes before {BLIND_CUTOFF:%Y-%m-%d} can be seen):")
    for one_pass in newest_passes(passes):
        print(f"  Track {one_pass['track']} frame {one_pass['frame']}: {one_pass['acquired_start']}")
    for track in ERUPTION_TRACKS:
        if not any(pair["after"]["track"] == track for pair in pairs):
            print(f"Track {track}: no new pass on ASF yet. Try again later.")
    for pair in pairs:
        note = "coherence ready" if has_coherence(pair) else "NO COHERENCE YET: wait for the GUNW"
        print(f"{pair['id']}: {note}")


def check_all(rows):
    """Print how many products of each kind there are, and the newest. Names only: nothing is opened."""
    print(f"Every product maturity on tracks {MAYON_TRACKS} (only products before {BLIND_CUTOFF:%Y-%m-%d} can be seen):")
    groups = {}
    for row in rows:
        groups.setdefault((row["track"], row["frame"], row["level"], row["maturity"]), []).append(row)
    for (track, frame, level, maturity), group in sorted(groups.items()):
        newest = max(group, key=lambda row: row["acquired"])
        print(f"  Track {track} frame {frame} {level} {maturity}: {len(group)}, newest {newest['acquired']}  {newest['granule_id']}")
    if not rows:
        print("  None found.")


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


def process_drill(pair_id, pairs, config, runner=run_pair):
    """Practise on an older pair. It reads cached crops only, and writes into its own folder."""
    chosen = [pair for pair in pairs if pair["id"] == pair_id]
    if not chosen:
        raise NotReady(f"Stopped: {pair_id} isn't a pair on ASF.")
    if chosen[0]["after"]["acquired_start"][:10] >= ERUPTION_START:
        raise NotReady(f"Stopped: {pair_id} is after the eruption, and a drill is only for older pairs.")
    return process(chosen, config, runner=lambda site, before, after: runner(site, before, after, out_folder=DRILL_FOLDER, reader=cached_crop))


def review(pair_ids, config, out_folder, maturities):
    """Print the hold rule's numbers for each pair and, with two tracks, how much they agree."""
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    land = load_land(SITE_ID)
    folders = {pair_id: Path(out_folder) / "sites" / SITE_ID / "pairs" / pair_id for pair_id in pair_ids}
    held = []
    for pair_id, folder in folders.items():
        if not (folder / "pair.json").is_file():
            raise NotReady(f"Stopped: {pair_id} hasn't been processed into {out_folder}.")
        measured = measure_pair(folder, config, land)
        reasons = hold_reasons(measured, maturities, baseline)
        print_review(measured, reasons, baseline)
        if reasons:
            held.append(pair_id)
    print_tracks(pair_ids, folders, baseline)
    return held


def print_tracks(pair_ids, folders, baseline):
    """Say how much two tracks agree or, with one pair, that it needs the single-track note."""
    if len(pair_ids) == 1:
        print("Only one pair: if the other track isn't ready, publish this one with --single-track.")
        return
    first, second = (read_pair(folders[pair_id])[2] for pair_id in pair_ids[:2])
    agreement = track_agreement(first, second)
    print("The two tracks agree on this share of everything either one flagged:")
    print(f"  Same grid cell: {_percent(agreement['same_cell'])}. Within about 200 m: {_percent(agreement['within_about_200_m'])}.")
    for row in baseline["track_agreement"]:
        print(f"  For comparison, {row['pairs'][0]} and {row['pairs'][1]}: "
              f"{_percent(row['same_cell'])} and {_percent(row['within_about_200_m'])}.")


def _percent(share):
    return "nothing flagged" if share is None else f"{share:.1%}"


def known_maturities(config):
    """Read each product's maturity from ASF. This reads names only, and opens nothing."""
    return {row["granule_id"]: row["maturity"] for row in list_all_maturities(config, SEARCH_START, MAYON_TRACKS)}


def build_preview(pair_ids, out_folder, preview_folder=PREVIEW_FOLDER, site_folder=SITE_FOLDER, publisher=publish_pair):
    """Copy the site and publish these pairs into the copy. The real site/ isn't touched."""
    preview_folder = Path(preview_folder)
    if preview_folder.exists():
        shutil.rmtree(preview_folder)
    shutil.copytree(site_folder, preview_folder)
    for pair_id in pair_ids:
        publisher(SITE_ID, pair_id, out_folder=out_folder, data_folder=preview_folder / "data")
    return preview_folder


class RoomyServer(http.server.ThreadingHTTPServer):
    """A local web server with room for the burst of files the site asks for at once.

    Python's default queue holds 5 waiting connections. When the computer is busy, the rest are
    refused, one of the site's scripts fails to load, and the page stays on "Loading".
    """

    request_queue_size = 128


def serve_preview(folder):
    """Serve the preview on this computer only, until Ctrl+C."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(folder))
    with RoomyServer(("127.0.0.1", PREVIEW_PORT), handler) as server:
        print(f"Preview: http://127.0.0.1:{PREVIEW_PORT}/  Press Ctrl+C to stop. Nothing has been published.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


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
    command = argv[0] if argv else None
    rest = [word for word in argv[1:] if word != "--drill"]
    drill = "--drill" in argv[1:]
    takes_pairs = command in ("review", "preview") and rest
    drill_process = command == "process" and drill and len(rest) == 1
    plain = len(argv) == 1 and command in ("check", "check-all", "process", "republish", "baseline")
    if not (takes_pairs or drill_process or plain):
        print(__doc__)
        return 1
    config = load_site(SITE_ID)
    try:
        require_owner_go_ahead(config)
        if drill_process:
            process_drill(rest[0], build_track_pairs(SITE_ID, search_gcov(config, SEARCH_START), search_gunw(config, SEARCH_START)), config)
        elif command == "review":
            held = review(rest, config, DRILL_FOLDER if drill else OUT_FOLDER, known_maturities(config))
            return 1 if held else 0
        elif command == "preview":
            serve_preview(build_preview(rest, DRILL_FOLDER if drill else OUT_FOLDER))
        elif command == "baseline":
            baseline = build_baseline(DATA_FOLDER, config, load_land(SITE_ID))
            BASELINE_PATH.write_text(json.dumps(baseline, indent=1) + "\n", encoding="utf-8")
            print(f"Saved {baseline['pair_count']} pairs to {BASELINE_PATH}")
        elif argv[0] == "republish":
            republish(config, build_track_pairs(SITE_ID, search_gcov(config, SEARCH_START), search_gunw(config, SEARCH_START)))
        elif argv[0] == "check-all":
            check_all(list_all_maturities(config, SEARCH_START, MAYON_TRACKS))
        elif argv[0] == "process":
            process(find_pairs(config), config)
        else:
            passes = search_gcov(config, SEARCH_START)
            check(eruption_pairs(build_track_pairs(SITE_ID, passes, search_gunw(config, SEARCH_START))), passes)
    except (NotReady, FileNotFoundError) as problem:
        print(problem)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

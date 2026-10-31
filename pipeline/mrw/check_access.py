"""Task T-003: check the Earthdata login and list NISAR GCOV passes over Mayon.

Run from the project folder:
    python pipeline/mrw/check_access.py

The first time, it asks for your Earthdata username and password (the password
is hidden while you type) and saves them in your home folder, never in this project.
"""
import re
import sys
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

import asf_search as asf
import earthaccess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mrw.search import BLIND_CUTOFF

# Mayon area (west, south, east, north) from the progress notes
MAYON_AOI = "POLYGON((123.56 13.14, 123.81 13.14, 123.81 13.38, 123.56 13.38, 123.56 13.14))"

# Product names look like NISAR_L2_PR_GCOV_<cycle>_<track>_<A or D>_<frame>_...
NAME_RE = re.compile(r"NISAR_L2_[A-Z]{2}_GCOV_(\d{3})_(\d{3})_([AD])_(\d{3})_")


def main():
    auth = earthaccess.login(persist=True)
    ok = bool(auth) and getattr(auth, "authenticated", False)
    print("Earthdata login:", "OK" if ok else "FAILED")

    results = asf.search(
        dataset=asf.DATASET.NISAR,
        processingLevel="GCOV",
        dataMaturity="PROVISIONAL",
        intersectsWith=MAYON_AOI,
        start="2026-06-17",
        # Stay blind to the eruption until the final thresholds are set.
        end=BLIND_CUTOFF - timedelta(seconds=1),
    )
    print(f"GCOV products found: {len(results)}")

    groups = defaultdict(list)
    for r in results:
        name = r.properties.get("sceneName") or r.properties.get("fileID") or ""
        m = NAME_RE.search(name)
        if not m:
            continue
        _cycle, track, direction, frame = m.groups()
        groups[(direction, int(track), int(frame))].append(r.properties.get("startTime", ""))

    print()
    print("Direction    Track  Frame  Passes  First                 Last")
    for (direction, track, frame), times in sorted(groups.items()):
        times = sorted(t for t in times if t)
        label = "ascending " if direction == "A" else "descending"
        first = times[0] if times else "-"
        last = times[-1] if times else "-"
        print(f"{label}   {track:5d}  {frame:5d}  {len(times):6d}  {first:20s}  {last}")


if __name__ == "__main__":
    main()

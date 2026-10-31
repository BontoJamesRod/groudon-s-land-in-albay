# Day plan 3

The owner is out on errands and can't answer questions. **Every hard rule in `NIGHT_PLAN.md` still applies.** Keep working on branch `night-1`; never push or merge. Download budget: at most 10 GB. Add a "Day 3" section to `NIGHT_REPORT.md` and keep it current.

## What the owner saw on the live app

- **Compare bug:** clicking Compare shows the compare view for a moment and then it snaps back to the normal map. The Close button works. Likely causes: the click handler is attached twice (so it toggles twice), the click bubbles to a map or document handler that closes the view or opens the readout, or the divider's pointer handlers treat the click as the end of a drag. Find the root cause; don't hide the symptom.
- **False alarms on quiet pairs:** Sep 26 → Oct 8 shows 4.74 km² and Oct 8 → Oct 20 shows 8.60 km² of new material, both before the eruption. The dots cluster on farmland west of Ligao and Guinobatan, in built-up areas, and on the upper northwest slopes inside the danger zone. Nearly all are low confidence (one signal).
- **Label overlap:** the "Permanent Danger Zone (6 km)" label sits on top of "Tabaco City", and the compare divider covers labels.

## Tasks, in order

0. **Leftovers:** read `NIGHT_REPORT.md` and finish any night-2 task that is unfinished and not blocked by an owner decision.
1. **Browser test harness:** use Python Playwright (`pytest-playwright`, Chromium). If it isn't installed, install it into `.venv` and add it to `pipeline/requirements.txt`. Put browser tests in `pipeline/tests/e2e/` with a pytest fixture that serves `site/` on a free local port, and mark them `e2e`. Add a CI step that installs Chromium and runs them.
2. **Fix the compare bug, test first:** write a failing browser test for TC-018: click Compare once, wait 1 s, the compare view is still open with both date labels; drag the divider; click Close and the normal map returns. Then fix the root cause and show the test passing. Also test TC-019 (missing image).
3. **Browser tests for the MVP:** cover every browser-checkable case in `docs/08-test-plan.md` §3 (TC-001 to TC-021, TC-028 to TC-034, TC-038, TC-040 to TC-047), using local fixtures from 08 §5 where needed and skipping with a reason where data or decisions are missing. Save a screenshot for each main screen at 1280 px and 360 px wide in `pipeline/reports/screens/`. Report pass, fail or skip for each TC.
4. **False-alarm study (adds to the T-016 report):**
   - For every published pre-eruption pair, report detected area by class, and where it falls: cropland, built-up, steep slopes facing the radar, coast, other. Use free land-cover data such as ESA WorldCover only as context, and cite it in `sources.json` if you use it.
   - Test candidate filters as config options that are **off by default**: minimum connected cluster size, showing high confidence only, and requiring the change to persist across 2 consecutive pairs. For each, show the area it removes on quiet pairs and what it keeps on the July 14 pair.
   - Add the results, figures and 2–3 recommended combinations to `pipeline/reports/threshold-study-night-1.md`. Don't change defaults, thresholds or `docs/`; these are owner decisions.
5. **Small UI fixes:** stop the danger-zone label overlapping town labels, and keep labels readable beside the compare divider. Check with the browser tests and screenshots.
6. **Optional visual pass:** if browser tools (Claude in Chrome) are connected, open the local site and check the main flows by eye. If they aren't, skip this.

## End of the day

Update the "Day 3" section of `NIGHT_REPORT.md`: task status, commits, browser test results with screenshot paths, the false-alarm study in short, data downloaded, and the decisions waiting for the owner.

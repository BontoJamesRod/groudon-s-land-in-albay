# Night plan 2

Same situation as night 1: the owner is asleep and nobody can answer questions until morning. **Every hard rule in `NIGHT_PLAN.md` still applies** (branch, secrets, data in Git, locked docs, blind to the eruption, thresholds, beginner-readable code, don't get stuck, Windows), with these changes:

- Keep working on branch `night-1`. Don't create a new branch; never push or merge.
- Download budget for tonight: at most 20 GB, counted separately from night 1.
- Add a new section "Night 2" to `NIGHT_REPORT.md` and keep it up to date; don't delete the night 1 section.

## Tasks, in order

0. **Finish night 1.** Read `NIGHT_REPORT.md`. Finish any night-1 task that is unfinished or failed, unless it's blocked by something only the owner can decide. Run `pytest` and the contract check, and fix any failures first.
1. **Independent review.** Use a subagent to review every change on `night-1` (`git diff main...night-1`) against `docs/04`, `docs/05`, `docs/06`, `docs/08` and the hard rules in `NIGHT_PLAN.md`. Ask it to report only problems that affect correctness, the spec or the rules, not style. Fix what it finds and list the findings and fixes in the report.
2. **T-026:** readout card (`readout.js`): decode the grid, find the town, distance, danger-zone notice, class and confidence, no-data reasons, loading and error states. Messages exactly as in 01 §6.
3. **T-027:** town search (`search.js`): suggestions after 2 letters, center the map and open the card, the no-match message.
4. **T-029:** compare view (`compare.js`): before and after images with a draggable divider and dates, and the missing-image message. The old swipe code in `pipeline/legacy/template.html` may help.
5. **T-030:** "What am I looking at?" panel. Move all interface text into `site/js/strings.js`. Add a test or script that fails if any text says a lahar, eruption or flood will happen (FR-038, TC-030).
6. **T-031:** Data sources panel.
7. **T-032:** site picker with the retry error (it only needs to work with the one site for now).
8. **T-033:** finish `404.html` and the README (what the app is, data sources, how to run the pipeline and the site).
9. **T-034:** phone and color-blind pass: 360 px layout, 44 × 44 px tap targets, a color-blind-safe palette, a text label for every class.
10. **T-020:** process and publish the track 111 backlog from 2026-06-17 onward, only passes acquired before 2026-10-30, within tonight's download budget. Stop early if the budget runs out and record which pairs are left.
11. **T-035, code plus a draft:** build the "How we checked this" panel and `validation.py`. Then make a draft validation record for the track 111 pair that spans 2026-07-14: find PHIVOLCS bulletins (or news reports quoting PHIVOLCS) from those dates, list the gullies they name, and mark whether the app detected new material there. Label the record `DRAFT, owner must review` and cite every source with its link.
12. **Decision prep, no decisions:**
    - **Channel lines (T-010):** extract the OpenStreetMap waterways inside the Mayon bounds to a candidate file in `pipeline/context/`. Match them against the PHIVOLCS channel names in `docs/05` §8 and report which channels were found, which are missing, and how good the match is. Don't build `channels.geojson` yet.
    - **Second site (T-036):** find 3 candidate sites on other continents with a clear 2026 surface change that the new-material method can detect (a volcanic eruption, landslide or flood, not only ground movement), and with NISAR PROVISIONAL passes before and after the event, acquired before 2026-10-30. For each: event and date, evidence links, track, frame and dates of a usable pair, and why it fits. Save as `pipeline/reports/second-site-candidates.md`. Don't choose one.

## End of night

Update `NIGHT_REPORT.md` with: each task's status, commit and test evidence; data downloaded tonight; the review findings; the two decision reports in short; and the owner's to-do list for the morning.

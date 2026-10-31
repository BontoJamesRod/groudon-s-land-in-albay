# Docs plan 6: bring the docs up to date with the owner's decisions (2026-11-01)

The planning docs in `docs/` are the spec for the build, but they've fallen behind what was decided and built on Oct 31 and Nov 1. This run brings them up to date, so the Nov 5–10 build can follow them.

**The owner asked for this docs update on 2026-11-01. That lifts the CLAUDE.md rule "don't edit `docs/`" for this run only.**

## Hard rules

1. Work on `night-1`. Commit and push `night-1`. **Don't merge into `main`.**
2. **Never write threshold values into `docs/`.** Describe rules in words; the values live in the site config.
3. No NISAR or Earthdata searches or downloads. Don't change `site/data/`, thresholds, or the channel-test outputs in `pipeline/reports/`.
4. **IDs are permanent.** Never renumber or reuse an ID. A removed item stays in its table, marked Removed. New items take the next free ID of their kind.
5. Every new ID must be traced through the docs: a feature (F) points to its user stories (US), and so on down to requirements (FR), screens (SCR), data files (TBL), file contracts (API), tasks (T) and tests (TC). Check that no ID is left dangling.
6. Keep the docs' plain, short style. Use the doc kit's existing tables and formats.
7. Run `pytest -q` and the contract check before each push, and push only if both exit cleanly. Check the exit codes, not just the output.

## A. Apply all 6 changes in `docs/notes/proposed-doc-changes.md` (owner approved)

Apply them exactly as written there, **including the code, test and data parts of changes 2 and 6**. After applying, mark each change at the top of that file as "Applied on 2026-11-01 by owner decision", with the commit hash.

## B. Record the decisions already made

1. **Final classification rule (gate 2, locked 2026-11-01, before any post-eruption data was opened).** Update every FR, the technical design and any test that describes classification: a pixel is flagged by its brightness change alone; coherence loss only raises a flagged pixel to high confidence and never adds area. Replace wording that calls the thresholds provisional with "final, set on 2026-11-01 before the post-eruption passes were opened". Products are still PROVISIONAL, so keep that wording where it refers to NISAR products.
2. **The 10 km reach limit** (live since Oct 31). Add it as a new FR: the site config sets a reach distance from the summit; detections beyond it are not shown, and a tap there says "Not checked: this map only looks within 10 km of the summit". Add a TC for it.
3. **The blind cutoff was lifted for the Oct 31 passes** (CLAUDE.md already says so). Record it in 04 or wherever the cutoff is described.
4. **The held pair D104 2026-09-25 → 2026-10-07** stays off the map by owner decision, because its baseline's coherence is unusually high. Record it in `PROGRESS.md`.

## C. Add one new feature: Channel timeline (Must)

The owner chose **only this feature** for the Nov 5–10 build. It builds on F-19 (Channels and towns), which stays.

- **What it does:** a list of the confirmed channels, sorted by how much changed since the last pass. Each channel has one bar per radar pass, showing the area flagged inside its channel strip (km²), and opening a channel shows its strip on the map.
- **Channel strips:** a strip of set width along each channel line. The width goes in the site config. The pipeline computes the flagged area per channel per pair from the final rule's flagged grid, never in the browser.
- **Which channels:** only channels whose line the owner has confirmed. Unconfirmed candidates (`pipeline/context/channel_name_candidates.geojson`) are never shown. Record the source and the confirmation in the data, as F-19 already expects.
- **Unequal gaps:** a pair whose gap isn't 12 days (the 24-day pair) is dimmed, with a short "24-day gap, not comparable" note, on this timeline and on the existing pass timeline (F-03). If that marking was already built tonight, record it as a done task instead of adding it again.

Add the new feature to every doc, with new IDs:

- **00 brief:** a new F row (next free F-ID, Must). Raise the version to 0.4 and update the summary so it says the app now watches how Mayon's channels change between passes. Keep the eruption as a chapter of that story.
- **01 PRD:** new US and AC, and new FRs for the list, sorting, bars, strips, unequal-gap marking and the confirmed-only rule.
- **02 MVP scope:** add the feature to the MVP.
- **03 user flows:** the screens or screen states for the channel list and the channel view, with new SCR IDs or changes to the existing channel card (T-028). Include the empty, loading and no-data states.
- **04 technical design:** a new ADR for computing channel strips in the pipeline, with strip width in config.
- **05 data design:** a new table for the per-channel, per-pair areas (a new file or new fields; choose the simpler one, and say why).
- **06 file contract:** the matching API entry, with an example.
- **07 roadmap:** the new tasks, with dependencies (channel confirmation by the owner comes first).
- **08 test plan:** new TCs covering each new FR.

## D. Write down what was considered but not added

In the brief's out-of-scope section, add one line each, marked "Considered on 2026-11-01, not in this version":

- why labels using rain data (eruption, heavy rain, little rain); rain stays a study input in the channel-test report
- a story intro with real radar images
- a quarry hint ("changed during little rain")

Also add a rule: **the app never labels any change as illegal or unpermitted.**

## E. Keep the second site (F-10, Must, for requirement R7)

Requirement R7 asks for sites on at least 2 continents. Keep F-10 as one Panama pair, using the same engine and the plain change map, with no channels. Update the brief and the roadmap to name Panama, citing `pipeline/reports/second-site-candidates.md` and the Panama trial, and keep its tasks (T-036, T-037) as the way to deliver it.

## F. Repair the task IDs

From the afternoon of Oct 31, commit labels stopped matching `07-roadmap.md`. For example, commit d274224 is labelled T-038, but T-038 in 07 is the eruption pairs; commits labelled T-042 to T-049 are night 4 and 5 work, while 07 uses those IDs for other tasks.

1. **Don't rewrite history.**
2. Add every piece of done work that isn't in 07 as a done task with a new ID. Where a commit's label already equals a free ID you assign (T-050 republish, T-051 test fix and night 5 report), keep it. Give all other mislabeled work the next free IDs after T-051.
3. Add an **ID errata** table to 07: commit hash, label used, real task ID, one line.
4. Add this rule to CLAUDE.md: "Use only task IDs that exist in `docs/07-roadmap.md` in commit messages. If the work isn't there, add it to 07 first, with the next free ID." Use the new IDs from this run on.

## G. Finish

1. Raise each changed doc's version and add a dated line to its change log, if it has one.
2. Update `docs/PROGRESS.md` to today's state: gates 1 and 2, the live final rule, the eruption passes not on ASF yet, and what's next.
3. Update the README's description of the app so it matches brief 0.4, in 3 to 5 plain sentences.
4. Write `docs/reviews/consistency-03.md`: list every new and changed ID and where it's referenced, and confirm there are no dangling IDs, no renumbered IDs and no threshold values in `docs/`. If any Mermaid diagrams changed, check that they still render.
5. Commit in readable steps: the 6 fixes, the decisions, the new feature, the out-of-scope lines, the ID repair, and the review. Use the new IDs in the commit messages. Push `night-1`.
6. Add a short "Docs run" section to `NIGHT_REPORT.md`: what changed, the new IDs, anything you couldn't decide (list it, don't guess), and the test and contract-check results.

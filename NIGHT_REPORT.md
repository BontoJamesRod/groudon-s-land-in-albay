# Night reports

Night 2 is at the end of this file.

# Night report 1 (2026-10-31)

Branch `night-1`. Nothing pushed, nothing merged into `main`.

## Status

| Task | Status | Commit | Test evidence |
| --- | --- | --- | --- |
| T-006 | Done | af1a13d | `pytest -q`: 35 passed. `python pipeline/mrw/contract_check.py`: 0 errors. CI itself has not run, because nothing was pushed |
| T-007 | Done, not run | 67f5ecc | `gitleaks/gitleaks-action@v3` confirmed in its README and as a tag on GitHub. Not executed: running the gitleaks binary locally was denied by the session's safety check, and pushing a test branch is forbidden. Owner: see morning checks |
| T-008 | Done | 710698e | `pytest -q`: 50 passed, including TC-036 |
| T-009 | Done | cad2170 | Contract check 0 errors; 12 towns; land = 84% of the box. Alignment with imagery is a manual check for the owner |
| T-011 | Done | bcd3a2a | Contract check 0 errors. July source read; the Manila Bulletin page returned 403, so its description comes from the 06 example, unverified |
| T-012 | Done | a8b34df | `pytest -q`: 64 passed, including TC-025, TC-026. Real search below |
| T-013 | Done | see `git log --grep T-013` | `pytest -q`: 77 passed. Tests cover the cache, byte log, budget stop and blind refusal |
| T-014 | Done | de3b85f | TC-027 passes. Reference pair median land change **+0.124 dB** against the expected ≈ +0.14 dB |
| T-015 | Done | beeedf5 | `pytest -q`: unit tests pass, including the fallback when a GUNW is missing |
| T-017 | Done | c903a45 | TC-022, TC-023 pass |
| T-018 | Done | e73fe9c | TC-024 ran on the reference pair: status ready, 4 granules, 0.38 km² high and 8.22 km² low at PROVISIONAL values. Contract check on `pipeline/out`: 0 errors |
| T-019 | Done | d0d6cce | `pytest -q`: 111 passed. Contract check on `site/data`: 0 errors. Reference pair published on this branch |
| T-016 | Done, analysis only | see `git log --grep T-016` | 10 pairs studied. No values chosen. See summary below |
| T-022 to T-025 | Done | see `git log --grep T-02` | Checked in headless Edge, below |

## Real ASF search (T-012)

Searched from 2026-06-01 with the request limited to before the cutoff: 29 GCOV (track 111 frame 8: 10, track 104 frame 82: 10, track 39 frame 8: 9), 24 GUNW, 26 consecutive pairs. No result had to be dropped by the cutoff filter. "Track 111 pairs match Vertex" was not compared by eye: owner check.

Track 111 dates: 06-21, 07-03, 07-15, 07-27, 08-20, 09-01, 09-13, 09-25, 10-07, 10-19. 08-08 is missing, so 07-27 → 08-20 spans 24 days, and the same gap appears on the other two tracks.

**Pairs with no GUNW on ASF:** `D104F082_20260621_20260703` and `A111F008_20260621_20260703`. So the track 111 pair spanning July 14 (07-03 → 07-15) has no previous-pair baseline and can't get coherence loss under FR-022.

## Data downloaded from ASF

Total: **3.34 GB** of the 20 GB budget, from `raw/download_log.jsonl`. About 0.98 GB of that was fetched twice: I started a second copy of the threshold study because I wrongly thought the first had died. Both finished with the same result.

## Threshold study summary

Full report: `pipeline/reports/threshold-study-night-1.md`. **No values were chosen.** PROVISIONAL values stay in the config: 3.0 dB, coherence loss 0.3.

| Candidate | Quiet pairs, km² flagged | July pairs, km² flagged |
| --- | --- | --- |
| A: 3.0 dB, 0.3 (PROVISIONAL) | 3.24–8.60 | 5.20–7.06 |
| B: 4.0 dB, 0.4 | 1.10–2.53 | 2.29–2.85 |
| C: 5.0 dB, 0.5 | 0.41–0.98 | 1.15–1.29 |

The method doesn't clearly separate the July event from quiet pairs at any candidate. Coherence loss shows no July signal, though only one July pair has a baseline. Both July maps do show a narrow streak on the slope, seen by eye only.

## Web checks (T-022 to T-025)

Served `site/` locally and checked it in headless Edge, using temporary copies for the broken states.

| Check | Result |
| --- | --- |
| Normal load | Latest pair selected, 12 town labels, danger-zone label, overlay, legend, 8.60 km² |
| TC-002: tiles fail | "Background map unavailable"; borders and ring stay |
| TC-004: zoom limits | Starts at 12; held at 10 and at 16 |
| TC-014: Next on latest | "This is the latest pass" |
| TC-017: empty pairs | "No radar passes processed yet for this site"; base layers only |
| TC-021: zero area | "No new material detected between Oct 8, 2026 and Oct 20, 2026" |
| Missing `pairs.json` | "Couldn't load Mayon Volcano, Albay. Try again." with Retry |
| Broken or wrong-version `sites.json` | "Couldn't load the site list. Try again." with Retry |
| Missing overlay image | "Couldn't load this pass. Try again." |
| Toggle off | Overlay removed; disclaimer stays |
| Screenshots | Desktop and 500 px wide looked right; borders line up with imagery |

Not checked: real phones, 360 px, TC-013 and TC-015 (only one pair is published).

## Findings the owner should know

- **The published reference pair shows 8.60 km² of "new material" with no recorded event.** The layer is labelled PROVISIONAL, but don't deploy it as real detection until the thresholds are set.
- **The July event date may be wrong.** The Asia News Network article is dated July 14 and appears to say the current happened on a Monday; 2026-07-14 is a Tuesday. I kept 07-14 as the plan says.
- **FR-011's "slope the radar can't see" will rarely appear.** The GCOV `mask` only flags invalid samples (0.02% of the crop), not layover or shadow.
- **The coastline line also traces the straight edges of the site box,** because land is clipped to the bounds. Cosmetic.
- **Land only covers Albay.** Land from another province inside the bounds would count as sea. A grid of sample points found none, but that isn't a full check.

## Files the plan expected that are missing

`CLAUDE.md` is not at the repo root (it is at `docs/CLAUDE (1).md`, which I read). `pipeline/notebooks/nisar_albay_starter.ipynb`, `pipeline/legacy/` and `docs/notes/` do not exist in the repo, so all pipeline logic was written from the docs and from inspecting real products. The granule names come from the examples in `docs/06-api-spec.md`.

## Assumptions

- T-006: `contract_check` rejects fields not in 05 ("exactly the column names in 05").
- T-006: `previous_pair_id` is checked for format only, not for presence in `pairs.json`. The baseline pair may be processed but not published, as with the reference pair tonight.
- T-006: a pair without coherence may omit the `coherence_loss` layer, because there is nothing to draw. 06 says a real pair has 5 layers but doesn't cover this case.
- T-006: `ci.yml` skips pushes to `main` because `deploy.yml` calls the same checks for those. Every push is still checked once.
- T-008: the site config holds three pipeline-only settings beyond the 05 columns: `thresholds`, `provisional_fields`, `tracks`.
- T-009: names are changed from "City of Tabaco" to "Tabaco City" to match 05 and TC-005. An extra `esri_world_imagery` row is in `sources.json` for TC-032.
- T-012: `search.py` holds `BLIND_CUTOFF`; it must be lifted by hand once the owner sets thresholds (T-038).
- T-018: web grid about 20 m (0.000185°). Areas are measured on the 10 m radar grid, so a small speck can show in the area but not in the image. "PROVISIONAL" is carried in the new-material layer's `title`, since 05 has no field for it.
- T-018: `new_material` lists 4 granules when coherence is used, including the previous pair's GUNW, because the layer really used it. TC-024 expects 3.
- T-022: request timeout 15 s (06 Open Question 2 is open).
- T-022 to T-025: text stays in the modules for now; `strings.js` is T-030.

# Night 2

Branch `night-1`. Nothing pushed, nothing merged. `docs/` wasn't edited; `docs/NIGHT_PLAN_2.md` is your file, and I left it untracked.

**Final evidence:** `pytest -q`: 190 passed. Contract check: 0 errors on `site/data`, 0 on `pipeline/out`. Both ran locally. **Downloaded tonight: 1.34 GB** of 20 GB (night 1: 3.34 GB), including 1.08 GB for the second-site probe. Nothing was fetched twice tonight.

## Read this first

1. **The method finds a signal on the named gullies, using brightness.** All three July pairs flag more than every quiet pair on the same track, in each of the three flanks PHIVOLCS named. Mi-isi on track 111 is 0.061 km² against at most 0.007. This is the best evidence so far, but it's small, coarse, and uses a rule I changed after a first misleading result. See `pipeline/reports/threshold-study-night-1.md`.
2. **Don't deploy the map as real detection yet.** All 9 published pairs show 3–15 km² of "new material" at PROVISIONAL values, mostly background change. The layer is labelled PROVISIONAL.
3. **CI has never run.** Every workflow was checked by reading only, because nothing may be pushed.

## Tasks

| # | Task | Status | Commit | Evidence |
| --- | --- | --- | --- | --- |
| 0 | Finish night 1 | Done; CI run blocked | 61b6904, 0f26788, 50bc6d5, 5a17008, b72ca05 | T-016 and T-022 to T-025 finished. T-007 still hasn't run on GitHub (below) |
| 1 | Independent review | Done, 2 passes, all Critical and Major findings fixed; CI run blocked | 219c6cd, dc94da5 | Findings below |
| 2 | T-026 readout | Done | d10e008, dc94da5 | TC-008, 009, 012 driven in headless Edge. TC-010: off-grid point gives "outside radar coverage". TC-011: a real 253 cell gives "a slope the radar can't see" |
| 3 | T-027 search | Done | e3a62a4, dc94da5 | TC-005, 006, 007 driven |
| 4 | T-029 compare | Done; drag test blocked | 27740a5, dc94da5 | TC-018 driven by keyboard; clip follows the divider. **Dragging by finger or mouse not tested.** TC-019 driven on a temp copy with the image removed: exact message, map unchanged |
| 5 | T-030 help, `strings.js`, wording test | Done | b20b892, dc94da5 | TC-028 driven. `test_wording.py` covers TC-030; a word list can still miss things, so read the text yourself |
| 6 | T-031 data sources | Done | b20b892 | TC-031, TC-032 driven. ASF links not opened (06 Open Question 3) |
| 7 | T-032 site picker | Done, one site | b20b892, dc94da5 | Picker opens and closes. Failure on switching untested until a second site exists |
| 8 | T-033 404 and README | Done; check at a Pages address blocked | 4c98f0c | Script commands tried. 404 page opened in Edge: "Page not found" with its link. Not tried at a GitHub Pages address |
| 9 | T-034 phone and color-blind | Done in emulation; real phone blocked | 65741e3 | 360 px iframe in Edge: no horizontal scroll, no tap target under 44 px, disclaimer stays on screen. Palette validator: CVD and normal-vision checks pass. **No real phone used.** The orange's contrast is low (2.19:1), which is allowed because each class has a text label |
| 10 | T-020 track 111 backlog | Done | 7116d6e | 9 of 9 pairs published, 2026-06-21 to 10-19. None left. `site/data` is 74 MB |
| 11 | T-035 panel, `validation.py`, draft | Done; publishing blocked on your review | 91fd0a2, 75729dd | TC-041 driven. TC-040 driven on a temp copy only, using the draft's table. Draft is refused by `--publish` and isn't in `site/data` |
| 12a | Channel lines (T-010) prep | Done, not built | a52f480 | `pipeline/reports/channel-candidates.md` |
| 12b | Second site (T-036) prep | Done, none chosen; boundary data and full-method run blocked | 22fc3bd, b686bf4 | `pipeline/reports/second-site-candidates.md` |

Three tasks share a commit (T-030 to T-032), since their code is in the same files.

## Blocked, with reasons

These parts of the tasks above are not done, and I can't finish them tonight.

| Task | What is blocked | Reason | What unblocks it |
| --- | --- | --- | --- |
| 8, T-033 | Opening the 404 page at a GitHub Pages address | It needs a deploy, and hard rule 1 forbids pushing | To-do item 1, then a deploy |
| 9, T-034 | Check on a real phone | No phone is available in this session; 360 px and tap targets were only emulated in Edge | Your phone check, to-do item 2 |
| 4, T-029 | Dragging the divider by finger or mouse | Headless Edge can't send a real pointer drag here; only the keyboard path was driven | The same phone check |
| 11, T-035 | Publishing the July validation | The plan requires your review of the draft | Your answer to decision 3 below |
| 12b, T-036 | Boundary data and a full-method run for a second site | `NIGHT_PLAN_2.md` doesn't ask for these, and both depend on which site you choose. The candidates were checked by ASF metadata and a brightness-only probe | Your choice of site |
| 1, and night 1 T-006 and T-007 | Running CI and the fake-secret test on GitHub | Hard rule 1 forbids pushing, and running the gitleaks binary locally was denied by the session's safety check. `pytest` and the contract check pass on the last commit locally only | To-do item 1 |

"Done" in the table above means the task's work is finished and tested as its evidence column says. Anything that needs a real phone, GitHub or your decision is in this table instead.

## Track 111 backlog (PROVISIONAL values)

| Pair | Coherence | High km² | Low km² | Total km² |
| --- | --- | --- | --- | --- |
| 06-21 → 07-03 | No | 0.00 | 7.39 | 7.39 |
| 07-03 → 07-15 (spans the event) | No | 0.00 | 5.20 | 5.20 |
| 07-15 → 07-27 | Yes | 0.12 | 6.27 | 6.39 |
| 07-27 → 08-20 (24 days) | No: unequal gaps | 0.00 | 14.51 | 14.51 |
| 08-20 → 09-01 | No: unequal gaps | 0.00 | 3.11 | 3.11 |
| 09-01 → 09-13 | Yes | 0.08 | 5.72 | 5.80 |
| 09-13 → 09-25 | Yes | 0.56 | 4.39 | 4.95 |
| 09-25 → 10-07 | Yes | 0.57 | 4.17 | 4.74 |
| 10-07 → 10-19 | Yes | 0.38 | 8.22 | 8.60 |

Before the unequal-gap fix, 07-27 → 08-20 showed 38.92 km². So most of that number came from comparing a 24-day pair with a 12-day pair, not from the ground. It's still the highest total, since a longer wait also changes brightness.

## Review findings and fixes

**First pass (commits up to b72ca05):**

| Severity | Finding | Fix |
| --- | --- | --- |
| Critical | CI used Node 20 actions, which the gitleaks README says were removed from runners in September | Moved to the current majors, each checked on GitHub: checkout v7, setup-python v7, configure-pages v6, upload-pages-artifact v5, deploy-pages v5 |
| Major | `check_access.py` could search past the cutoff | Search now ends before the cutoff |
| Major | Contract check accepted missing required files | Now required for published data |
| Major | `pairs.json` rows weren't compared with `pair.json` | Now compared |
| Major | Gitleaks can scan nothing on a merge | Added `secret-scan-history.yml`, weekly and by hand. **A merge push alone still isn't fully scanned: run it before releasing** |
| Major | README pipeline commands didn't start | Scripts now set their own path |
| Minor | Contract check too loose: 0.01 area slack, NaN, fake time zones, class 2 without coherence, and others | Fixed, with tests |
| Minor | Grid check allowed a pixel's shift; swapped or skipped passes; server hang; small areas rounding to 0; PROVISIONAL mark could vanish; hardcoded study thresholds; no run logs; manual deploy from any branch; some web error handling | Fixed |

**Second pass (commits after b72ca05):**

| Severity | Finding | Fix |
| --- | --- | --- |
| Critical | A draft validation could reach `site/data` through a re-publish | Drafts go to `pipeline/out/validation_drafts/`; publish never copies a validation; contract check rejects "DRAFT" |
| Major | Readout could show one pair's values under another pair's dates | Grid is now tied to its pair |
| Major | Compare had no guard while loading, and could leave images stuck on the map | Closing or reopening cancels a running load |
| Major | The 24-day pair is compared with 12-day baselines | Fixed conservatively: when the two gaps differ, the pipeline uses brightness only (FR-030), and the contract check enforces it. Both affected pairs were republished. Your call to keep this (decision 2) |
| Major | My draft's "no" results compared unlike things | Fixed: all pairs measured by brightness alone. All three became "yes" |
| Major | Map size went stale when the panel appeared | Map is remeasured and recentred |
| Major | Wording test missed real predictions | Wider word list, reads each string separately, covers all site text and JSON |
| Major | An Urgent Response GUNW could replace a PROVISIONAL one | GUNW search now filters by maturity too |
| Minor | Stale pair loads, 1-letter search submit, no card without a pair, compare covering borders, help without a pair, units missing from the legend, coastline source, candidate A's frames | Fixed |

**Left open:**

- Event date (question 1).
- `previous_pair_id` isn't checked against `pairs.json`. All 9 now link correctly except the reference to none on the first pair, which is correct.
- The download log is only written when a product finishes, so a hard kill could undercount. Totals are far under budget.
- `data.js` checks only some required fields, and `DataError` lacks the `message` format in 06 §2. The screens use `strings.js` instead.
- The second review's fixes and the unequal-gap fix weren't reviewed a third time. I re-ran the tests and contract check on all of them, and the Edge checks on the web fixes.

## Decision reports, in short

**Channel lines (T-010):** OSM has 714 waterway segments but only 58 are named, and name matching finds just **2 channels: Bulawan and Basud**. Basud-Lidong may be Basud. The other 12 listed channels, including Mi-isi and Bonga, are missing. OSM alone can't supply them by name; matching unnamed lines by hand is possible, but it's manual work. OSM's ODbL license needs reading first.

**Second site (T-036):** three candidates, none chosen. A brightness-only probe of real crops checked each one; the full method hasn't been run at these sites, and boundary data wasn't checked. The plan doesn't ask for boundary data, so it's listed as a step before choosing.

| Candidate | Event | Best pair | Radar probe | Main risk |
| --- | --- | --- | --- | --- |
| Azuero Peninsula, Panama | Landslides from the Mw 7.7 earthquake, 2026-10-09 | Track 141 frame 85, 09-27 → 10-09 (12 days) | Clear: at 5 dB, 0.04 → 0.65 km² | The earthquake may lower coherence everywhere; other tracks have almost no valid pixels there |
| Fuego, Guatemala | Pyroclastic flows, 2026-08-03 | Track 134, 07-17 → 08-10 (24 days) | About twice the area, 0.14 → 0.37 km² | Long gap; constant activity |
| Nyamulagira, DR Congo | Lava flow, active 2026-08-09 | Track 14, 07-21 → 08-14 (24 days) | No sign: 0.10 → 0.09 km² | Flow's start date unknown; little to validate against |

Panama and Fuego are on the same continent, and Nyamulagira is the only one in Africa.

## Your to-do list

**Do first**

1. Push `night-1` to a test branch and watch CI run, because no workflow has ever run. Add a fake secret on a throwaway branch to confirm the scan fails (T-007), and run "Scan history for secrets" by hand.
2. Open the site on a real phone: check the map centre, drag the compare divider, tap the map.
3. Read `pipeline/reports/threshold-study-night-1.md`, including the night 2 section, and decide the thresholds. They must be set before any eruption data is opened; then lift `BLIND_CUTOFF` in `search.py`.

**Your decisions**

1. **Event date:** GMA, quoting PHIVOLCS, reports the current on the morning of Monday **July 13**. `docs/05`, the plan and `events.json` say July 14. Both fall in the same pairs, so no marker moves. Which should the app say?
2. **24-day pairs:** I chose the conservative fix, since the plan says to fix review findings. Pairs whose gap differs from the previous pair's now use brightness only, low confidence at most. FR-022 doesn't cover this, so keep it or change it. To undo it, remove the `same_gap` condition in `export.py` and the matching contract rule. The total for 07-27 → 08-20 is still the highest (14.51 km²), so you may also want a warning on long gaps.
3. **July validation draft:** review `pipeline/context/validation_sheets/mayon_A111F008_20260703_20260715.json`. Is a flank wedge good enough to say "yes", or should it wait for channel lines? Flank directions came from search summaries, so check them against a bulletin.
4. **Channel source**, **second site**, and the remaining questions in `docs/PROGRESS.md`.

**Worth checking in the docs (I didn't edit them)**

- 01 §11 and 04 assume 12-day pairs; real gaps reach 24 days, and FR-022 needs a rule for unequal gaps.
- 01 FR-011: "a slope the radar can't see" doesn't match the GCOV mask, which doesn't flag layover or shadow.
- 08 TC-024 expects 3 granules; a pair with coherence uses 4.
- 06 says a real pair has 5 layers; pairs without coherence have 4.
- 04 and 07 say CI runs on pushes to `main`; the plan asked for every push and pull request.
- The plan points to `pipeline/legacy/`, the notebook and `docs/notes/`, which aren't in the repo.

**Also corrects night 1 above:** the 360 px, TC-013 and TC-015 checks listed as not done were done tonight in emulation. The July date concern is now backed by GMA's report.

# Day 3

Branch `night-1`. Nothing pushed, nothing merged. No file in `docs/` was changed: `docs/DAY_PLAN_3.md` and `docs/NIGHT_PLAN_2.md` are your files, and I left them untracked.

**Final evidence, all run locally:** `pytest -q`: 295 passed, 6 skipped, 1 expected failure. That splits into `pytest -m "not e2e"`: 208 passed, and `pytest -m e2e`: 87 passed, 6 skipped, 1 expected failure. Contract check: 0 errors on `site/data`, and 0 on `pipeline/out` under its unpublished rules. **Downloaded today: under 0.05 GB** of 10 GB (estimate, as these reads aren't logged). That's two map windows that take 8.8 MB on disk, and one read of a July product's metadata. No radar crops were fetched, and nothing from on or after 2026-10-30 was opened.

## Read this first

1. **Compare is fixed, but do a hard reload to see it (Ctrl+Shift+R).** In real Chrome a normal reload kept running the old JavaScript. It showed the old labels until I hard reloaded. The real host may cache files too, so a visitor could see old code for a while.
2. **Most false alarms are on farmland.** Cropland is 7.7% of the land but holds 41–80% of detected area. No filter fixes this without also losing July signal.
3. **Don't assume Oct 8 → Oct 20 is a false alarm.** It has 2.49 km² inside the danger zone, about 4 to 40 times the other pairs, and it's the last pair before the eruption. Check it against PHIVOLCS bulletins first.
4. **CI still has never run**, including the new browser step.

## Tasks

| # | Task | Status | Commit | Evidence |
| --- | --- | --- | --- | --- |
| 0 | Leftovers | Done; 3 parts blocked (below) | d0b5561, 88ce6eb | Divider drag by mouse is now tested. TC-011, 019 and 040 are now repeatable tests |
| 1 | Browser test harness | Done; CI run blocked | d0b5561 | `pipeline/tests/e2e/`, marked `e2e`, serves `site/` on a free port. `pytest-playwright` added to requirements. CI installs Chromium and runs them, but that step has never run |
| 2 | Compare bug and TC-018, TC-019 | Done | d0b5561, 313ce06 | Before the fix: 3 failed, 6 passed. After: all pass |
| 3 | Browser tests for the MVP | Done | 88ce6eb, 313ce06 | Table below. 20 screenshots in `pipeline/reports/screens/` |
| 4 | False-alarm study | Done; nothing turned on | fa8a62f | `pipeline/reports/threshold-study-night-1.md`, day 3 section. 208 non-browser tests include the new filter tests |
| 5 | Small UI fixes | Done | e7ae4db, 313ce06 | Before the fixes: 9 label tests failed. After: all 24 pass |
| 6 | Visual pass | Done on desktop | none: no code | Claude in Chrome was connected. Checked the main map, Compare, a divider drag and the labels by eye, after a hard reload. Screenshots at 360 px were read by eye too |

## Blocked, with reasons

| Task | What is blocked | Reason | What unblocks it |
| --- | --- | --- | --- |
| 0, 1 | Running CI, including the new browser step, and the fake-secret test | Hard rule 1 forbids pushing | You push `night-1` to a test branch |
| 0, night 2 T-033 | Opening the 404 page at a real GitHub Pages address (TC-038 passes on a local server that behaves the same way) | It needs a deploy | The same push, then a deploy |
| 0, night 2 T-034 | Check on a real phone, including a finger drag of the divider | No phone in this session. 360 px and touch tap are emulated in Chromium, and the drag used a mouse | You, on a phone |

Not attempted, because they're your decisions and the plan excludes them: publishing the July validation, the second site, the channel source.

**One review leftover stays open on purpose:** `previous_pair_id` isn't checked against `pairs.json`. I tried it and took it back, because it would stop a pair being published on its own when its baseline pair isn't published. All 8 real links are correct today.

## Compare bug: root cause

**Cause:** when a pair finished loading, `main.js` always called `compare.close()`. If you picked another pair and clicked Compare before that pair had finished loading, the view opened on the old pair, then closed when the new pair arrived. With a slow file it opened at 0.06 s and closed at 1.4 s.

**How sure I am:** this is the only path I could make fail, and it matches what you saw, but I can't watch your session. A single click on a settled page never failed, at 1280 px, at 360 px by touch, or as a double click, and it stayed open in real Chrome too. None of the plan's three guesses was the cause: there is one handler, nothing on the map closes the view, and the divider's handlers don't either. **If it still snaps back after a hard reload, tell me what you clicked first**, since that would mean there's a second cause.

**Fix:** a visitor who is comparing keeps comparing, and the view moves to the new pair's images. Close is what ends it. Compare is also disabled until the first pair has loaded, because clicking early falsely said the images were missing.

**Also fixed:** dragging the divider to the far right blocked the Close button, and the divider could cut through the date labels. A touch interrupted mid-drag now ends the drag properly.

## Browser test results (`pipeline/tests/e2e/`)

| TC | Result | Note |
| --- | --- | --- |
| 001–009 | Pass | |
| 010 | Pass | No published grid has a 255 cell, so it taps just off the grid, which reads as 255 |
| 011–014 | Pass | |
| 015 | July: pass. Eruption: skip | No eruption pair may be opened yet |
| 016 | Pass | |
| 017 | Pass | Empty-pairs fixture |
| 018 | Pass | Includes a real mouse drag both ways, and the snap-back case |
| 019 | Pass | Each image missing in turn |
| 020 | Pass, on the latest pair | The doc asks for the eruption pair |
| 021 | Pass | Zero-area data made in the test; the image itself isn't blank |
| 028 | Pass | PHIVOLCS link's address checked, not opened |
| 029, 030 | Pass | |
| 031 | Pass, on the latest pair | ASF links' format checked, not opened |
| 032 | Pass, without channels | Channels aren't built |
| 033 | Skip | No second site: your decision |
| 034 | Pass | Uses a made-up second site, in the test browser only |
| 038 | Pass, locally | Real Pages address blocked |
| 040 | Pass, from a local fixture | Uses the July draft's table in the test only. Nothing is published |
| 041 | Pass | |
| 042 | Pass, **with one known failure** | Leaflet's small credit link in the map's corner is under 44 px, so that test is marked as an expected failure. Every other control passes. Emulated, not a real phone |
| 043 | Pass | Chromium's deuteranopia and protanopia emulation |
| 044–047 | Skip | Channels aren't built: they wait for your channel source |

The plan's list doesn't include TC-022 to 027 or 035 to 037, which aren't browser cases.

**Screenshots:** `pipeline/reports/screens/`, as `<screen>-1280.jpg` and `<screen>-360.jpg`, for main, readout, search, compare, help, sources, check, picker, no-pairs and not-found. A normal test run doesn't change them; `test_screens.py` says how to refresh them.

## UI fixes

- **Danger-zone label:** moved to just outside the ring's south edge. Below the default zoom, a town name that would touch it is hidden until you zoom back in, because the danger zone matters more. All 12 town names show at the default zoom.
- **Divider:** a map label that the line would cut moves to the nearer side, then returns when Compare closes.
- **Still open at 360 px:** the map is about 270 px tall, smaller than the ring, so the danger-zone label is off screen until you pan. This was already true with the label in the north, and fixing it means a different default zoom for phones, so it's a question for you below.

## False-alarm study in short

Full tables, figures and limits are in `pipeline/reports/threshold-study-night-1.md`. All filters are off, and no default or threshold changed.

| Filter | Removed on quiet pairs | July flank signal kept |
| --- | --- | --- |
| Clusters from 2,000 m² | 16% | 70% |
| Clusters from 10,000 m² | 54% | 42% |
| High confidence only | 97% | **0%**: the July pair has no coherence |
| Persists into next pair | 86% | 18%, and it needs a pass 12 days later |
| Mixed: high only with coherence, else clusters from 10,000 m² | 75% | 42% |

Your own observations mostly hold. Ligao and Guinobatan: 41–80% of detections are on cropland across the site. Built-up areas are only 1.5–4% of detected area, though. The upper northwest slopes stand out in one pair only, and those slopes face away from the radar.

## Decisions waiting for you

1. **Filter:** none, 2,000 m², 10,000 m², or mixed? The study recommends these three and advises against persistence. Mixed needs a small code change.
2. **Oct 8 → Oct 20:** real change before the eruption, or a false alarm? Please check PHIVOLCS bulletins for October.
3. **Cropland:** would you consider hiding or dimming it? It would remove more than any filter, but new material can reach fields too. It's outside the brief, so I didn't test it as a filter.
4. **Phone map:** should phones start one zoom level further out, so the whole ring and its label show? `default_zoom` is PROVISIONAL.
5. **Leaflet's credit link** (TC-042): make it bigger, or remove it? Leaflet's license doesn't appear to need the link, but check before removing it.
6. All the night 2 decisions are still open: thresholds, event date, 24-day pairs, July draft, channel source, second site.

## Worth checking in the docs (I didn't edit them)

- 05 `context_use` has no value for analysis data, so WorldCover and the elevation model are listed as `validation`, and they now appear in the Data sources panel.
- 08 TC-020 and TC-031 need an eruption pair, which the blind rule forbids for now.
- 08 §5 asks for fixture files for the missing-image and zero-area pairs. The tests make those in the browser instead, so no large copies are stored. `grid_cells.json` and `empty_pairs.json` are real files.

## After the Day 3 report

These replace the matching lines above where they differ.

- **Pushed:** you asked for `night-1` to be pushed, and commit 3caa367 went up. `main` wasn't touched, and nothing deployed.
- **CI ran for the first time and passed** on 3caa367: secret scan, tests, browser tests and contract check. The fake-secret test still hasn't been done.
- **Real phone check passed.** You ran it in Brave on your phone over Wi-Fi and reported that every step worked, including the finger drag of the divider. It used a local server, not the live site.
- **404 page:** you set Pages to GitHub Actions. The live address still shows GitHub's own 404, because nothing is deployed. It needs your yes to merge into `main`.
- **Phone drawer, at your request:** you found the lower panel bigger than the map. On phones it's now a drawer, closed by default, opened by tapping or swiping its handle. `site/js/drawer.js`, tests in `pipeline/tests/e2e/test_drawer.py`.
  - Closed, it keeps the pass controls and says the results are PROVISIONAL. The legend and total area are one tap away, which is a trade-off, since a first-time visitor won't see them straight away.
  - The map at 360 px went from about 270 px to about 435 px tall, so the whole ring and its label now show. That settles decision 4, the phone map zoom.
  - The drawer tests against the old site code: 9 failed, 3 passed. Full run now: `pytest -q`: 310 passed, 6 skipped, 1 expected failure. Contract check on `site/data`: 0 errors.
  - The drawer hasn't been checked on a real phone yet. A swipe is emulated with a mouse in the tests.

# Afternoon run

Branch `night-1`. `main` wasn't touched. `site/data` wasn't changed. This section also covers the earlier "After Day 3 analysis" request, whose tasks are inside this plan.

**Final evidence:** `pytest -q`: 317 passed, 6 skipped, no expected failures left. Contract check: 0 errors on `site/data`, and 0 on `pipeline/out` under its unpublished rules. **Downloaded: about 0.35 GB** of 10 GB: 0.315 GB of NISAR crops for Panama plus the 32 MB boundary file. Nothing from on or after 2026-10-30 was opened.

## Read this first

1. **Oct 8 → Oct 20 is 98% coherence only, and neither radar geometry nor noise explains it.** It's still unknown whether it's real. Check rain records and PHIVOLCS bulletins.
2. **A reach zone removes far more than any filter**, mostly by removing farmland, but it also stops the map looking beyond its edge. It's your call.
3. **On Panama the method responds strongly but not specifically:** 117.3 km² against 4.72 km², with 26% of the land flagged.
4. **Site speed is fine:** 0.78 MB and 2.0 s, so overlays stay as PNG.

## Tasks

| # | Task | Status | Commit | Result |
| --- | --- | --- | --- | --- |
| 1 | Housekeeping | Done | 2170070 | `CLAUDE.md` is at the root. `.dodsrc` is untracked and ignored, and it's still on your computer. I didn't open it. **It stays in old commits on GitHub**, since history isn't rewritten, so if it holds anything private, change that |
| 2 | Oct 8 → Oct 20 split | Done | 650f679 | Below, with `pipeline/reports/october-signal-split.png` |
| 3 | Masks | Done | 650f679 | Below, with full tables in `pipeline/reports/threshold-study-night-1.md` |
| 4 | Panama trial | Done | a88c1ee | Below, with `pipeline/reports/second-site-candidates.md` |
| 5 | Performance and version strings | Done; WebP not needed | 06f0fb5 | Below |
| 6 | Credit link tap size | Done | 9a0d2a2 | TC-042 passes, with no expected failure left. Checked in emulation, not yet on a real phone |
| 7 | Proposed doc edits | Done | bdde5b7 | `docs/notes/proposed-doc-changes.md`, all six items. No other doc was edited |
| 8 | This section | Done | this commit | |
| Earlier request | Fake-secret CI test | Done | none on `night-1` | The scan failed as it should, and later steps were skipped: [the run](https://github.com/BontoJamesRod/groudon-s-land-in-albay/actions/runs/41182890528) |

Nothing is blocked.

**Left for you to clear:** the fake-secret branch was deleted locally as asked, but `throwaway/fake-secret-test` is still on GitHub. Its value is made up and unlocks nothing. To remove it: `git push origin --delete throwaway/fake-secret-test`. Its commit may also trip "Scan history for secrets" if that scan reaches it, so remove the branch before relying on that scan.

## Oct 8 → Oct 20 inside the danger zone

![Which signal flagged each cell](pipeline/reports/october-signal-split.png)

| Signal | km² | Share | NW of summit | On steep away-facing slopes | Near the noise floor |
| --- | --- | --- | --- | --- | --- |
| Coherence only | 2.433 | 98% | 1.180 | 0.447 | 0.000 |
| Brightness only | 0.054 | 2% | 0.021 | 0.019 | 0.000 |
| Both | 0.004 | 0.2% | 0.002 | 0.000 | 0.000 |

- Away-facing slopes are 10% of the zone's land and hold 18% of the coherence-only area, so geometry explains only a little.
- Noise explains none of it, at any test level from -25 to -18 dB. The noise level and beam angle are assumed, not read from the product.
- Other pairs with coherence in use have 0.02–0.37 km², so this is about 7 to 120 times as much.
- Coherence falling without brightness changing could be wet ground or vegetation, and could be thin disturbance. A thick fresh deposit would usually change brightness too, which leans against one, but that's general reasoning and this study didn't test it.

## Masks

Quiet set: 7 pairs, leaving out July and Oct 8 → Oct 20.

| Option | Quiet removed | July flanks kept | Oct 8 → Oct 20 kept |
| --- | --- | --- | --- |
| Within 8 km | 92% | 100% | 33% |
| Within 8 km + clusters from 2,000 m² | 94% | 69% | 32% |
| Within 10 km | 70% | 100% | 47% |
| Within 10 km + clusters | 77% | 69% | 43% |
| Within 12 km | 41% | 100% | 65% |
| Within 12 km + clusters | 53% | 69% | 59% |
| Noise floor and away-facing slopes | 2% | 94% | 93% |
| Noise and away-facing + clusters | 19% | 64% | 84% |

**Read the 100% with care:** the flank wedges only reach 3.8 km, so these masks can't touch them. It shows they're safe for those flanks, not that they find the event better. July's flanks (0.120 km²) are still below the worst quiet pair's (0.374 km²).

**My pick, if you want a mask now: within 10 km alone.** It removes 70% with no loss in the flanks. The map would have to say it only looks within 10 km, and it cuts off Guinobatan's label point (10.3 km). Skip the noise and away-facing mask, because it removes 2% and costs 6% of the flank signal.

## Panama trial

| Measure (km²) | Quiet, 09-15 → 09-27 | Earthquake, 09-27 → 10-09 |
| --- | --- | --- |
| Total | 4.72 | 117.30 |
| High confidence | 0.09 | 4.66 |
| Brightness alone | 2.40 | 7.73 |
| High confidence, in the box on the cluster | 0.006 | 1.75 |

- 26% of the land is flagged, far more than landslides could cover, so low confidence is mostly a region-wide fall in coherence. High confidence looks more useful.
- It hasn't been checked against the mapped landslides, and the earthquake's time against the 23:53 UTC pass isn't confirmed.
- **Boundaries:** geoBoundaries gbOpen Panama ADM2, from the Smithsonian Tropical Research Institute (2012), CC BY 4.0. The record's license detail says "need to update", so read its source before any public use.
- Output is in `pipeline/out/sites/panama/` only. The config isn't in `pipeline/sites/`, so publishing can't list it.

## Performance (TC-050)

Fast 4G, cold cache, real tiles, median of 3 loads, from a local server. A real host adds distance but also compresses files.

| Screen | First view | Until the first pair shows |
| --- | --- | --- |
| 1280 px | 0.78 MB | 2.0 s |
| 360 px | 0.58 MB | 2.0 s |

- That's under the suggested 5 MB and 5 s, so **no WebP switch or republish**, as your condition said. The final NFR-001 target is still `[TBD]`. `test_performance.py` keeps checking the budget in CI, with fake tiles.
- **Later loads are bigger:** Compare fetches about 3.2 MB (about 3 s at this speed, calculated) and the first map tap fetches a 1.75 MB grid (about 1.6 s, calculated). So TC-051's suggested 200 ms can't hold for a first tap. WebP could shrink the Compare images if that matters.
- **Stale code:** JS and CSS links now carry a version made from each file's contents, including modules, through an import map in `index.html`. After changing `site/js` or `site/css`, run `python pipeline/mrw/stamp_assets.py`. A test fails if you forget. Leaflet isn't stamped, because its folder name already carries its version. It's checked in tests, and it can't help visitors holding the old `index.html` until that page refreshes.

## Decisions waiting for you

1. **Go live?** Merging `night-1` into `main` makes the map public. The 404 check at the real address waits on this too.
2. **Mask or filter:** none, within 10 km (my pick), within 12 km, or a filter from the day 3 list.
3. **Oct 8 → Oct 20:** check rain records and PHIVOLCS bulletins. Do you want a pass from another track compared too?
4. **Thresholds:** still PROVISIONAL, and they must be set before eruption data is opened.
5. **Second site:** Panama now has a full-method result, but it's unvalidated. Compare it with the mapped landslides, or try Fuego?
6. **Doc edits:** accept or change the six items in `docs/notes/proposed-doc-changes.md`. Item 1 is also the 24-day decision. Item 2 changes visitor wording.
7. **Still open from earlier:** event date (July 13 or 14), July validation draft, channel source, cropland.

# Going live

You chose **within 10 km alone** and asked to go live. Filter `max_distance_km: 10` is on for Mayon, and all 9 pairs were republished from cache, with no radar data downloaded.

| Pair (UTC dates) | Before (km²) | Within 10 km (km²) |
| --- | --- | --- |
| 06-21 → 07-03 | 7.39 | 2.38 |
| 07-03 → 07-15 (July event) | 5.20 | 1.80 |
| 07-15 → 07-27 | 6.39 | 2.31 |
| 07-27 → 08-20 (24 days) | 14.51 | 4.09 |
| 08-20 → 09-01 | 3.11 | 1.15 |
| 09-01 → 09-13 | 5.80 | 1.74 |
| 09-13 → 09-25 | 4.95 | 1.24 |
| 09-25 → 10-07 | 4.74 | 1.36 |
| 10-07 → 10-19 | 8.60 | 4.07 |

**How the limit shows:** a white dotted ring, "within 10 km of the summit" in the legend title, a line in the help panel, and a tap beyond the ring says "Not checked: this map only looks within 10 km of the summit" rather than "No new material detected".

**Known limits on the live map:** thresholds are still PROVISIONAL. Most of what's left is still likely not new material. Oct 8 → Oct 20 is unresolved. `reach` is set in two places, the site config and `map.js`, and a test fails if they differ. On a phone at the default view the ring is off screen, so the closed drawer's handle states the limit.

**Live:** https://bontojamesrod.github.io/groudon-s-land-in-albay/ . Checked there in Chromium at 1280 and 360 px: map, 12 town labels, radar layer, ring and legend limit, Compare still open after 2.5 s, TC-038 (404 status, "Page not found", link opens the map), all requests HTTPS, no console errors. This replaces the earlier block on the 404 check. Drawer, swipe and the larger credit link haven't been checked on a real phone.

## Compare labels stay still

You found town labels sliding around while dragging the divider. That came from my day 3 fix, which pushed labels aside. Labels now never move, and the white line runs behind them, so they stay readable. This replaces the "Divider" item under Day 3's UI fixes.

# Evening run

**One thing differs from what you asked:** I published 2 of the 3 track 104 pairs, and held back 09-25 → 10-07. It would have shown 102.26 km² of new material on the public map, about a third of the land inside the 10 km ring, and only 1.94 km² of that reaches the brightness threshold. The cause is its baseline (09-13 → 09-25), whose coherence is unusually high, so coherence appears to fall across the whole scene. It passes the contract check and is ready in `pipeline/out`. To publish it anyway: `python pipeline/mrw/publish.py mayon mayon_D104F082_20260925_20261007`.

| Task | Result | Evidence |
| --- | --- | --- |
| 1. Label and 36 px fixes live | Done | Merged as 6781de6 after CI passed on 403a385. Live site in Chromium: 12 labels didn't move at any of 5 slider positions at 1280 and 360 px; Compare moved the map 0 px at 1280 px; TC-038 passed. The drag used a mouse, not a real phone |
| 2. Remove the test branch, scan history | Done, nothing to delete | `throwaway/fake-secret-test` was already gone from GitHub when I checked. I don't know who removed it. "Scan history for secrets" run [41202424240](https://github.com/BontoJamesRod/groudon-s-land-in-albay/actions/runs/41202424240): 61 commits scanned across all branches, **no leaks found**. It ran on 6781de6, so T-039 and later commits get the normal CI scan, not this one. I started it from your signed-in Chrome, because `gh` isn't logged in here |
| 3. Calibration check | Done | "Evening run" in `pipeline/reports/threshold-study-night-1.md`. At 3.0 dB its wedge numbers match night 2's. No default changed |
| 4. Track 104 pairs | Done, except the held pair above | Published 09-13 → 09-25 (0.93 km²) and 10-07 → 10-19 (2.13 km²). The track 104 eruption pair's baseline, 10-07 → 10-19, is ready. 0.26 GB of the 10 GB limit used |
| 5. Eruption runbook | Done, not run on eruption data | `pipeline/RUNBOOK-eruption.md` and `pipeline/mrw/eruption_run.py`. The script stops before contacting ASF unless thresholds are FINAL and the cutoff is lifted. I ran it for real only to confirm it refuses. On a throwaway copy with both edits made, all tests pass, using fake data only |
| 6. This report | Done | |

**The blind rule held.** The latest pass any search returned was 2026-10-19. Thresholds in the config are still PROVISIONAL, at 3.0 dB and 0.3. Nothing in `docs/` changed.

**Tests changed for the runbook:** five tests assumed the cutoff and PROVISIONAL status could never change, so they would have failed on the day. They now check the same refusals in a way that survives the lift.

## What the calibration says

Full tables are in the study. All of this is within 10 km, and none of it chooses a value.

| T | Pairs labelled quiet, total (km²) | July pairs, total (km²) |
| --- | --- | --- |
| 3.0 dB | 0.755–1.937 | 1.804–2.239 |
| 4.0 dB | 0.286–0.586 | 0.742–0.816 |
| 5.0 dB | 0.165–0.226 | 0.339–0.375 |

- **Dropping coherence-alone removes most of the area,** and 4 and 5 dB separate July from the quiet pairs. That separation doesn't hold against every pair: 06-21 → 07-03 and the 24-day pair are above the July pairs at all three values.
- **Coherence at 0.4 doesn't confirm July.** The only July pair with a baseline has 0.003–0.005 km² of high confidence, below most of the quiet pairs with a baseline.
- **Mi-isi holds up on all three tracks at all three values, but it isn't only in the event pair.** The pairs just before and after July on track 111 have about the same area.
- **I need to correct the night 2 claim.** It said July beat quiet on every track and flank. With more quiet pairs on track 104, Basud and Bonga no longer do at any T.
- **The October patch mostly doesn't repeat on track 104.** Coherence-only area in the danger zone is 0.304 km², against 2.434 km² on track 111, and 0.000 against 1.167 km² northwest of the summit. That leans against change on the ground without settling it.
- **The October track 104 pairs have more brightness change in the danger zone than any July pair** (0.44–0.455 km² at 3 dB, against 0.205–0.429). Nothing here says why, and these are the last pairs before the eruption.

## Decisions waiting for you

1. **Final thresholds, and the rule.** "Brightness leads" isn't how the site works today. If you choose it, `classify.py` must change first, as step 1 of the runbook says. Everything else about the eruption pairs waits on this.
2. **The held pair, D104 09-25 → 10-07.** My recommendation is to leave it off the public map. It isn't needed as a baseline for the eruption pair.
3. **What to do about baselines like that one.** The same problem could inflate an eruption pair's coherence loss. Under "brightness leads" it can only raise confidence, not add area, which is one point in that rule's favour. The runbook tells you to check for it before publishing. I didn't add a fix, because that's a method change.
4. **Still open from before:** Oct 8 → Oct 20 against rain records and PHIVOLCS; a real-phone check on the live site; second site; doc edits; event date; July draft; channel source; cropland.

**Worth knowing:** the timeline now mixes two tracks, and each pair's label names its track. Areas from different tracks aren't directly comparable, because the viewing angle differs.

**Final evidence:** `pytest -q`: 337 passed, 6 skipped. Contract check: 0 errors on `site/data`. **Downloaded this evening: 0.26 GB** of 10 GB (5.25 GB logged in `raw/` in total). Nothing from on or after 2026-10-30 was searched for or opened.

# Night 4

The full report is [pipeline/reports/channel-test.md](pipeline/reports/channel-test.md). It's for gate 1 on Sunday.

**Verdict: GO, by the smallest possible margin.** The quarry-to-quiet ratio reached 2.0 in exactly 5 of 9 track 111 pairs at 3.0 dB combined. Leaving out either of two single quarries makes it 4 of 9, and the test can't say whether the change is digging or bare gravel responding to the weather.

- **Part A:** OpenStreetMap has 8 quarries (77.81 ha), all kept. Six are near Padang, and none is near Budiao or Maninila. Check them by eye in `pipeline/context/channel_test_sites.kml`.
- **Part B: skipped on the first attempt.** NASA's server refused the IMERG files with a 403. "Rain rerun" below has the results.
- **Part C:** the channel-to-land ratio reached 1.5 in 9 of 9 pairs, but a strip mask would keep 53–62% of the 10 km circle's flagged area while already covering 51% of its land.

**Downloads:** IMERG rain 0 bytes on the first attempt (see "Rain rerun" below). OpenStreetMap quarries and places were two small Overpass queries. NISAR nothing.

**No NISAR product was searched for or opened** beyond the cached crops already in `raw/`, the latest dated 2026-10-19. `site/`, the site config, `classify.py`, the thresholds and `docs/` are unchanged on `night-1`, and nothing was merged into `main`. `docs/NIGHT_PLAN_4.md` is still untracked, because the plan says not to change `docs/`.

**Commits:** c00d4ae (the test and its report), plus the commit that adds this section.

**Part E, optional, done:** branch `brightness-leads-prep` (f41a49c) adds a `thresholds.rule` switch to `classify.py`. Brightness alone decides whether a pixel is flagged, and coherence can only raise it to high. The default is unchanged, Mayon's config doesn't choose it, and no existing test changed. It's pushed but not merged, and it contains no threshold values. On that branch: 354 passed, 6 skipped.

**Final evidence:** `pytest -q` on `night-1`: 344 passed, 6 skipped. Contract check: 0 errors on `site/data`.

**Rain rerun: the quarry ratio reaches 2.0 in 2 of the 3 low-rain pairs, and no pair meets the heavy-rain rule** (100 mm in 3 days; the most was 50.5 mm), so the verdict stays GO and heavy rain is untested. Oct 8 → Oct 20 was on the wet side but not extreme: 95.5 mm, the highest daily rate of the 9 pairs. Rain download: 1.699 GB, after the owner raised the limit from 1.5 to 1.75 GB for this fetch. No NISAR product was searched for or opened. Details are under "Rain rerun" in [pipeline/reports/channel-test.md](pipeline/reports/channel-test.md).

# Night 5

**Eruption data: not on ASF yet, so nothing was downloaded or processed.** `eruption_run.py check` at 2026-10-31 16:26 UTC (the computer's clock) reports no new pass on track 104 or track 111. Earlier passes suggest about 10:16 UTC for track 104 and 21:13 UTC for track 111, so at that time the track 111 pass hadn't been due yet. Only names were checked. To look again: `python pipeline/mrw/eruption_run.py check`.

**The owner's gate 2 decision is in place on `night-1`, and not on `main`.** Thresholds are FINAL and the rule is brightness leads. The cutoff opens the Oct 31 passes only. T-049, which holds the decision and the lifted cutoff, was committed before any search for eruption passes, so the history shows the thresholds came first.

All 11 published pairs were redone. Areas are km² within 10 km. High confidence didn't change on any pair, because this rule only removes coherence-only area.

| Pair (UTC) | Coherence used | Total before | Total now | Removed | High confidence |
| --- | --- | --- | --- | --- | --- |
| A111 06-21 → 07-03 | No | 2.38 | 2.38 | 0.00 | 0.00 |
| A111 07-03 → 07-15 | No | 1.80 | 1.80 | 0.00 | 0.00 |
| A111 07-15 → 07-27 | Yes | 2.31 | 1.76 | 0.55 | 0.03 |
| A111 07-27 → 08-20 | No | 4.09 | 4.09 | 0.00 | 0.00 |
| A111 08-20 → 09-01 | No | 1.15 | 1.15 | 0.00 | 0.00 |
| A111 09-01 → 09-13 | Yes | 1.74 | 1.26 | 0.48 | 0.02 |
| A111 09-13 → 09-25 | Yes | 1.24 | 0.77 | 0.47 | 0.05 |
| A111 09-25 → 10-07 | Yes | 1.36 | 0.86 | 0.50 | 0.08 |
| A111 10-07 → 10-19 | Yes | 4.07 | 0.75 | 3.32 | 0.05 |
| D104 09-13 → 09-25 | Yes | 0.93 | 0.81 | 0.12 | 0.01 |
| D104 10-07 → 10-19 | Yes | 2.13 | 1.65 | 0.48 | 0.02 |

- **The biggest change is A111 10-07 → 10-19, from 4.07 to 0.75 km².** The October patch was mostly coherence loss alone, so it has largely gone from the map.
- **The tallest pair on the timeline is now the 24-day pair, at 4.09 km².** Its gap is twice the others', and pairs without coherence never lost any area because they never had coherence-only area.
- **The held pair, D104 09-25 → 10-07, stays off the map.** It's still only in `pipeline/out`, under the old rule.

**What changed on the site, for your morning check:** the legend title no longer says PROVISIONAL. The drawer now says "PROVISIONAL radar products", because the products still are. The help panel's confidence wording describes the new rule, and it says the thresholds haven't been checked against field reports. The legend's "one signal" and "both signals" labels stay, because they're still accurate.

**Worth knowing:**
- **I pushed once with a failing test.** My command only checked the contract result before pushing 78ff330, which you asked me not to do. One test failed because its saved "low" map cell was coherence-only and now correctly reads "none". T-051 gives it a cell that is low under the final rule, and I didn't rewrite history.
- **Tests changed for the decision:** two legend tests now check that PROVISIONAL is gone, and the rule test now checks Mayon uses the owner's rule.
- **`channel_test.py` still uses the old rule for its "site rule" sensitivity column.** I didn't rerun or change it. Its verdict uses 3.0 dB brightness only and isn't affected.
- **The runbook names no report file for eruption results.** With no data yet, this didn't matter tonight. Results will need a place, such as a new section in this file.

**Downloaded tonight:** 0 bytes of NISAR data. No threshold values were written into `docs/`.

**Final evidence:** `pytest -q`: 360 passed, 6 skipped. Contract check: 0 errors on `site/data`. A second check at 16:28 UTC also found no new pass on either track.

# Docs run (2026-11-01)

**The docs now match what was decided and built, and the Nov 5–10 build can follow them once you decide items 1 and 2 below.** `night-1` is pushed and not merged into `main`, so the changes below aren't on the public site yet.

## What changed

| Commit | Task | What |
| --- | --- | --- |
| 8089a2c | T-067 | The 6 approved changes, including their code, test and data parts. Code 253 now reads "the radar product marked this spot as invalid", and the two study datasets are `analysis` sources |
| e25fae5 | T-068 | Final rule, 10 km reach limit, lifted blind cutoff and held pair recorded |
| 753cdcb | T-069 | Channel timeline added to all 9 docs. Brief is v0.4; the others are v0.2 |
| 4820b4b | T-070 | Out-of-scope lines, the rule against legal labels, and Panama named for F-10 |
| 35a9d77 | T-071 | Done work added to 07, ID errata in 07 §11, task-ID rule in `CLAUDE.md` |
| Latest on `night-1` | T-072 | `PROGRESS.md`, README, `docs/reviews/consistency-03.md`, this section |

History wasn't rewritten. The 21 mislabeled commits are in the errata table.

## New IDs

- **Feature and stories:** F-20, US-024 to US-026, plus new criteria on US-004, US-005, US-008 and US-012.
- **Requirements:** FR-060 (reach), FR-061 to FR-067 (timeline), FR-068 (no legal labels), FR-069 (site with no summit).
- **Design:** SCR-13, SCR-14, ADR-011, TBL-12 (`channel_areas.json`, a new file because it changes with every publish while the channel file doesn't), API-012.
- **Tasks:** T-052 to T-066 (done work that was mislabeled or missing), T-067 to T-072 (this run), T-073 to T-078 (the build).
- **Tests:** TC-061 to TC-076.

The unequal-gap marking wasn't built, so it's a new task (T-077), not a done one.

## Decisions for you

I didn't guess at these.

1. **Which channel lines do you confirm?** Nothing in F-20 can start until you do (T-073).
2. **What strip width goes in the site config?** T-074 needs it.
3. **Threshold values still in `docs/`:** your old plans `docs/NIGHT_PLAN.md` line 20 and `docs/NIGHT_PLAN_4.md` lines 26 and 57 contain them. I didn't edit your plans, and I left `NIGHT_PLAN_4.md` and `DOCS_PLAN_6.md` uncommitted. Should those lines be removed? `NIGHT_PLAN.md` is already in Git.
4. **FR-031 and US-010/AC-1** hold a coherence display mask for the ground-movement layer, a Could feature. It's the same number as the final coherence threshold, though it's a different setting. Keep it, or move it to the config?
5. **Panama:** the trial flagged 26% of the land, which isn't specific, and the boundary record's license detail still has to be read. T-036 also needs you to confirm that the final thresholds apply there.
6. **Reach in the browser:** FR-060 says the site config sets the distance, but `site/js/readout.js` has its own constant. It matches today. I recorded this and didn't change the code, because the plan didn't ask for it.
7. **Legend labels:** published pairs still say "(one signal)" and "(both signals)". That's still true, but less clear under the final rule. Changing them means editing `site/data/`, which this run couldn't do beyond change 6.
8. **Still open from before:** the channel distance (01 OQ3), the event-date rule (consistency-02 #8), and where eruption results get reported.

## A rule I had to interpret

Hard rule 3 says not to change `site/data/`, while section A requires the data part of change 6. I followed section A, and only the `used_for` value of two rows in `site/data/sources.json` changed. I took "the 24-day pair" and "gap isn't 12 days" literally, so any gap other than 12 days is dimmed.

## Evidence

- **Tests:** `pytest -q`: 360 passed, 6 skipped, exit code 0. **Contract check:** 0 errors, exit code 0. Both were run again right before the push.
- **IDs:** 0 dangling and 0 renumbered, by script. All 16 new acceptance criteria have a test, and all 10 new requirements have a task and a test.
- **Diagrams:** 14 of 14 Mermaid diagrams rendered in headless Chromium.
- **Not checked:** the new wording in a browser by eye, beyond the automated test. No NISAR or Earthdata searches or downloads were made, so the eruption passes' status is still from 16:28 UTC on Oct 31.

# Owner's decisions on the docs run (2026-11-01)

**Six of your seven decisions are done and pushed on `night-1`, not merged into `main`. T-073 hasn't started: it waits for your Google Earth check.**

| Decision | Task | Result |
| --- | --- | --- |
| Strip width | T-080 | `channel_strip_half_width_m` is 200 in `pipeline/sites/mayon.json`, the same as `STRIP_M` in the channel test. Nothing uses it until T-074 |
| Plan files | T-081 | All 5 are in `plans/`, with the same checksums as before the move. `NIGHT_PLAN_4.md` and `DOCS_PLAN_6.md` are now in Git for the first time |
| Ground-movement number | T-082 | Now `ground_movement.min_coherence` in the site config. FR-031 and US-010/AC-1 describe it in words |
| Panama | T-083 | Below |
| Reach distance | T-084 | `sites.json` now has `detection_reach_km`, built from `filters.max_distance_km`. `map.js` and `readout.js` read it, and the constant is gone |
| Legend labels | T-085 | 11 pairs republished. Every area and coherence flag is unchanged, the held pair is still off, and there are no post-eruption pairs. The help panel's color lines use the same words |

## Panama under the final rule

Mayon's rule and thresholds are read when the trial runs, with no tuning. Output is in `pipeline/out/` only (`panama-trial-final-rule.json`). No NISAR data was downloaded, because the crops were cached. The earlier `pipeline/reports/panama-trial.json` stays as it was, so the old rule's numbers remain on record.

| Pair | Land checked | Flagged share of land | Flagged area (final rule) | Low / high | Flagged area (old rule) |
| --- | --- | --- | --- | --- | --- |
| Quiet, 09-15 → 09-27 | 443.97 km² | **0.5%** | 2.40 km² | 2.31 / 0.09 | 4.72 km² |
| Earthquake, 09-27 → 10-09 | 443.97 km² | **1.7%** | 7.73 km² | 3.06 / 4.66 | 117.30 km² (26%) |

The earthquake pair now flags about 3 times the quiet pair, and the old 26% came almost entirely from coherence loss alone. Near the reported landslide cluster it flags 2.40 km² of 120.89 km² of land. This is still unchecked against the mapped landslides, and an earthquake can change the ground without a landslide.

## Panama boundary license: your decision

- **geoBoundaries' record** says CC BY 4.0, with the license detail "need to update". Its site asks for the name and a link in a product's credits.
- **The upstream source it points to** (Smithsonian Tropical Research Institute data portal on ArcGIS) says **CC BY-SA 4.0**, which is stricter. The record is marked deprecated, is titled "Panama Districts Boundaries - 2016", and credits Panama's National Geographic Institute "Tommy Guardia" (2019). geoBoundaries calls the same data 2012.
- **What it means:** treat the stricter terms as the real ones. Published borders made from this data would need credit and the same license. `pipeline/reports/panama_trial_land.geojson` still says CC BY 4.0, because it's a trial file I didn't change. This isn't legal advice.
- **Decision:** accept CC BY-SA for Panama's `towns` and `land` files, or look for another boundary source. T-036 waits for this.

## Evidence

`pytest -q`: 370 passed, 6 skipped, exit code 0. Contract check: 0 errors on `site/data`, exit code 0. IDs: 0 dangling, by script. No threshold values were found in `docs/` by script. All 14 Mermaid diagrams render. The new labels and the reach were checked by the automated browser tests, not by eye on a phone.

# Panama site files (2026-11-01)

**T-036 is done and the Panama borders are credited under CC BY-SA 4.0, on `night-1`, not merged into `main`.** Panama isn't on the map or in the site list: its status stays `draft` until it has a pair (T-037).

- **Credit:** `sources.json` has a new row, `pa_admin_boundaries`, and the Data sources panel shows it with geoBoundaries, its upstream sources, a link to geoboundaries.org and "License: CC BY-SA 4.0". A browser test checks the panel. This row is on the panel for every site, because the panel lists all context sources.
- **Marking:** `towns.geojson` and `land.geojson` under `site/data/sites/panama/` both carry a top-level `license` member. Docs 05 and 06 describe it, and the contract check accepts it.
- **Site config:** `pipeline/sites/panama.json` has the same rule and thresholds as Mayon, and a test keeps them equal. It has no summit, reach or channels.
- **Districts:** Las Minas, Los Pozos and Mariato. The land matches the trial's land almost exactly.

**Things to know:**

- **One code change:** `context.py` had the Philippine source ID hardcoded, so a boundary file can now name its own source and license. The next site won't need this, but T-036's "no code changes" wasn't strictly met. TC-035 should be read with that in mind when T-037 runs it.
- **Map credit (T-087, not built):** `map.js` always shows the Philippine boundary credit, which would be wrong on Panama. T-037 now depends on it.
- **Public reachability:** the two Panama files will be reachable by direct URL once `night-1` is merged, even though the site isn't listed. They carry their license, so that's fine under the terms you accepted.
- **Still true:** the upstream record is marked deprecated, and the Panama result hasn't been checked against mapped landslides.

**Evidence:** `pytest -q`: 375 passed, 6 skipped, exit code 0. Contract check: 0 errors, exit code 0.

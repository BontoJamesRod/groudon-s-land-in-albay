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

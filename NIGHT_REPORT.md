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

**Final evidence:** `pytest -q`: 187 passed. Contract check: 0 errors on `site/data`, 0 on `pipeline/out`. **Downloaded tonight: 0.26 GB** of 20 GB (night 1: 3.34 GB).

## Read this first

1. **The method finds a signal on the named gullies, using brightness.** All three July pairs flag more than every quiet pair on the same track, in each of the three flanks PHIVOLCS named. Mi-isi on track 111 is 0.061 km² against at most 0.007. This is the best evidence so far, but it's small, coarse, and uses a rule I changed after a first misleading result. See `pipeline/reports/threshold-study-night-1.md`.
2. **Don't deploy the map as real detection yet.** All 9 published pairs show 3–39 km² of "new material" at PROVISIONAL values, mostly background change. The layer is labelled PROVISIONAL.
3. **CI has never run.** Every workflow was checked by reading only, because nothing may be pushed.

## Tasks

| # | Task | Status | Commit | Evidence |
| --- | --- | --- | --- | --- |
| 0 | Finish night 1 | Done | 61b6904, 0f26788, 50bc6d5, 5a17008, b72ca05 | T-016 and T-022 to T-025 finished. T-007 still hasn't run on GitHub (below) |
| 1 | Independent review | Done, 2 passes; M3 blocked on your decision | 219c6cd, dc94da5 | Findings below |
| 2 | T-026 readout | Done | d10e008, dc94da5 | TC-008, 009, 012 driven in headless Edge. TC-010: off-grid point gives "outside radar coverage". TC-011 not driven |
| 3 | T-027 search | Done | e3a62a4, dc94da5 | TC-005, 006, 007 driven |
| 4 | T-029 compare | Done; drag test blocked | 27740a5, dc94da5 | TC-018 driven by keyboard; clip follows the divider. **Dragging by finger or mouse not tested.** TC-019's path was read, not driven |
| 5 | T-030 help, `strings.js`, wording test | Done | b20b892, dc94da5 | TC-028 driven. `test_wording.py` covers TC-030; a word list can still miss things, so read the text yourself |
| 6 | T-031 data sources | Done | b20b892 | TC-031, TC-032 driven. ASF links not opened (06 Open Question 3) |
| 7 | T-032 site picker | Done, one site | b20b892, dc94da5 | Picker opens and closes. Failure on switching untested until a second site exists |
| 8 | T-033 404 and README | Done | 4c98f0c | Script commands tried. 404 page not opened in a browser |
| 9 | T-034 phone and color-blind | Done in emulation; real phone blocked | 65741e3 | 360 px iframe in Edge: no horizontal scroll, no tap target under 44 px, disclaimer stays on screen. Palette validator: CVD and normal-vision checks pass. **No real phone used.** The orange's contrast is low (2.19:1), which is allowed because each class has a text label |
| 10 | T-020 track 111 backlog | Done | 7116d6e | 9 of 9 pairs published, 2026-06-21 to 10-19. None left. `site/data` is 74 MB |
| 11 | T-035 panel, `validation.py`, draft | Done; publishing blocked on your review | 91fd0a2, 75729dd | TC-041 driven. **TC-040 not driven**, because no published record exists. Draft is refused by `--publish` and isn't in `site/data` |
| 12a | Channel lines (T-010) prep | Done, not built | a52f480 | `pipeline/reports/channel-candidates.md` |
| 12b | Second site (T-036) prep | Done, none chosen | 22fc3bd, b686bf4 | `pipeline/reports/second-site-candidates.md` |

Three tasks share a commit (T-030 to T-032), since their code is in the same files.

## Blocked, with reasons

These parts of the tasks above are not done, and I can't finish them tonight.

| Task | What is blocked | Reason | What unblocks it |
| --- | --- | --- | --- |
| 1, review finding M3 | The 24-day pair is still compared with 12-day baselines | Owner decision: FR-022 doesn't cover unequal gaps, and the docs are locked | Your answer to decision 2 below |
| 9, T-034 | Check on a real phone | No phone is available in this session; 360 px and tap targets were only emulated in Edge | Your phone check, to-do item 2 |
| 4, T-029 | Dragging the divider by finger or mouse | Headless Edge can't send a real pointer drag here; only the keyboard path was driven | The same phone check |
| 11, T-035 | Publishing the July validation, and TC-040 on a published record | The plan requires your review of the draft | Your answer to decision 3 below |
| Night 1, T-006 and T-007 | Running CI and the fake-secret test on GitHub | Hard rule 1 forbids pushing, and running the gitleaks binary locally was denied by the session's safety check. `pytest` and the contract check pass on the last commit locally only | To-do item 1 |

Not blocked, but not done because the plan didn't ask for it: boundary data for the second-site candidates wasn't checked, and it's listed as a check to do before choosing in `pipeline/reports/second-site-candidates.md`.

## Track 111 backlog (PROVISIONAL values)

| Pair | Coherence | High km² | Low km² | Total km² |
| --- | --- | --- | --- | --- |
| 06-21 → 07-03 | No | 0.00 | 7.39 | 7.39 |
| 07-03 → 07-15 (spans the event) | No | 0.00 | 5.20 | 5.20 |
| 07-15 → 07-27 | Yes | 0.12 | 6.27 | 6.39 |
| **07-27 → 08-20 (24 days)** | Yes | 0.45 | 38.47 | **38.92** |
| 08-20 → 09-01 | Yes | 0.06 | 3.18 | 3.24 |
| 09-01 → 09-13 | Yes | 0.08 | 5.72 | 5.80 |
| 09-13 → 09-25 | Yes | 0.56 | 4.39 | 4.95 |
| 09-25 → 10-07 | Yes | 0.57 | 4.17 | 4.74 |
| 10-07 → 10-19 | Yes | 0.38 | 8.22 | 8.60 |

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
| Major | The 24-day pair is compared with 12-day baselines | **Not changed: your decision, question 2 below.** Help text now says gaps can be longer |
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
- The fixes in commit dc94da5 and 75729dd weren't reviewed a third time. I re-ran the tests and the Edge checks on them.

## Decision reports, in short

**Channel lines (T-010):** OSM has 714 waterway segments but only 58 are named, and name matching finds just **2 channels: Bulawan and Basud**. Basud-Lidong may be Basud. The other 12 listed channels, including Mi-isi and Bonga, are missing. OSM alone can't supply them by name; matching unnamed lines by hand is possible, but it's manual work. OSM's ODbL license needs reading first.

**Second site (T-036):** three candidates, none processed yet.

| Candidate | Event | Best pair | Main risk |
| --- | --- | --- | --- |
| Azuero Peninsula, Panama | Landslides from the Mw 7.7 earthquake, 2026-10-09 | Track 4, 09-30 → 10-12 (12 days) | The earthquake may lower coherence everywhere; partial frames |
| Fuego, Guatemala | Pyroclastic flows, 2026-08-03 | Track 134, 07-17 → 08-10 (24 days) | Long gap; constant activity |
| Nyamulagira, DR Congo | Lava flow, active 2026-08-09 | Track 14, 07-21 → 08-14 (24 days) | Flow's start date unknown; little to validate against |

Panama and Fuego are on the same continent, and Nyamulagira is the only one in Africa.

## Your to-do list

**Do first**

1. Push `night-1` to a test branch and watch CI run, because no workflow has ever run. Add a fake secret on a throwaway branch to confirm the scan fails (T-007), and run "Scan history for secrets" by hand.
2. Open the site on a real phone: check the map centre, drag the compare divider, tap the map.
3. Read `pipeline/reports/threshold-study-night-1.md`, including the night 2 section, and decide the thresholds. They must be set before any eruption data is opened; then lift `BLIND_CUTOFF` in `search.py`.

**Your decisions**

1. **Event date:** GMA, quoting PHIVOLCS, reports the current on the morning of Monday **July 13**. `docs/05`, the plan and `events.json` say July 14. Both fall in the same pairs, so no marker moves. Which should the app say?
2. **24-day pairs:** 07-27 → 08-20 shows 38.92 km², which a visitor could read as a real event. Refuse to use coherence when the two gaps differ, warn in the label, or leave it? FR-022 doesn't cover this. Fuego and Nyamulagira would have the same problem.
3. **July validation draft:** review `pipeline/context/validation_sheets/mayon_A111F008_20260703_20260715.json`. Is a flank wedge good enough to say "yes", or should it wait for channel lines? Flank directions came from search summaries, so check them against a bulletin.
4. **Channel source**, **second site**, and the remaining questions in `docs/PROGRESS.md`.

**Worth checking in the docs (I didn't edit them)**

- 01 §11, the help text and 04 assume 12-day pairs; real gaps reach 24 days.
- 01 FR-011: "a slope the radar can't see" doesn't match the GCOV mask, which doesn't flag layover or shadow.
- 08 TC-024 expects 3 granules; a pair with coherence uses 4.
- 06 says a real pair has 5 layers; pairs without coherence have 4.
- 04 and 07 say CI runs on pushes to `main`; the plan asked for every push and pull request.
- The plan points to `pipeline/legacy/`, the notebook and `docs/notes/`, which aren't in the repo.

**Also corrects night 1 above:** the 360 px, TC-013 and TC-015 checks listed as not done were done tonight in emulation. The July date concern is now backed by GMA's report.


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

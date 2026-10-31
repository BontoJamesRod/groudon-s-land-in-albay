# Proposed doc changes

| Change | Status |
| --- | --- |
| 1 | Applied on 2026-11-01 by owner decision (8089a2c) |
| 2 | Applied on 2026-11-01 by owner decision (8089a2c) |
| 3 | Applied on 2026-11-01 by owner decision (8089a2c) |
| 4 | Applied on 2026-11-01 by owner decision (8089a2c) |
| 5 | Applied on 2026-11-01 by owner decision (8089a2c) |
| 6 | Applied on 2026-11-01 by owner decision (8089a2c) |

Written for the project owner. Each one is a place where the docs and the built app disagree, or where a doc can't be followed as written. Threshold values are left out on purpose, as they don't belong in `docs/`.

## 1. Unequal gaps between passes

The app already follows this rule, but no doc states it. It needs your decision (night 2, decision 2), so apply this only if you keep the rule.

**`01-prd.md`, FR-022.** Replace:

> The pipeline shall compute coherence loss as the coherence of the previous pair on the same track minus the coherence of the current pair.

With:

> The pipeline shall compute coherence loss as the coherence of the previous pair on the same track minus the coherence of the current pair, only when both pairs span the same number of days. Otherwise it shall treat the pair as having no coherence data (FR-030).

**`01-prd.md`, FR-030.** Replace:

> The pipeline shall still process a pair when its GUNW product is unavailable, classing every detection as low confidence and recording that no coherence data was used.

With:

> The pipeline shall still process a pair when its GUNW product is unavailable, or when FR-022 excludes its baseline, classing every detection as low confidence and recording that no coherence data was used.

**`01-prd.md`, assumptions (line 479).** Replace:

> Pairs are consecutive passes on the same track, 12 days apart, because coherence comes from the mission's GUNW products for those dates.

With:

> Pairs are consecutive passes on the same track, usually 12 days apart. A missed pass makes the gap longer, as on track 111 from 2026-07-27 to 2026-08-20 (24 days).

**Why:** comparing a 24-day pair with a 12-day pair flagged 38.92 km². With the rule it flags 14.51 km².

## 2. FR-011 mask wording

**`01-prd.md`, FR-011.** Replace:

> The system shall show "No radar data here" with one of three reasons (outside radar coverage, sea, slope the radar can't see) when the tapped point has no valid value.

With:

> The system shall show "No radar data here" with one of three reasons (outside radar coverage, sea, flagged invalid by the product) when the tapped point has no valid value.

**The screen text would change too:** `noDataReasons[253]` in `site/js/strings.js`, and TC-011's expected result in `08-test-plan.md`, need matching wording. Suggested visitor wording: "the radar product marked this spot as invalid".

**Why:** code 253 comes from the product's own `mask` dataset. It doesn't come from a layover or shadow check, so "a slope the radar can't see" claims more than the data says. The afternoon study found only about 0.009 km² of possible shadow in the danger zone, at an assumed beam angle.

## 3. TC-024 granule count

**`08-test-plan.md`, TC-024, expected result.** Replace:

> Files written to `pipeline/out/`; summary shows status "ready", the 3 granule IDs and areas in km²

With:

> Files written to `pipeline/out/`; summary shows status "ready", the granule IDs used (4 with coherence: 2 GCOV and 2 GUNW; 2 without) and areas in km²

**Why:** coherence loss compares two GUNW products, so a pair with coherence uses four granules.

## 4. Layer count in the API spec

**`06-api-spec.md`, line 475.** Replace:

> `200 OK` (one pass and one layer shown in full; the real file has 2 passes and 5 layers)

With:

> `200 OK` (one pass and one layer shown in full; the real file has 2 passes and 5 layers, or 4 when the pair has no coherence data, because `coherence_loss` is then left out)

**Why:** 4 of the 9 published pairs have no coherence data, so they have 4 layers.

## 5. CI triggers

**`04-technical-design.md`, line 168.** Replace:

> On every push to `main`, a GitHub Actions workflow runs `pytest` (pipeline unit tests, no downloads), the data-contract check on `site/data/`, and a secret scan. If all pass, it deploys the `site/` folder to GitHub Pages (verify the official Pages deploy actions). Any failure stops the deploy.

With:

> On every push to any branch and on every pull request, a GitHub Actions workflow runs the secret scan, `pytest` (no downloads), the browser tests in Chromium, and the data-contract check on `site/data/`. On a push to `main`, the same checks run and, if all pass, the `site/` folder deploys to GitHub Pages. Any failure stops the deploy. A separate workflow scans the whole Git history weekly and on demand.

**Why:** `NIGHT_PLAN.md` asked for checks on every push and pull request, and the browser tests were added on day 3. `08-test-plan.md` §2, which lists end-to-end tests as manual, could change the same way, and that would also answer its Open Question 2.

## 6. `context_use` values

**`05-database-design.md`, line 483.** Replace:

> | `context_use` | `basemap`, `boundaries`, `coastline`, `channels`, `events`, `validation` | `sources.used_for` |

With:

> | `context_use` | `basemap`, `boundaries`, `coastline`, `channels`, `events`, `validation`, `analysis` | `sources.used_for` |

**Then:** add `analysis` to `CONTEXT_USE` in `pipeline/mrw/contract_check.py`, and change `esa_worldcover_2021` and `copernicus_dem_glo30` to it in `pipeline/context/sources.json` and `site/data/sources.json`.

**Why:** ESA WorldCover and the Copernicus elevation model are used only in the false-alarm study. They're listed as `validation` today, the closest allowed value, which isn't accurate.

## Order

Change 2 needs code and test changes along with the doc. Change 6 needs code and data changes. Changes 1, 3, 4 and 5 only change the docs, because the app already behaves that way.

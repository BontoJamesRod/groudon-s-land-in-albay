# Progress

**Project:** Mayon Radar Watch
**Current step:** The Field map design, the Relief or Satellite switcher and the Channel timeline are live on `main` (34d1c19), with 4 confirmed channels. The eruption pairs (T-038) are waiting for their passes to reach ASF.
**Last updated:** 2026-11-03

Status values: `Not started` · `In progress` · `Draft ready` · `Approved` · `Skipped` · `Reopened`

## Documents

| Order | Document | Status | Version | Approved on | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | `00-project-brief.md` | Draft ready | 0.4 | — | Summary now about channels; F-20 added |
| 2 | `01-prd.md` | Draft ready | 0.2 | — | FR-060 to FR-069, US-024 to US-026 |
| 3 | `02-mvp-scope.md` | Draft ready | 0.2 | — | F-20 in the MVP |
| 4 | `03-user-flows.md` | Draft ready | 0.2 | — | SCR-13, SCR-14, Flow 9 |
| 5 | `04-technical-design.md` | Draft ready | 0.2 | — | Final rule in ADR-006; ADR-011 |
| 6 | `05-database-design.md` | Draft ready | 0.2 | — | TBL-12 |
| 7 | `06-api-spec.md` | Draft ready | 0.2 | — | API-012 |
| 8 | `reviews/consistency-01.md` | Draft ready | — | — | Checkpoint: 7 issues, 0 structural |
| 9 | `07-roadmap.md` | Draft ready | 0.2 | — | 119 tasks; ID errata in §11 |
| 10 | `08-test-plan.md` | Draft ready | 0.2 | — | 96 test cases |
| 11 | `reviews/consistency-02.md` | Draft ready | — | — | Checkpoint: 9 issues, 0 structural |
| 12 | `reviews/consistency-03.md` | Draft ready | — | — | Checkpoint after the 2026-11-01 update |

## Where Things Stand

| Item | State on 2026-11-03 |
| --- | --- |
| Gate 1 (channels) | Decided: build only the Channel timeline (F-20), on top of F-19. No quarry hint or rain labels (00 §6) |
| Gate 2 (rule and thresholds) | Decided before any post-eruption data was opened. The final rule is live on the public site on 11 pairs |
| Products | NISAR products are still PROVISIONAL |
| Eruption passes | Not on ASF at the last check (2026-11-02, about 17:00 UTC, `eruption_run.py check-all`, names only). Newest pass: track 39 on Oct 14, track 104 on Oct 19, track 111 on Oct 19, all PROVISIONAL. Nothing downloaded or published |
| Second site | Panama, two pairs, same final rule with no per-site tuning, live on the public site with borders under CC BY-SA 4.0 and a check against the University of Panama map (T-037, T-088) |
| Held pair | D104 2026-09-25 → 2026-10-07 stays off the map |
| Channels | The owner checked the lines in Google Earth Pro on 2026-11-01: Basud, Lidong, Mi-isi and Padang are confirmed; 5 others must never be shown; Matanag was then given as not confirmed, and stays off (`pipeline/reports/owner-checks.md`) |
| Design | Field map and the Relief or Satellite switcher are live on both sites (`main` at 34d1c19, T-107 to T-118). Relief is the default and is stored in the site. Satellite loads live from EOX (EOxCloudless 2024), low detail first, with a loading count. Esri is gone. Checked in test browsers, not yet on a real phone |
| Next | T-038 as soon as the eruption passes are on ASF, which also adds their channel rows |

## After Launch

| Item | Document | Status | Version | Date | Notes |
| --- | --- | --- | --- | --- | --- |
| — | `CHANGELOG.md` | Not started | — | — | First entry at T-042 |

Add one row per enhancement proposal (`EP-001` …) when it starts.

## Key Decisions

| Date | Decision | Recorded in |
| --- | --- | --- |
| 2026-10-31 | The project follows the Space Apps "Dancing with the SARs" requirements | 00 §12 |
| 2026-10-31 | One core question: where new material landed, and which channels and towns are near it | 00 §1 (v0.2) |
| 2026-10-31 | Past-years water comparison (F-15) removed; water-shortage users dropped | 00 §5, §13 (v0.2) |
| 2026-10-31 | All documents drafted in one pass at the owner's request, instead of one at a time with approval between | This file |
| 2026-11-01 | Gate 1: the Nov 5–10 build is the Channel timeline only (F-20) | 00 §5, 07 §3 |
| 2026-11-01 | Second site is Panama, for R7, using the same final rule. Two pairs, by owner decision | 00 §5, F-10 |
| 2026-11-01 | Channel strip width set in the site config, the same as the channel test | 01 FR-064, 07 T-080 |
| 2026-11-01 | Plan files moved from `docs/` to `plans/` | 07 T-081 |
| 2026-11-01 | Ground-movement mask moved to the site config; reach distance read from it | 07 T-082, T-084 |
| 2026-11-01 | Legend labels renamed to say which signals agree; 11 pairs republished | 07 T-085 |
| 2026-10-31 | Detections are limited by a reach distance from the summit set in the site config (live since Oct 31) | 01 FR-060, 04 ADR-006 |
| 2026-11-01 | Gate 2: final classification rule and thresholds locked before any post-eruption data was opened. Brightness change flags a pixel; coherence loss only raises it to high confidence. Values live in the site config | 01 FR-023, 04 ADR-006 |
| 2026-11-01 | Blind cutoff lifted for the Oct 31 passes only | 04 ADR-006, `CLAUDE.md` |
| 2026-11-01 | Pair D104 2026-09-25 → 2026-10-07 stays off the map by owner decision, because its baseline's coherence is unusually high | This file |
| 2026-11-01 | Channel lines confirmed by the owner in Google Earth Pro; only those are published. Change is counted within the reach distance, and what lies past it is drawn as not checked | `pipeline/reports/owner-checks.md`, 01 FR-065, FR-071 |
| 2026-11-02 | Design: Field map, with a minimum mark and darker edge for flagged change, areas also as basketball courts, and a wider Copernicus DEM under 300 MB with its size logged | 01 F-22, 04 ADR-012 |
| 2026-11-02 | Coverage view: only after the design is built, and only if that's done by Nov 8, with eruption work first. It may show pass dates (metadata only) past the cutoff, because the thresholds are final; the processing cutoff is unchanged | This file |
| 2026-11-02 | The histogram's channel outline stays desktop-only for now, to revisit with the design | This file |
| 2026-11-03 | Rule for holding a pair set before any post-eruption data: a large area alone is never a reason. A single track is published with a note | 04 ADR-014, 01 FR-085, FR-086 |
| 2026-11-03 | Satellite keeps loading live from EOX with the preview layer; no bulk download of imagery | `NIGHT_REPORT.md` |
| 2026-11-02 | Map switcher: Relief by default, or Satellite. Panama's relief approved (under 300 MB, size logged). Esri's terms need Esri software or a subscription, so Satellite uses EOxCloudless | 01 F-23, 04 ADR-013 |

## Open Questions Carried Forward

| # | Question | From | Blocks |
| --- | --- | --- | --- |
| 1 | Do the Space Apps and Legazpi local-event rules allow code written before 2026-11-14? | 00 OQ5 | All of Phase 1 in 07 |
| 2 | Closed on 2026-11-01: the owner accepted CC BY-SA 4.0 for the Panama borders. | 01 OQ5 | Nothing now |
| 3 | Closed on 2026-11-01: the owner confirmed Basud, Lidong, Mi-isi and Padang. | 01 OQ4 | Nothing now |
| 4 | Closed on 2026-11-01: strip width is in the site config. | 01 OQ8 | Nothing now |
| 5 | Answered for now, and the owner can change it: "in or near" means inside the channel's strip. | 01 OQ3 | Nothing now |
| 6 | Frontend approach and hosting: accept the Suggestions (plain JavaScript, GitHub Pages)? They're what was built. | 04 OQ1, OQ2 | Nothing now |
| 7 | How many hours per week can the builder spend? | 02 OQ1 | Dates in 07 |
| 8 | How do people near Mayon find out today what changed, and what goes wrong with that? | 00 OQ1, OQ2 | 00 §2 |
| 9 | Monthly budget? | 00 OQ6 | 04 §2 |

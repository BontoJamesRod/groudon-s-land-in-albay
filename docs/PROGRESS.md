# Progress

**Project:** Mayon Radar Watch
**Current step:** Build the Channel timeline, Nov 5–10 (07 T-073 to T-078). The owner confirms channel lines first (T-073).
**Last updated:** 2026-11-01

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
| 9 | `07-roadmap.md` | Draft ready | 0.2 | — | 78 tasks; ID errata in §11 |
| 10 | `08-test-plan.md` | Draft ready | 0.2 | — | 76 test cases |
| 11 | `reviews/consistency-02.md` | Draft ready | — | — | Checkpoint: 9 issues, 0 structural |
| 12 | `reviews/consistency-03.md` | Draft ready | — | — | Checkpoint after the 2026-11-01 update |

## Where Things Stand

| Item | State on 2026-11-01 |
| --- | --- |
| Gate 1 (channels) | Decided: build only the Channel timeline (F-20), on top of F-19. No quarry hint or rain labels (00 §6) |
| Gate 2 (rule and thresholds) | Decided before any post-eruption data was opened. The final rule is live on the public site on 11 pairs |
| Products | NISAR products are still PROVISIONAL |
| Eruption passes | Not on ASF at the last check (2026-10-31, 16:28 UTC, tracks 104 and 111). Nothing downloaded or published. This docs run made no searches |
| Second site | Panama, one pair; not published yet (T-036, T-037) |
| Held pair | D104 2026-09-25 → 2026-10-07 stays off the map |
| Next | T-073 (owner confirms channel lines), then T-010, T-074 to T-078; T-038 as soon as the eruption passes are on ASF |

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
| 2026-11-01 | Second site is one Panama pair, for R7 | 00 §5, F-10 |
| 2026-10-31 | Detections are limited by a reach distance from the summit set in the site config (live since Oct 31) | 01 FR-060, 04 ADR-006 |
| 2026-11-01 | Gate 2: final classification rule and thresholds locked before any post-eruption data was opened. Brightness change flags a pixel; coherence loss only raises it to high confidence. Values live in the site config | 01 FR-023, 04 ADR-006 |
| 2026-11-01 | Blind cutoff lifted for the Oct 31 passes only | 04 ADR-006, `CLAUDE.md` |
| 2026-11-01 | Pair D104 2026-09-25 → 2026-10-07 stays off the map by owner decision, because its baseline's coherence is unusually high | This file |

## Open Questions Carried Forward

| # | Question | From | Blocks |
| --- | --- | --- | --- |
| 1 | Do the Space Apps and Legazpi local-event rules allow code written before 2026-11-14? | 00 OQ5 | All of Phase 1 in 07 |
| 2 | Is the Panama boundary license fine for public use? | 01 OQ5 | T-036 |
| 3 | Which channel lines does the owner confirm? | 01 OQ4 | T-073, T-010, F-20 |
| 4 | What strip width goes in the site config? | 01 OQ8 | T-074 |
| 5 | What distance from a channel counts as "in or near" it? | 01 OQ3 | US-023/AC-2, TC-045, TC-046 |
| 6 | Frontend approach and hosting: accept the Suggestions (plain JavaScript, GitHub Pages)? They're what was built. | 04 OQ1, OQ2 | Nothing now |
| 7 | How many hours per week can the builder spend? | 02 OQ1 | Dates in 07 |
| 8 | How do people near Mayon find out today what changed, and what goes wrong with that? | 00 OQ1, OQ2 | 00 §2 |
| 9 | Monthly budget? | 00 OQ6 | 04 §2 |

# Progress

**Project:** Mayon Radar Watch
**Current step:** Review all drafts. Start by fixing consistency-02 issues 1 and 2, then approve 00.
**Last updated:** 2026-10-31

Status values: `Not started` · `In progress` · `Draft ready` · `Approved` · `Skipped` · `Reopened`

## Documents

| Order | Document | Status | Version | Approved on | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | `00-project-brief.md` | Draft ready | 0.3 | — | Consistency-02 issues 1 and 7 |
| 2 | `01-prd.md` | Draft ready | 0.1 | — | Consistency-02 issues 2, 3, 8, 9 |
| 3 | `02-mvp-scope.md` | Draft ready | 0.1 | — | All Must features included |
| 4 | `03-user-flows.md` | Draft ready | 0.1 | — | 11 Suggestion messages to accept or reject |
| 5 | `04-technical-design.md` | Draft ready | 0.1 | — | Stack gate open: frontend approach and hosting |
| 6 | `05-database-design.md` | Draft ready | 0.1 | — | No database engine: static files (ADR-003) |
| 7 | `06-api-spec.md` | Draft ready | 0.1 | — | No backend: static-file contract (ADR-001) |
| 8 | `reviews/consistency-01.md` | Draft ready | — | — | Checkpoint: 7 issues, 0 structural |
| 9 | `07-roadmap.md` | Draft ready | 0.1 | — | 49 tasks; no dates until weekly hours are known |
| 10 | `08-test-plan.md` | Draft ready | 0.1 | — | 60 test cases; 41 / 41 MVP acceptance criteria covered |
| 11 | `reviews/consistency-02.md` | Draft ready | — | — | Checkpoint: 9 issues, 0 structural |

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

## Open Questions Carried Forward

| # | Question | From | Blocks |
| --- | --- | --- | --- |
| 1 | Do the Space Apps and Legazpi local-event rules allow code written before 2026-11-14? | 00 OQ5 | All of Phase 1 in 07 |
| 2 | Which second site, and which boundary data for it? | 00 OQ4, 01 OQ5 | F-10, T-036, consistency-02 #2, #6 |
| 3 | What brightness-change and coherence-loss thresholds count as new material? | 00 OQ7, 01 OQ2 | FR-023, T-016 (before 2026-11-03) |
| 4 | Where do the channel lines come from? | 01 OQ4 | F-19, T-010 |
| 5 | What distance from a channel counts as "in or near" it? | 01 OQ3 | US-023/AC-2, TC-045, TC-046 |
| 6 | Frontend approach and hosting: accept the Suggestions (plain JavaScript, GitHub Pages)? | 04 OQ1, OQ2 | T-004, T-005 |
| 7 | How many hours per week can the builder spend? | 02 OQ1 | Dates in 07 |
| 8 | How do people near Mayon find out today what changed, and what goes wrong with that? | 00 OQ1, OQ2 | 00 §2 |
| 9 | Monthly budget? | 00 OQ6 | 04 §2 |

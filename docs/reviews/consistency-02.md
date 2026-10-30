# Consistency Report 02: Mayon Radar Watch

| Date | Documents checked | Verdict |
| --- | --- | --- |
| 2026-10-31 | 00 v0.3, 01 v0.1, 02 v0.1, 03 v0.1, 04 v0.1, 05 v0.1, 06 v0.1, 07 v0.1, 08 v0.1 (all Draft) | Fix 2 issues first |

Method: the same script as report 01, extended to the roadmap and test plan. It checked task sizes, task dependencies against the build order, task coverage of every MVP story, screen, table and endpoint, test coverage of every MVP acceptance criterion and NFR, and the traceability matrix, and rendered all 13 Mermaid diagrams again (13 rendered, 0 failed). It found no ID, coverage or format problems. The documents were then read side by side; issues 1–7 below are carried over from report 01 because no document has been reopened yet, and issues 8–9 are new. The same author wrote the documents and this check, so a second reviewer is still worthwhile.

## 1. Issues

| # | Severity | Type | Location | Problem | Suggested fix |
| --- | --- | --- | --- | --- | --- |
| 1 | Major | Contradiction | 00 §5 F-05 vs 01 FR-022 and 04 ADR-006 | F-05 says the two signals "agree between two passes"; coherence loss needs the previous pair, so three passes. (From report 01.) | REOPEN 00: change F-05's description as proposed in 01 §13. |
| 2 | Major | Gap | 01 US-004/AC-1, FR-010; 05 §10; 08 TC-008 | The readout requires distance to the summit; behavior for a site without a summit is only a Suggestion. (From report 01.) | Choose the second site; if it has no summit, REOPEN 01 to add an acceptance criterion, then add a test to 08. |
| 3 | Major | Gap | 01 US-023/AC-2, FR-057; 06 API-011; 08 TC-045, TC-046 | The channel distance is `[TBD]`, so TC-045 and TC-046 can't be run as written. (From report 01.) | Decide the distance (01 Open Question 3) and REOPEN 01. |
| 4 | Major | Gap | 01 FR-023; 05 TBL-05; 07 T-016 | Threshold values don't exist yet. T-016 now produces them, so this closes when T-016 is done. (From report 01.) | Do T-016 before 2026-11-03; record the values in 01 and 05. |
| 5 | Major | Gap | 01 §8; 04 ADR-008; 05 TBL-03; 07 T-010 | The channel line source is `[TBD]`; T-010 can't start without it. (From report 01.) | Choose the source; update 04 ADR-008 and 05 §8. |
| 6 | Major | Gap | 01 F-10; 05 §8; 07 T-036, T-037 | The second site isn't chosen; T-036 starts with that decision. (From report 01.) | Choose it right after the thin slice (07 build-order step 32 at the latest). |
| 7 | Minor | Mismatch | 00 §5 F-02 vs 01 US-004/AC-1 | "Distance to the crater" and "new material nearby" in the brief; "distance to the summit" and the result at the tapped point in the PRD. (From report 01.) | REOPEN 00 to align the wording, or accept it. |
| 8 | Minor | Gap | 01 US-005/AC-3, FR-016; 05 TBL-07 `event_date` | It isn't stated whether an event on the same local date as a pass counts as inside that pair. A developer would have to guess. | REOPEN 01: state that an event counts when `before` local date < `event_date` ≤ `after` local date (or another rule you choose). |
| 9 | Minor | Gap | 01 US-004/AC-1, FR-010; 05 TBL-02 | The card must show a town name, but a tapped point may lie outside every town in `towns.geojson` (for example in the sea, or in a neighbouring province inside the site bounds). | REOPEN 01: add what the card shows then, e.g. "Outside the mapped towns". |

## 2. Coverage

| Check | Result |
| --- | --- |
| MVP stories with at least one screen | 17 / 17 |
| MVP requirements that store data with a table | 41 / 41 (8 of the 49 MVP requirements store or read no data: FR-036, FR-037, FR-038, FR-045, FR-046, FR-047, FR-049, FR-050) |
| MVP stories needing server data with an endpoint | 12 / 12 (US-009 and US-015 reach ASF through the pipeline; US-012 is fixed text; US-016 is the app's own files; US-018 is layout) |
| MVP stories with at least one task | 17 / 17 (also every MVP screen 10 / 10, table 11 / 11 and endpoint 11 / 11) |
| MVP acceptance criteria with at least one test | 41 / 41 (60 test cases: 49 functional, 11 non-functional; NFR-006 has a stated reason instead) |

## 3. Unresolved Items

| Document | Section | Item |
| --- | --- | --- |
| 00-project-brief.md | §2 | Current workaround and cost of the problem `[TBD]` |
| 00-project-brief.md | §4, §6 | Goals G-01 to G-03 and the out-of-scope list are still `Suggestion:` |
| 00-project-brief.md | §7, §11 | Budget; event rule on pre-built code; team and presenter names |
| 01-prd.md | §3, §7, §10, §12 | Persona details; NFR targets for NFR-001, NFR-003, NFR-005, NFR-006, NFR-009; 4 `Suggestion:` ideas; 7 open questions |
| 02-mvp-scope.md | §2, §10 | Weekly hours; who the 10 testers are |
| 03-user-flows.md | §1, §4, §5 | Layout approach and 11 `Suggestion:` messages not covered by acceptance criteria |
| 04-technical-design.md | §2 | Stack decision gate: frontend approach and hosting still `Suggestion:` |
| 04-technical-design.md | §6 and elsewhere | 29 `(verify)` items |
| 05-database-design.md | §8, §11 | Mayon zoom levels; ASF Vertex link format (verify) |
| 06-api-spec.md | §1, §2 | Base URL; network timeout |
| 07-roadmap.md | §2, §8 | No dates until a start date and weekly hours are given |
| 08-test-plan.md | §4, §6 | NFR targets for TC-050, TC-051, TC-054, TC-060; whether an iPhone is available |

## 4. Verdict

Fix 2 issues first: #1 (one sentence in the brief) and #2 (needs the second-site decision). Reopen in this order: 00-project-brief.md (issues 1 and 7), then 01-prd.md (issues 2, 3, 8 and 9). Issues 4–6 are decisions that the roadmap already schedules (T-016, T-010, T-036). Once those two documents are revised, the set is ready for approval one document at a time.

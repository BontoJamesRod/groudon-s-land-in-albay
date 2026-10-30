# Consistency Report 01: Mayon Radar Watch

| Date | Documents checked | Verdict |
| --- | --- | --- |
| 2026-10-31 | 00 v0.3, 01 v0.1, 02 v0.1, 03 v0.1, 04 v0.1, 05 v0.1, 06 v0.1 (all Draft) | Fix 2 issues first |

Method: a script cross-checked every ID definition and reference, duplicates and gaps, story and requirement coverage, the ERD against the data dictionary, every JSON field in 06 against the 05 columns, and rendered all 13 Mermaid diagrams (13 rendered, 0 failed). The documents were then read side by side for contradictions and invented details. Problems found and fixed before this report: F-15 restored to the brief's feature table as `Removed` (brief v0.3); missing error and fallback messages added to 03 so that 06 no longer refers to undefined behavior. The same author wrote the documents and this check, so a second reviewer is still worthwhile.

## 1. Issues

| # | Severity | Type | Location | Problem | Suggested fix |
| --- | --- | --- | --- | --- | --- |
| 1 | Major | Contradiction | 00 §5 F-05 vs 01 FR-022 and 04 ADR-006 | F-05 says brightness change and coherence loss "agree between two passes", but FR-022 defines coherence loss against the previous pair, which needs three passes. | REOPEN 00: change F-05's description to the wording proposed in 01 §13. |
| 2 | Major | Gap | 01 US-004/AC-1, FR-010; 05 §10 | The readout must show "the distance to the summit", but the second site may have no summit. 05 §10 has only a Suggestion for that case, so a developer would have to guess. | Choose the second site first. If it has no summit, REOPEN 01 to add an acceptance criterion for sites without one. |
| 3 | Major | Gap | 01 US-023/AC-2, FR-057; 06 API-011 | "Channel distance" is `[TBD]`; 06 uses 500 m only as an illustration. | Decide the distance (01 Open Question 3) and REOPEN 01 to put the number in US-023/AC-2. |
| 4 | Major | Gap | 01 FR-023; 05 TBL-05 `brightness_threshold_db`, `coherence_loss_threshold` | No threshold values exist, so classification can't be built as specified. | Set them from quiet pairs before the eruption data arrives (brief Open Question 7); record them in 01 FR-023 and 05. |
| 5 | Major | Gap | 01 §8; 04 ADR-008; 05 TBL-03 `line_source_id`, §8 | The channel line source is `[TBD]`. | Choose a source, then update 04 ADR-008 and the 05 seed data. |
| 6 | Major | Gap | 01 F-10, §8; 02 §6 criterion 3; 05 §8 | The second site and its boundary data aren't chosen, and R7 depends on them. | Choose the site (brief Open Question 4), then update 01 §8 and the 05 seed data. |
| 7 | Minor | Mismatch | 00 §5 F-02 vs 01 US-004/AC-1 | The brief says "distance to the crater" and "new material nearby"; the PRD says "distance to the summit" and gives the result at the tapped point. | REOPEN 00 to use "summit" and "at that spot", or accept the difference. |

## 2. Coverage

| Check | Result |
| --- | --- |
| MVP stories with at least one screen | 17 / 17 |
| MVP requirements that store data with a table | 41 / 41 (8 of the 49 MVP requirements store or read no data: FR-036, FR-037, FR-038, FR-045, FR-046, FR-047, FR-049, FR-050) |
| MVP stories needing server data with an endpoint | 12 / 12 (US-009 and US-015 reach ASF through the pipeline; US-012 is fixed text; US-016 is the app's own files; US-018 is layout) |
| MVP stories with at least one task | Roadmap not written yet |
| MVP acceptance criteria with at least one test | Test plan not written yet |

## 3. Unresolved Items

| Document | Section | Item |
| --- | --- | --- |
| 00-project-brief.md | §2 | Current workaround and cost of the problem `[TBD]` (Open Questions 1, 2) |
| 00-project-brief.md | §4, §6 | Goals G-01 to G-03 and the out-of-scope list are still `Suggestion:` |
| 00-project-brief.md | §7, §11 | Budget `[TBD]`; event rule on pre-built code (Open Question 5); team and presenter names |
| 01-prd.md | §3 | Tech comfort and main device for three personas `[TBD]` |
| 01-prd.md | §7 | NFR-001, NFR-003, NFR-005, NFR-006, NFR-009 targets `[TBD]`, each with a `Suggestion:` |
| 01-prd.md | §10 | Four `Suggestion:` ideas (barangay level, "Use my location", share links, optical toggle) |
| 01-prd.md | §13 | Conflict with brief F-05 (issue 1) |
| 02-mvp-scope.md | §2, §10 | Weekly hours; who the 10 testers are |
| 03-user-flows.md | §1, §4, §5 | Layout approach and 11 `Suggestion:` messages not covered by acceptance criteria |
| 04-technical-design.md | §2 | Stack decision gate: frontend approach and hosting are still `Suggestion:` |
| 04-technical-design.md | §6, §13 | 29 `(verify)` items, incl. Esri tile terms, GitHub Pages limits, Colab limits |
| 05-database-design.md | §8, §11 | Mayon zoom levels; ASF Vertex link format (verify) |
| 06-api-spec.md | §1, §2 | Base URL; network timeout |

## 4. Verdict

Fix 2 issues first, starting with #1 (one sentence in the brief) and #2 (depends on choosing the second site). Reopen in this order: 00-project-brief.md (issues 1 and 7), then 01-prd.md (issues 2 and 3). Issues 4–6 are decisions, not writing errors; make them before building the matching roadmap tasks. Continuing to 07 and 08 as drafts is safe, because neither depends on those decisions.

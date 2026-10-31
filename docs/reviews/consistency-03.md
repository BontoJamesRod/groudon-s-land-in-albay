# Consistency Report 03: Mayon Radar Watch

| Date | Documents checked | Verdict |
| --- | --- | --- |
| 2026-11-01 | 00 v0.4, 01 v0.2, 02 v0.2, 03 v0.2, 04 v0.2, 05 v0.2, 06 v0.2, 07 v0.2, 08 v0.2 (all Draft) | No ID problems. Open decisions are listed in §5 |

Method: a script read every ID definition in the nine documents, looked for gaps and duplicates, and looked for references to IDs that don't exist, including acceptance criteria. It also checked that each new acceptance criterion has a test, and each new requirement has a task and a test. All Mermaid diagrams were rendered in headless Chromium with Mermaid 10.9.1. The same author wrote the changes and this check, so a second reviewer is still worthwhile.

## 1. New IDs

| ID | What | Referenced in |
| --- | --- | --- |
| F-20 | Channel timeline | 00 §5; 01 §5, §6, §8; 02 §3, §6; 04 §3; 05 §8; 07 §1, §3; 08 §1 |
| US-024 | See which channels changed most | 01; 02 §3, §5; 03 SCR-13, Flow 9; 06 API-012; 07 T-075; 08 §7 |
| US-025 | Read one channel's timeline | 01; 02 §3, §5; 03 SCR-14, Flow 9; 06 API-005, API-012; 07 T-076, T-077; 08 §7 |
| US-026 | Compute channel areas | 01; 02 §3, §5; 03 SCR-12; 07 T-073, T-074; 08 §7 |
| US-004/AC-4, US-004/AC-5 | Beyond the reach; site with no summit | 01; 03 SCR-02; 08 TC-061, TC-076 |
| US-005/AC-4 | Unequal gap on the pass timeline | 01; 03 SCR-01; 08 TC-071 |
| US-008/AC-4, US-008/AC-5 | Coherence alone adds no area; reach is drawn and stated | 01; 03 SCR-01; 08 TC-063, TC-062 |
| US-012/AC-4 | No legal labels | 01; 08 TC-075 |
| FR-060 | Reach limit | 01; 04 ADR-006, ADR-011; 05 TBL-01, TBL-06; 06 API-010; 07 T-057, T-074; 08 TC-061, TC-062, TC-072 |
| FR-061 | List and sorting | 01; 05 TBL-12; 06 API-012; 07 T-069, T-075; 08 TC-064 |
| FR-062 | Bars | 01; 05 TBL-05, TBL-12; 06 API-012; 07 T-076; 08 TC-067 |
| FR-063 | Strip on the map | 01; 05 TBL-03; 06 API-005; 07 T-076; 08 TC-068 |
| FR-064 | Pipeline computes strip areas | 01; 05 TBL-01, TBL-03, TBL-12; 07 T-074; 08 TC-072, TC-073 |
| FR-065 | Confirmed channels only | 01; 05 TBL-03; 06 API-005; 07 T-073, T-074; 08 TC-074 |
| FR-066 | Unequal-gap marking | 01; 05 TBL-05; 07 T-077; 08 TC-070, TC-071 |
| FR-067 | List and no-data states | 01; 05 TBL-12; 06 API-012; 07 T-075, T-076; 08 TC-065, TC-066, TC-069 |
| FR-068 | No legal labels | 01; 07 T-070, T-078; 08 TC-075 |
| FR-069 | Site with no summit | 01; 07 T-036, T-070; 08 TC-076 |
| SCR-13, SCR-14 | Channel list, channel view | 03; 07 T-075, T-076; 08 TC-064 to TC-070 |
| ADR-011 | Channel strips in the pipeline, width in config | 04; 07 T-074 |
| TBL-12 | `channel_areas` | 05; 07 T-074; 08 TC-072 |
| API-012 | `channel_areas.json` | 06; 07 T-074 to T-076; 08 TC-064, TC-066, TC-067, TC-069, TC-072 |
| T-050 to T-072 | Done work, including this run | 07 §3, §11 |
| T-073 to T-078 | Channel timeline tasks | 07 §2, §3, §4; 01 OQ8; 08 |
| TC-061 to TC-076 | New tests | 08 §3, §7; 07 task rows |

## 2. Changed IDs

| ID | Change | Referenced in |
| --- | --- | --- |
| F-05, FR-023, US-008/AC-3, ADR-006 | Final rule: brightness flags a pixel, coherence only raises confidence | 00, 01, 04; 08 TC-022 |
| FR-011, US-004/AC-2, TC-011 | New wording for code 253 (change 2) | 01, 03 SCR-02, 08; `strings.js`, e2e test |
| FR-022, FR-030 | Unequal gaps (change 1) | 01, 04 ADR-006 |
| TC-024, API-008 | Granule count and layer count (changes 3 and 4) | 08, 06 |
| `context_use` | New value `analysis` (change 6) | 05; `contract_check.py`, both `sources.json` files |
| API-005, TBL-01, TBL-03 | New fields for the strip and the confirmation | 05, 06 |
| API-007, API-008 | Threshold numbers in the examples replaced with a placeholder | 06 |
| F-10, T-036, T-037 | Name Panama | 00, 01, 02, 05, 07 |
| T-010, T-016, T-040 | New dependency; thresholds recorded in config; wider scope | 07 |
| SCR-01, SCR-02, SCR-12 | New elements and stories | 03 |

## 3. Checks

| Check | Result |
| --- | --- |
| Definitions: 20 F, 26 US, 69 FR, 14 SCR, 12 TBL, 12 API, 78 T, 11 ADR, 76 TC | No gaps and no duplicates |
| Dangling references (F, US, AC, FR, SCR, TBL, API, T, ADR, TC) | 0 |
| Renumbered IDs | 0. Old IDs keep their numbers and meaning; labels that were wrong are explained in 07 §11 |
| New acceptance criteria with a test | 16 / 16 |
| New requirements with a task and a test | 10 / 10 |
| Mermaid diagrams | 14 rendered, 0 failed (changed: 03 navigation map, Flow 3, Flow 9; 05 ERD) |

## 4. Threshold Values in `docs/`

No classification threshold value is in documents 00–08, PROGRESS or the reviews. Two API examples held numbers that had to go, and now show a placeholder. Three things remain, and none was written in this run:

- `NIGHT_PLAN.md` line 20 and `NIGHT_PLAN_4.md` lines 26 and 57 are the owner's old run plans, and they weren't edited. `NIGHT_PLAN_4.md` is left uncommitted.
- FR-031 and US-010/AC-1 hold a display mask for the ground-movement layer (F-06). It isn't a classification threshold.
- The Git history still holds the old API examples, because history isn't rewritten.

Update on 2026-11-01, after the owner's decisions: the plan files moved to `plans/`, and the ground-movement mask moved to the site config, so `docs/` no longer holds any of these values. Only the Git history does.

## 5. Open Items

| # | Severity | Location | Item |
| --- | --- | --- | --- |
| 1 | Major | 01 OQ4; 07 T-073 | The owner hasn't confirmed any channel line yet, so F-20 can't start |
| 2 | Closed | 01 OQ8; FR-064 | Strip width is in the site config (T-080) |
| 3 | Major | 01 OQ3; US-023/AC-2 | Channel distance is still `[TBD]` (consistency-02 #3) |
| 4 | Closed | 01 OQ5; T-036 | The owner accepted CC BY-SA 4.0 for the Panama borders (T-086). The upstream record is still marked deprecated |
| 5 | Closed | FR-060; `site/js/readout.js` | The browser reads the reach distance from `sites.json`, built from the site config (T-084) |
| 6 | Closed | API-008; `site/data/` | Legend labels renamed and the pairs republished (T-085) |
| 7 | Minor | 01 US-005/AC-3 | Whether an event on a pass's local date counts as inside the pair is still unstated (consistency-02 #8) |

Consistency-02 issues 1, 2, 4 and 6 are closed by this update, and issue 5 is closed apart from the confirmation in item 1.

## 6. Verdict

The IDs are consistent and the documents agree. The Nov 5–10 build can follow them once item 1 is done, which waits for the owner's Google Earth check.

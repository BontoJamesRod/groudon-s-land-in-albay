# MVP Scope: Mayon Radar Watch

| Version | Status | Last updated | Based on |
| --- | --- | --- | --- |
| 0.2 | Draft | 2026-11-01 | 00-project-brief.md v0.4 (Draft), 01-prd.md v0.2 (Draft) |

## 1. MVP Goal

**This MVP proves that:** NISAR radar, shown in a simple public web app, can show non-experts how Mayon's named channels change between passes, including after the Oct 30, 2026 eruption, and that the same engine works on a second site on another continent.

## 2. MVP Constraints

| Constraint | Value |
| --- | --- |
| Time available | From 2026-10-31 to the hackathon on 2026-11-14 to 2026-11-15 (fixed). Weekly hours: [TBD]. |
| First users | Space Apps judges (number [TBD]); then 10 Albay residents or LGU staff for the readability test (G-03; who: [TBD]) |
| Platform | Public static web app for phone and desktop browsers, English only |

## 3. In the MVP

| F-ID | Feature | US-IDs included | Why it's essential |
| --- | --- | --- | --- |
| F-01 | Interactive map | US-001, US-002 | The base every other feature sits on (R1) |
| F-02 | Place readout | US-003, US-004 | Turns the map into plain words for one spot (R1, R8) |
| F-03 | Pass timeline | US-005, US-006 | "Track" means change over time; shows the July 14 and Oct 30 events (R4) |
| F-04 | Before/after view | US-007 | Lets visitors see the change with their own eyes (R4, R5) |
| F-05 | New-material layer | US-008, US-009 | The core result, made from real NISAR data (R2, R3, R5, R6) |
| F-08 | "What am I looking at?" panel | US-012 | Makes radar understandable and keeps the app honest (R8) |
| F-09 | Data sources panel | US-013 | Judges must see NISAR products named and dated (R2, R3) |
| F-10 | Second showcase site (two Panama pairs) | US-014, US-015 | Required for "locations around the world" (R7) |
| F-11 | Public app and code | US-016 | Judges can't score what they can't open |
| F-12 | Validation check | US-017 | Proves the core result is true; supports the Validity criterion |
| F-13 | Mobile-friendly, color-blind-safe design | US-018 | Residents mainly use phones; cheaper to build in from the start |
| F-19 | Channels and towns | US-023 | The link from new material to the people downstream (R8) |
| F-20 | Channel timeline | US-024, US-025, US-026 | Shows how each channel changes from pass to pass; the owner's chosen feature for the Nov 5–10 build (R4, R8) |
| F-21 | Brightness histogram | US-027 | Answers "why did this spot count as changed?" for residents and judges |

## 4. Deferred

| ID | Item | Moved to | Reason |
| --- | --- | --- | --- |
| US-010 | F-06 Ground movement: see ground movement | v1.1 | Could priority; the Oct 8–20 test showed about ±1.35 cm noise, so it needs careful handling. First to add if time remains. |
| US-011 | F-07 Flood layer: see flooded areas | v1.1 | Could priority; needs a lowlands site and a typhoon pair |
| US-019 | F-14 Point time series: see a point's history | v1.1 | Could priority; needs many published pairs first |
| US-020 | F-16 Filipino and Bikol: use the app in Filipino or Bikol | v1.2 | Could priority; the submission must be in English |
| US-021 | F-17 Automatic updates: update automatically | v1.2 | Could priority; manual runs are enough for the MVP |
| US-022 | F-18 More change types and places: see other change types | v2 | Could priority; outside the MVP's question |
| F-15 | Past-years water comparison | Won't | Removed in brief v0.2 (Out of Scope) |

## 5. Core User Journey

1. A visitor opens the public link; the Mayon map loads on the latest pair, with the disclaimer line visible. (US-016, US-001, US-006, US-012)
2. They search for their town and the map centers on it. (US-003)
3. They see where new material was detected and how much area it covers. (US-008)
4. They swipe between the before and after radar images. (US-007)
5. They tap a detected area and read the card: town, distance to the summit, danger-zone status, confidence, and the channel it's in. (US-004, US-023)
6. They step back through the timeline to the July 14, 2026 pyroclastic flow. (US-005)
7. They open the channel list, see which channels changed most, and open one to see its bars and strip. (US-024, US-025)
8. They open "What am I looking at?", "Data sources" and "How we checked this". (US-012, US-013, US-017)
9. They switch to the second site and see the same method there. (US-014)

Behind the journey, the maintainer processes and publishes each pair and adds the second site from a config file; the pipeline computes the channel areas. (US-009, US-015, US-026) The whole journey works on a phone. (US-018)

## 6. MVP Success Criteria

| # | Criterion | Target | How it's measured |
| --- | --- | --- | --- |
| 1 | Challenge requirements visibly met (G-01) | R1–R8: 8 of 8, by 2026-11-15 | Walk through the checklist's §10 pre-submit list on the live site |
| 2 | Eruption shown in real NISAR data (G-02) | ≥ 1 post-eruption pair published by 2026-11-07 | Count published pairs after 2026-10-30 in the Mayon pair list |
| 3 | Second site live (R7) | 1 site on another continent with ≥ 1 published pair by 2026-11-13 | Site list on the live app |
| 4 | Result checked against an independent source | ≥ 1 pair with a validation record by 2026-11-13 | "How we checked this" panel on the live app |
| 5 | Readable for non-experts (G-03) | ≥ 7 of 10 testers correctly say where new material is and which channel it's in, by 2026-11-30 | Short test session with a written answer sheet |
| 6 | Channel timeline live (F-20) | At least 1 confirmed channel with its bars on the live app, by 2026-11-10 | Open the channel list on the live app |

## 7. Allowed Shortcuts

| Shortcut | Instead of | Replaced by (version) |
| --- | --- | --- |
| The maintainer runs the pipeline by hand in Colab or locally | Scheduled automatic processing | F-17, US-021 (v1.2) |
| Validation records are typed by hand from PHIVOLCS bulletins | A repeatable validation routine for every pair | More validated pairs in v1.1 |
| Channel lines are prepared once and kept as a fixed file | A maintained channel dataset | Reviewed after the hackathon (v1.1) |
| English only | Filipino and Bikol | F-16, US-020 (v1.2) |
| The second site has 2 pairs | A full timeline for the second site | v1.1 |
| No staging site; the maintainer checks on localhost before publishing | A separate staging deployment | Reviewed in v1.1 |

## 8. Risks and Mitigations

| Risk | Likelihood (Low / Med / High) | Impact (Low / Med / High) | Mitigation |
| --- | --- | --- | --- |
| Space Apps or local-event rules don't allow code written before 2026-11-14 | [TBD] | High | Check the rules first (brief Open Question 5); if not allowed, keep the docs and rebuild during the event from the roadmap |
| The eruption pair shows no clear new material | Med | High | Keep the July 14, 2026 pyroclastic-flow pair as the backup showcase |
| Post-eruption products arrive later than 36–72 h | Med | Med | Prepare the pipeline on older pairs first so the eruption pair takes hours, not days |
| The Panama result hasn't been checked against mapped landslides | Med | Med | Show it as one plain change map with its limits stated, and compare it with mapped landslides before publishing |
| Thresholds are tuned to make the eruption look good | Med | High | Done: the thresholds were set on 2026-11-01, before the post-eruption passes were opened (FR-023) |
| Text reads like a lahar forecast | Med | High | Review all text against FR-038 before release |
| Large downloads on slow internet; Colab resets | High | Med | Crop early, cache downloads, save outputs to Google Drive |
| Solo beginner builder runs out of time | Med | High | Build the thin slice first (one pair end to end), then widen; deferred items stay deferred |

## 9. Assumptions

- The Space Apps demo is a video of 30 s or less, or 7 slides or fewer (challenge checklist §7).
- Post-eruption products for tracks 104 and 111 appear around 2026-11-03 to 2026-11-04 (brief §7).
- A presenter teammate records the demo; the maintainer builds.

## 10. Open Questions

| # | Question | Affects |
| --- | --- | --- |
| 1 | How many hours per week can the builder spend? | §2, 07-roadmap |
| 2 | Who are the 10 testers, and when can the test session happen? | §6 criterion 5 |
| 3 | Do the event rules allow code written before 2026-11-14? | §8 |
| 4 | Closed on 2026-11-01: Panama, two pairs. | F-10, §6 criterion 3 |

## 11. Conflicts with Earlier Documents

None.

## 12. Revision History

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-31 | First draft |
| 0.2 | 2026-11-01 | Added F-20 Channel timeline and criterion 6. Second site is Panama. |

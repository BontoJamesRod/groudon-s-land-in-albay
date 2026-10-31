# Roadmap: Mayon Radar Watch

| Version | Status | Last updated | Based on |
| --- | --- | --- | --- |
| 0.2 | Draft | 2026-11-01 | 00 v0.4, 01–06 v0.2 (all Draft), consistency-03 |

No calendar is given, because weekly hours aren't known yet (02 Open Question 1). The dates below are fixed outside events and the targets already set in 02 §6, not estimates.

## 1. Phases

| Phase | Goal | Includes (F-IDs) | Exit criteria |
| --- | --- | --- | --- |
| Phase 0: Setup | Project ready to build and deploy | — | An empty Leaflet map opens at the public URL in a private window; CI runs tests, the contract check and the secret scan |
| Phase 1: MVP | Show where Mayon put new material after the Oct 30, 2026 eruption and which channels it's in, plus a second site (02 §1) | F-01, F-02, F-03, F-04, F-05, F-08, F-09, F-10, F-11, F-12, F-13, F-19, F-20 | 02 §6 success criteria 1–4 and 6 met; 08 exit criteria met; entry submitted |
| Phase 2: v1.1 | Add the deferred Could features that reuse the same data | F-06, F-07, F-14 | Their stories (US-010, US-011, US-019) pass their acceptance criteria |
| Phase 3: v1.2 | Reach more residents and stop manual runs | F-16, F-17 | US-020 and US-021 pass their acceptance criteria |
| Phase 4: v2 | Other change types and places | F-18 | US-022 passes its acceptance criteria |

## 2. Milestones

| # | Milestone | Done when | Fixed date or target |
| --- | --- | --- | --- |
| 1 | Setup done | T-001 to T-007 done: empty map live at the public URL | Before the eruption data arrives |
| 2 | Thin slice | Build-order steps 8–22 done (T-008 to T-025, except T-010, T-020 and T-021): one real pair runs from ASF to the live map | Before 2026-11-03, when eruption products are expected (brief §7) |
| 3 | Eruption pair live | T-038 done | Target 2026-11-07 (02 §6, criterion 2) |
| 4 | MVP feature-complete | Second site (T-037), validation (T-039) and phone pass (T-034) done | Target 2026-11-13 (02 §6, criteria 3 and 4) |
| 5 | Tested and submitted | T-040 to T-042 done | Hackathon 2026-11-14 to 2026-11-15 (fixed) |
| 6 | Readability test | T-043 done | Target 2026-11-30 (02 §6, criterion 5) |
| 7 | Channel timeline live | T-073 to T-078 done | Build 2026-11-05 to 2026-11-10 (02 §6, criterion 6) |

## 3. Task Breakdown

### Phase 0: Setup

| T-ID | Task | Related IDs | Size | Depends on | Done when |
| --- | --- | --- | --- | --- | --- |
| T-001 | Create the public repository with the folders from 04 §10, a `.gitignore` for `raw/`, `*.h5`, `.netrc`, `pipeline/out/` and `pipeline/logs/`, and a README stub | ADR-001, ADR-003, US-016 | S | — | The repository and README open in a signed-out browser |
| T-002 | Write `pipeline/requirements.txt` and install it in Colab and on Windows | ADR-002 | S | T-001 | `import asf_search, earthaccess, h5py, rasterio` works in both places |
| T-003 | Log in with `earthaccess` and search NISAR GCOV over the Mayon bounds | US-009, ADR-002 | S | T-002 | The search lists tracks 111, 104 and 39 as in the brief |
| T-004 | Create `site/index.html`, `site/404.html` and `site/css/`, copy Leaflet 1.9.4 into `site/vendor/`, show an empty map at the Mayon center | SCR-01, SCR-09, ADR-004, US-016 | S | T-001 | `python -m http.server` in `site/` shows the map on localhost |
| T-005 | Add the GitHub Actions workflow that deploys `site/` to the chosen host | ADR-005, US-016 | S | T-004 | The public URL shows the map in a private window with no login |
| T-006 | Set up `pytest` and the `contract_check` skeleton (envelope and `schema_version` for every JSON file under `site/data/`) and run both in CI | TBL-01, API-001, NFR-008 | M | T-005 | A broken JSON file fails CI; a correct one passes |
| T-007 | Add a secret-scanning step to CI | NFR-002 | S | T-005 | A fake secret on a test branch fails the check |

### Phase 1: MVP

| T-ID | Task | Related IDs | Size | Depends on | Done when |
| --- | --- | --- | --- | --- | --- |
| T-008 | Write `pipeline/sites/mayon.json` and the `config` module that checks it and builds the `sites` row | US-015, TBL-01, SCR-12 | S | T-002 | A valid config gives the row; reversed bounds stop with "Invalid bounds in site config: <file>" |
| T-009 | Build `towns.geojson`, `land.geojson` and the boundary row of `sources.json` for Mayon from the Albay boundary file | US-001, US-003, TBL-02, TBL-10, TBL-11, API-002, API-003, API-004 | M | T-008 | Files pass the contract check; town borders line up with the background imagery on localhost |
| T-010 | Compile the channel names from PHIVOLCS bulletins, get their lines from the chosen source, link each to its towns, write `channels.geojson` and its `sources.json` row | US-023, TBL-03, TBL-10, API-005, ADR-008 | M | T-009, T-073 | Every channel has a confirmed line, at least 1 town and a name source; the file passes the contract check |
| T-011 | Write `events.json` with the 2026-07-14 and 2026-10-30 events and their sources | US-005, TBL-07, API-006 | S | T-008 | The file passes the contract check |
| T-012 | Build the `search` and `pairs` modules: list passes per track, frame and direction, form consecutive pairs, stop on mixed passes or missing GCOV products | US-009, TBL-04, TBL-05, SCR-12 | M | T-003, T-008 | Track 111 pairs match Vertex; mixed tracks and an unknown granule give the exact 01 messages and write no files |
| T-013 | Build the `download` module: download or stream, crop to the site bounds, cache in `raw/` (or Google Drive in Colab) | US-009 | M | T-012 | A second run uses the cache; cropped arrays cover the site bounds |
| T-014 | Build the `gcov` module: HH backscatter in dB, 5 × 5 speckle filter, brightness change, sea, coverage and product masks with no-data reasons | US-008, TBL-06, TBL-11 | M | T-013, T-009 | Unit tests pass; the Oct 7 → Oct 19 track 111 pair gives a median land change near the +0.14 dB found in the progress notes |
| T-015 | Build the `coherence` module: GUNW coherence for the current and previous pair, resampled to the GCOV grid; brightness-only fallback | US-008, ADR-006 | M | T-013 | Unit tests pass on small test arrays; a pair without GUNW sets `coherence_used` to `false` |
| T-016 | Study thresholds on at least 3 quiet pairs and the July 14 pair; record the chosen values in the site config and the reasons in a report (never the values in `docs/`) | US-008, TBL-05 | M | T-014, T-015 | Thresholds are in the site config and dated before any pair after 2026-10-30 is opened |
| T-017 | Build the `classify` module: none, low and high classes, areas in km², `new_material` grid with no-data codes | US-008, TBL-05, TBL-06 | S | T-016 | Tests cover every class and code; `new_material_area_km2` equals high + low |
| T-018 | Build the `export` module: reproject to EPSG:4326, colorize, write the 5 layer images, `new_material.bin` and `pair.json` to `pipeline/out/`, print the summary | US-007, US-009, US-013, TBL-04, TBL-05, TBL-06, API-008, API-009, API-010, SCR-12 | M | T-017 | `pair.json` passes the contract check; images line up with town borders on localhost |
| T-019 | Build the `publish` module: copy a pair to `site/data/`, set `published` and `published_at`, rebuild `pairs.json` and `sites.json` | US-009, US-015, TBL-01, TBL-05, API-001, API-007, SCR-12, ADR-009 | S | T-018 | Only published pairs appear in `pairs.json`; nothing from `pipeline/out/` reaches `site/` otherwise |
| T-020 | Process and publish the track 111 backlog since 2026-06-17, including the pair that spans 2026-07-14 | US-005, US-006 | M | T-019 | `pairs.json` lists every available track 111 pair |
| T-021 | Process and publish the track 104 backlog since 2026-06-17 | US-005 | M | T-020 | `pairs.json` lists every available track 104 pair |
| T-022 | Build `data.js`: fetch files, check the envelope and `schema_version`, map failures to NOT_FOUND, NETWORK_ERROR and INVALID_DATA | API-001, API-002, API-003, API-004, API-005, API-006, API-007, API-008, API-009, API-010, API-011, US-014 | S | T-004 | A 404, an offline browser and a broken file each give the right code |
| T-023 | Build `map.js`: site settings, zoom limits, background tiles with the "Background map unavailable" fallback, town borders and names, coastline, danger-zone ring | US-001, US-002, SCR-01, API-001, API-003, API-004 | M | T-022, T-009 | TC-001 to TC-004 pass |
| T-024 | Build `timeline.js`: pair list, latest pair by default, Previous and Next, "This is the latest pass", local-date label, event markers, empty state | US-005, US-006, SCR-01, API-006, API-007 | M | T-023, T-011, T-019 | TC-013 to TC-017 pass |
| T-025 | Build `layers.js` for new material: overlay, legend, total area, zero-area message, disclaimer line | US-008, US-012, SCR-01, API-008, API-009 | M | T-024 | TC-020, TC-021 and TC-029 pass |
| T-026 | Build `readout.js`: decode the grid, find the town, distance, danger-zone notice, class and confidence, no-data reasons, loading and error states | US-004, SCR-02, API-010 | M | T-025 | TC-008 to TC-012 pass |
| T-027 | Build `search.js`: suggestions after 2 letters, center and open the card, no-match message | US-003, SCR-03 | S | T-026 | TC-005 to TC-007 pass |
| T-028 | Add the channel layer, the channel card, the channel line in the readout, channel sources in the legend, and the "Channels unavailable" fallback | US-023, SCR-02, API-005 | M | T-026, T-010 | TC-044 to TC-047 pass |
| T-029 | Build `compare.js`: before and after images with a divider and dates, and the missing-image message | US-007, SCR-04, API-009 | M | T-025 | TC-018 and TC-019 pass |
| T-030 | Write the "What am I looking at?" panel and put every interface text in `strings.js`; review all text against FR-038 | US-012, SCR-05 | S | T-025 | TC-028 and TC-030 pass |
| T-031 | Build the Data sources panel | US-013, SCR-06, API-002, API-008 | S | T-025 | TC-031 and TC-032 pass |
| T-032 | Build the site picker, switching, and the retry error | US-014, SCR-08, API-001 | S | T-024 | TC-034 passes; TC-033 passes once the second site exists |
| T-033 | Finish the 404 page and the public README (what the app is, data sources, how to run the pipeline) | US-016, SCR-09 | S | T-005 | TC-038 and TC-039 pass |
| T-034 | Phone and color-blind pass: 360 px layout, 44 × 44 px tap targets, palette check, text labels for every class | US-018, SCR-01, NFR-004 | M | T-028, T-029, T-030, T-031, T-032 | TC-042, TC-043 and TC-055 pass |
| T-035 | Build the "How we checked this" panel and the `validation` module; create the validation record for the July 14 pair from a PHIVOLCS bulletin | US-017, SCR-07, TBL-08, TBL-09, API-011 | M | T-020, T-025 | TC-040 and TC-041 pass |
| T-036 | Second site is Panama (`pipeline/reports/second-site-candidates.md` and the Panama trial); write its config and build its towns, land and sources files | US-004, US-015, F-10, FR-069, TBL-01, TBL-02, TBL-10, TBL-11 | M | T-008, T-009 | Its files pass the contract check with no code changes |
| T-037 | Process and publish 2 Panama pairs, the quiet pair first and then the earthquake pair, with the plain change map, no channels, and a check of the earthquake pair in "How we checked this" | US-014, US-015, US-017, F-10, FR-048, T-089 | M | T-036, T-019, T-032, T-087, T-088, T-089 | The owner has read the T-088 report; TC-033, TC-035 and TC-076 pass |
| T-038 | Process and publish the eruption pairs (tracks 104 and 111, 2026-10-19 → 2026-10-31 UTC) as soon as they are on ASF, including each track's previous pair if not yet done | US-005, US-008, F-05 | M | T-016, T-019 | At least 1 post-eruption pair is live (G-02) |
| T-039 | Create the validation record for an eruption pair | US-017, TBL-08, TBL-09 | S | T-038, T-035 | The panel shows it on the live site |
| T-040 | Run the whole test plan (08) on the live site; fix every Critical and Major bug | All MVP stories (US-001 to US-026), NFR-001 to NFR-009 | M | T-034, T-037, T-039, T-076, T-077, T-078 | 08 exit criteria met |
| T-041 | With the presenter, write and record the 30-second demo, write the submission text and data citations | F-11, US-016 | M | T-040 | Demo is 30 s or less, public, in English, with subtitles |
| T-042 | Release v1.0: final deploy, private-window check, first `CHANGELOG.md` entry | F-11, US-016 | S | T-041 | Public link and repository open in a private window; entry submitted |
| T-043 | Run the readability test with 10 residents or LGU staff | US-012, US-018 | M | T-042 | Results recorded against 02 §6 criterion 5 |

### Phase 2: v1.1

| T-ID | Task | Related IDs | Size | Depends on | Done when |
| --- | --- | --- | --- | --- | --- |
| T-044 | Add the ground-movement layer with plane removal and the "within the noise" message | US-010, F-06 | M | T-042 | US-010 acceptance criteria pass |
| T-045 | Add a lowlands site and the flood layer | US-011, F-07 | M | T-042 | US-011 acceptance criteria pass |
| T-046 | Add the point history chart | US-019, F-14 | M | T-042 | US-019 acceptance criteria pass |

### Phase 3: v1.2

| T-ID | Task | Related IDs | Size | Depends on | Done when |
| --- | --- | --- | --- | --- | --- |
| T-047 | Translate `strings.js` into Filipino and Bikol with an English fallback | US-020, F-16 | M | T-042 | US-020 acceptance criteria pass |
| T-048 | Schedule the pipeline in GitHub Actions with Earthdata credentials in repository secrets | US-021, F-17 | M | T-042 | US-021 acceptance criteria pass |

### Phase 4: v2

| T-ID | Task | Related IDs | Size | Depends on | Done when |
| --- | --- | --- | --- | --- | --- |
| T-049 | Add the first additional change type at a new site | US-022, F-18 | M | T-042 | US-022 acceptance criteria pass |

### Phase 1: Channel timeline (F-20, build 2026-11-05 to 2026-11-10)

| T-ID | Task | Related IDs | Size | Depends on | Done when |
| --- | --- | --- | --- | --- | --- |
| T-073 | Owner: confirm which candidate channel lines are right, and record who and when | F-19, F-20, FR-065, TBL-03, US-023, US-026 | S | T-065 | The confirmed list is written down; candidates stay out of `site/data/` |
| T-074 | Build the `channel_areas` module and `channel_areas.json`; add the confirmed-only and TBL-12 rules to the contract check | US-026, FR-060, FR-064, FR-065, TBL-01, TBL-03, TBL-12, API-005, API-012, ADR-011, SCR-12 | M | T-010, T-019, T-080 | TC-072, TC-073 and TC-074 pass |
| T-075 | Build the channel list in `channels.js`, with empty, loading and error states | US-024, FR-061, FR-067, SCR-01, SCR-13, API-012 | M | T-022, T-074 | TC-064, TC-065 and TC-066 pass |
| T-076 | Build the channel view: bars, no-data state and the strip on the map | US-025, FR-062, FR-063, FR-067, SCR-14, API-005, API-012 | M | T-075, T-028 | TC-067, TC-068, TC-069 and TC-070 pass |
| T-077 | Dim pairs with an unequal gap, with a short note, on the pass timeline and the channel timeline | US-005, US-025, FR-066, SCR-01, SCR-14, API-007 | S | T-024, T-076 | TC-070 and TC-071 pass |
| T-078 | Add the rule against legal labels to the wording test | US-012, FR-068 | S | T-030 | TC-075 passes |

### Owner's decisions on the docs run (2026-11-01)

| T-ID | Task | Related IDs | Size | Depends on | Done when |
| --- | --- | --- | --- | --- | --- |
| T-080 | Put the channel strip width in the site config, measured on each side of the line, the same as the channel test | FR-064, ADR-011, TBL-01, T-074 | S | T-061 | The config holds it and is checked on load |
| T-081 | Move the plan files out of `docs/` into `plans/` at the repo root, unedited | §11 | S | — | Files are in `plans/`, byte for byte; no threshold value is left in `docs/` |
| T-082 | Move the ground-movement coherence mask to the site config; the docs describe it in words | FR-031, US-010, F-06, T-044, TBL-01 | S | — | The config holds it and is checked on load; the number is gone from `docs/` |
| T-083 | Rerun the Panama trial under the final rule with no per-site tuning, into `pipeline/out/` only; read the boundary license. Don't publish | F-10, FR-023, T-036, T-037 | S | T-066 | Flagged share and license findings are in the report; nothing new under `site/data/` |
| T-084 | Make the map and the readout read the reach distance from the site config, through `sites.json` | FR-060, US-004, US-008, TBL-01, API-001, SCR-01, SCR-02, TC-061, TC-062 | S | T-057 | `DETECTION_REACH_KM` is gone; TC-061 and TC-062 pass |
| T-085 | Rename the legend labels to say which signals agree, and republish the pairs | FR-025, US-008, TBL-06, API-008, SCR-05 | S | T-050 | All published pairs carry the new labels with unchanged areas; the held pair stays off |

| T-086 | Accept CC BY-SA 4.0 for the Panama borders: credit geoBoundaries with its license in `sources.json` and the Data sources panel, and mark the published border files | F-09, F-10, FR-040, TBL-02, TBL-10, TBL-11, API-002, API-003, API-004, T-036 | S | T-083 | The panel and `sources.json` show the credit and license; both border files carry the license |
| T-087 | Make the map's boundary credit follow the selected site, and show only the selected site's sources plus the shared ones in the Data sources panel | F-01, F-09, F-10, FR-040, US-013, SCR-01, SCR-06, TBL-01, TBL-10, API-001, API-002, TC-077 | S | T-086 | Panama's map credit names geoBoundaries and CC BY-SA 4.0; Mayon's is unchanged; TC-077 passes |
| T-088 | Compare the Panama pair with a public map of landslides or ground damage for the earthquake, and write `pipeline/reports/panama-check.md`. Don't publish | F-10, T-037, T-083 | S | T-083 | The report cites the map and states the result; the owner decides on T-037 |

| T-089 | Give a site its own wording: change instead of new material, its own official source and limits, with the earthquake pair titled "Changed after the earthquake" and never called landslides | F-10, FR-070, US-014, SCR-01, SCR-02, SCR-05, TBL-01, TBL-06, API-001, TC-078 | S | T-088 | TC-078 passes; Mayon's text is unchanged |

| T-090 | Draw only real coastline and town borders, not the edge where they're clipped to the site; show the quiet Panama pair's role in "How we checked this" | FR-003, FR-048, US-001, US-017, SCR-01, SCR-07, TBL-05, API-008, TC-079, TC-080 | S | T-037 | TC-079 and TC-080 pass |

| T-091 | Draw the part of a channel past the reach distance as "Not checked", never as zero change | F-20, FR-071, US-025, SCR-01, SCR-14, TBL-03, API-005, TC-081 | S | T-076 | TC-081 passes |
| T-092 | Record the owner's verdict on Matanag (not confirmed), accept ODbL for the channel files, and cite the PHIVOLCS advisory of 16 January 2026 (DZRH report) for Lidong and Padang next to the 2000 bulletin | F-19, FR-065, TBL-03, TBL-10, API-005 | S | T-073 | The record, the report and the published channels agree |
| T-093 | Narrow the unconfirmed-name rule to drawing or listing a channel, so a validation can cite such a place name | FR-065, US-026, TC-074 | S | T-074 | TC-074 passes; a cited name in a validation passes the contract check |
| T-094 | Show channel areas with 3 decimals | FR-061, FR-064, US-024, TBL-12, API-012, SCR-13, SCR-14, TC-064 | S | T-076 | TC-064 passes; all rows are rebuilt from the final rule |
| T-095 | On a short phone screen, open the map one zoom step further out when the danger-zone label wouldn't clear the map credits | FR-001, FR-004, US-001, TBL-01, TC-001, TC-082 | S | T-023 | TC-001 and TC-082 pass |

T-010 and T-074 to T-077 follow T-073, in that order, with T-028 after T-010 because T-076 needs it. T-078 wasn't part of the owner's request of 2026-11-01.

### Done work added on 2026-11-01

These tasks are done. They're listed so that every piece of finished work has an ID (see the ID errata in §11).

| T-ID | Task | Related IDs | Size | Depends on | Done when |
| --- | --- | --- | --- | --- | --- |
| T-050 | Republish the 11 pairs under the final thresholds and rule | FR-023, US-008, TBL-05, TBL-06 | M | T-066 | Done on 2026-11-01 |
| T-051 | Fix the test's low cell for the final rule, and write the night 5 report | FR-023, TC-011 | S | T-050 | Done on 2026-11-01 |
| T-052 | Add the browser test harness and browser tests for the MVP test cases | US-001 to US-023, TC-001 to TC-049 | M | T-034 | Done on 2026-10-31 |
| T-053 | Write the Day 3 report and add the owner's night 2 and day 3 plans to the repository | F-11 | S | — | Done on 2026-10-31 |
| T-054 | Measure the first view on Fast 4G and add version strings to JS and CSS links | NFR-001, TC-050 | S | T-025 | Done on 2026-10-31 |
| T-055 | List the exact doc edits the owner needs to decide on (`docs/notes/proposed-doc-changes.md`) | FR-011, FR-022, FR-030, TC-024 | S | — | Done on 2026-10-31 |
| T-056 | Write the afternoon run report | F-11 | S | — | Done on 2026-10-31 |
| T-057 | Limit Mayon detections to the reach distance, show the limit on the map, the card and the phone drawer, and republish all pairs | FR-060, US-004, US-008, TC-061, TC-062 | M | T-020 | Done on 2026-10-31 |
| T-058 | Add the evening calibration study and the guarded eruption script (the commit also published two track 104 pairs, which count towards T-021) | T-016, T-021, T-038, FR-023 | M | T-019 | Done on 2026-10-31 |
| T-059 | Add the eruption runbook, and make the blind and threshold tests still work after the cutoff is lifted | T-038, FR-023 | S | T-058 | Done on 2026-10-31 |
| T-060 | Write the evening report and tidy the eruption runbook | T-038 | S | T-059 | Done on 2026-10-31 |
| T-061 | Add the night 4 channel test and its report | F-19, F-20 | M | T-020 | Done on 2026-10-31 |
| T-062 | Write the night 4 report, with a note on the brightness-leads branch | F-19 | S | T-061 | Done on 2026-10-31 |
| T-063 | Add an optional brightness-leads rule to `classify`, off by default | FR-023, ADR-006, TC-022, TC-063 | S | T-017 | Done on 2026-10-31 |
| T-064 | Run the rain study for the channel test, with heavy-rain and low-rain checks, and add its results | F-19 | M | T-061 | Done on 2026-11-01 |
| T-065 | Add candidate matches between PHIVOLCS channels and OSM lines | F-19, FR-058, T-010 | M | — | Done on 2026-11-01 |
| T-066 | Lock the final thresholds and the brightness-leads rule, and lift the blind cutoff | FR-023, ADR-006, T-016 | S | T-063 | Done on 2026-11-01 |
| T-067 | Apply the 6 approved changes in `docs/notes/proposed-doc-changes.md`, with the code, test and data parts of changes 2 and 6 | FR-011, FR-022, FR-030, TC-011, TC-024, API-008, TBL-10, US-004 | S | — | Done on 2026-11-01 |
| T-068 | Record the owner's decisions in the docs: the final rule, the reach limit, the lifted blind cutoff and the held pair | FR-023, FR-060, ADR-006, US-004, US-008, TC-022, TC-061, TC-062, TC-063 | S | — | Done on 2026-11-01 |
| T-069 | Add the Channel timeline to every doc, with new IDs | F-20, US-024, US-025, US-026, FR-061 to FR-067, SCR-13, SCR-14, ADR-011, TBL-12, API-012, TC-064 to TC-074 | M | — | Done on 2026-11-01 |
| T-070 | Add the out-of-scope lines and the legal-label rule, and name Panama as the second site | F-10, US-004, US-012, FR-068, FR-069, TC-075, TC-076 | S | — | Done on 2026-11-01 |
| T-071 | Repair the task IDs: add the done work to this roadmap, the ID errata and the rule in `CLAUDE.md` | §11 | S | — | Done on 2026-11-01 |
| T-072 | Update `PROGRESS.md` and the README, write `reviews/consistency-03.md` and the docs run report | §3 | S | T-071 | Done on 2026-11-01 |
| T-079 | Check the rendered page with a vendored axe-core in a browser test, fix what it finds, and set up the axe Linter config and the cSpell word | NFR-004, F-13, US-018, SCR-01, SCR-04, SCR-05 | S | T-052 | Done on 2026-11-01 |

## 4. Build Order

Done work from T-050 to T-072, and T-079 to T-090, is listed in §3 and isn't repeated here. T-091 comes right after T-076.

1. T-001: everything else lives in the repository.
2. T-002: the pipeline needs its libraries.
3. T-003: proves Earthdata access before any processing work.
4. T-004: the web side needs a page to grow from.
5. T-005: deploy early so problems with hosting show up while they're cheap.
6. T-006: the contract check guards every later data file.
7. T-007: no secret should ever reach the public repository.
8. T-008: every pipeline step needs the site config.
9. T-009: towns and land are needed for masks and the map.
10. T-011: small; the timeline needs it later.
11. T-012: finding and pairing passes comes before downloading.
12. T-013: downloads feed both processing modules.
13. T-014: brightness change is the first signal.
14. T-015: coherence loss is the second signal.
15. T-016: thresholds must be fixed before the eruption data arrives.
16. T-017: classification needs the thresholds.
17. T-018: export makes the files the web app reads.
18. T-019: publishing puts the first pair on the site.
19. T-022: the web app needs its data loader first.
20. T-023: the map is the base for every layer.
21. T-024: the timeline picks which pair to show.
22. T-025: completes the thin slice (milestone 2).
23. T-038: the eruption pairs, as soon as they're on ASF (milestone 3).
24. T-026: the readout makes the map readable at one spot.
25. T-010: channel data for the next task.
26. T-028: channels connect new material to towns.
27. T-027: search reuses the readout.
28. T-029: compare view.
29. T-030: explainer and the wording review.
30. T-031: data sources for judges.
31. T-032: site picker, needed before the second site goes live.
32. T-036: second-site data.
33. T-037: second site live.
34. T-020: track 111 backlog, including the July 14 pair.
35. T-021: track 104 backlog.
36. T-035: validation panel, first record on the July 14 pair.
37. T-039: validation of an eruption pair.
38. T-033: 404 page and README.
39. T-034: phone and color-blind pass over the finished screens.
40. T-073: the owner confirms channel lines first; everything below needs them.
41. T-074: channel strips and areas in the pipeline.
42. T-075: channel list.
43. T-076: channel view, bars and strip.
44. T-077: unequal-gap marking on both timelines.
45. T-078: the rule against legal labels in the wording test.
46. T-040: full test run (milestone 4 complete).
47. T-041: demo and submission text.
48. T-042: release v1.0 (milestone 5).
49. T-043: readability test (milestone 6).
50. T-044: ground movement.
51. T-045: floods.
52. T-046: point history.
53. T-047: Filipino and Bikol.
54. T-048: automatic updates.
55. T-049: another change type.

## 5. Definition of Done

- [ ] Code follows the technical design, database design, and API spec
- [ ] Acceptance criteria for the related stories pass
- [ ] Tests written or updated
- [ ] No secrets or passwords in the code
- [ ] Documents updated if behavior changed
- [ ] Every published file passes the contract check
- [ ] New or changed interface text reviewed against FR-038

## 6. Schedule Risks

| Risk | Impact on schedule | Mitigation |
| --- | --- | --- |
| Eruption products arrive after 2026-11-04 | Milestone 3 slips by the same number of days | Finish the thin slice first, so T-038 takes hours, not days |
| Threshold study (T-016) is inconclusive | Milestones 2 and 3 slip by [TBD] days | Use the July 14 pair as the reference event; keep low and high confidence separate instead of forcing one threshold |
| Large downloads on slow internet; Colab resets | Each backlog task takes longer | Crop early, cache on Google Drive, process the eruption pairs before the backlogs |
| The Panama result doesn't match the mapped landslides, or its boundary license doesn't suit | Milestone 4 slips; R7 at risk | Compare it with mapped landslides first; Fuego and Nyamulagira stay the fallbacks in the candidates report |
| Event rules forbid pre-built code | Most of Phase 1 has to happen during the 48 hours | Check the rules first (brief Open Question 5); keep this roadmap as the 48-hour plan if needed |
| One builder | Any sickness or school deadline stops all work | Keep deferred features deferred; the presenter takes T-041 |

## 7. Assumptions

- One builder does every task except the demo recording, which is shared with the presenter (T-041).
- Sizes assume a beginner using the existing notebook and scripts as a starting point.
- GitHub Pages is the host (04 ADR-005, still a Suggestion); another static host changes only T-005.

## 8. Open Questions

| # | Question | Affects |
| --- | --- | --- |
| 1 | What is the start date and how many hours per week are available? Needed to put dates on the plan. | §2 |
| 2 | Closed on 2026-11-01: OpenStreetMap candidates, confirmed by the owner (T-073). | T-010, T-073 |
| 3 | Closed on 2026-11-01: Panama. | T-036, T-037 |
| 4 | Do the event rules allow building before 2026-11-14? | All of Phase 1 |

## 9. Conflicts with Earlier Documents

None.

## 10. Revision History

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-31 | First draft |
| 0.2 | 2026-11-01 | Added the Channel timeline tasks, the done work (T-050 to T-072), milestone 7 and the ID errata. Named Panama for T-036 and T-037. Added T-079 to T-091. |

## 11. ID Errata

From the afternoon of Oct 31, some commit labels stopped matching this roadmap. History isn't rewritten: this table gives each commit's real task ID. The IDs in the "Label used" column keep their meaning from §3 (for example, T-042 is still "Release v1.0"). Commits 78ff330 (T-050) and 33807d9 (T-051) already match. From now on, commit messages use only IDs that exist in this file.

| Commit | Label used | Real task ID | What it did |
| --- | --- | --- | --- |
| d0b5561 | T-029 | T-052 | Fix compare closing, and add the browser test harness (the fix part stays T-029) |
| 88ce6eb | T-034 | T-052 | Browser tests for the MVP test cases |
| 3caa367 | T-037 | T-053 | Day 3 report |
| 13c65c3 | T-037 | T-053 | Owner's night 2 and day 3 plans |
| 06f0fb5 | T-039 | T-054 | First-view measurement and version strings |
| bdde5b7 | T-037 | T-055 | List of proposed doc edits |
| 0906405 | T-037 | T-056 | Afternoon report |
| 5768d19 | T-037 | T-056 | Afternoon download total |
| d274224 | T-038 | T-057 | 10 km reach limit and republish |
| d551c8f | T-034 | T-057 | 10 km limit on the phone drawer |
| 8045b2e | T-039 | T-058 | Evening calibration, eruption script, two track 104 pairs (those count towards T-021) |
| fb1f1e6 | T-040 | T-059 | Eruption runbook |
| f1da270 | T-041 | T-060 | Evening report |
| c00d4ae | T-042 | T-061 | Night 4 channel test |
| 68d6684 | T-043 | T-062 | Night 4 report |
| f41a49c | T-044 | T-063 | Brightness-leads rule |
| e10cb3d | T-045 | T-062 | Brightness-leads note in the night 4 report |
| 35263c2 | T-046 | T-064 | Blocked rain rerun, heavy-rain and low-rain checks |
| b24eb24 | T-047 | T-064 | Rain rerun results |
| 06c1926 | T-048 | T-065 | Channel candidate matches |
| 0104a01 | T-049 | T-066 | Final thresholds and rule, blind cutoff lifted |

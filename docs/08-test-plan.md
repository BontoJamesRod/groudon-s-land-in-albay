# Test Plan: Mayon Radar Watch

| Version | Status | Last updated | Based on |
| --- | --- | --- | --- |
| 0.2 | Draft | 2026-11-01 | 01 v0.2, 02 v0.2, 03 v0.2, 06 v0.2 (all Draft) |

## 1. Scope

**Tested in this plan:** the MVP features F-01, F-02, F-03, F-04, F-05, F-08, F-09, F-10, F-11, F-12, F-13, F-19 and F-20 (02 §3), and NFR-001 to NFR-009.
**Not tested:** F-06, F-07, F-14, F-16, F-17 and F-18, deferred to v1.1 and later (02 §4); F-15, removed in brief v0.2.

## 2. Test Approach

| Level | What it covers | Tool | Who runs it |
| --- | --- | --- | --- |
| Unit | Pipeline math and rules: dB conversion, change, coherence loss, classes, masks, pair checks, config checks, grid encoding | Suggestion: `pytest` | Maintainer, and CI on every push |
| Integration | Pipeline output against the 05 and 06 contract: every published file, field and value range | `contract_check` (04 §3) | Maintainer, and CI on every push |
| End-to-end | The core journey (02 §5) | Automated browser tests in Chromium (`pipeline/tests/e2e/`, T-052), plus a manual run on the live site following the steps below | CI on every push and pull request; maintainer, then the presenter, on the live site |
| Manual | Visual checks, wording review, phone layout, color-blind simulation, performance | Chrome DevTools (device mode, network throttling, request blocking, "Emulate vision deficiencies"), Lighthouse | Maintainer and presenter |

## 3. Test Cases

Fixtures used below are listed in §5.

| TC-ID | Acceptance criterion | Other IDs | Scenario | Steps | Expected result | Type | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TC-001 | US-001/AC-1 | FR-001, FR-002, FR-003, FR-004, SCR-01, API-001, API-003, API-004 | Map opens on Mayon | 1. Open the public link. 2. Wait for the map. | Map centered on 13.2572° N, 123.6856° E at the default zoom (see TC-082 for short phones); town borders, town names, coastline and a 6 km ring labeled "Permanent Danger Zone (6 km)" are visible | Positive | High |
| TC-002 | US-001/AC-2 | FR-005, SCR-01 | Background imagery fails | 1. In DevTools, block requests to the tile host. 2. Reload. | "Background map unavailable" appears; borders, coastline and the ring still show | Negative | High |
| TC-003 | US-002/AC-1 | FR-006, SCR-01 | Pan and zoom | 1. Drag the map. 2. Zoom in 3 steps with scroll or pinch. | Map moves and zooms; the new-material overlay and channels stay on the same town borders | Positive | High |
| TC-004 | US-002/AC-2 | FR-006, SCR-01 | Zoom out past the minimum | 1. Zoom out until it stops. 2. Try once more. | Zoom level stays at the site's `min_zoom` | Edge | Medium |
| TC-005 | US-003/AC-1 | FR-007, FR-008, SCR-03, SCR-02, API-003 | Find Tabaco City | 1. Tap search. 2. Type "Tab". 3. Pick "Tabaco City". | Map centers on Tabaco City; its readout card opens | Positive | High |
| TC-006 | US-003/AC-2 | FR-009, SCR-03 | Name with no match | 1. Type "Xyz". 2. Submit. | "No town found. Try another name or tap the map." appears; the map doesn't move | Negative | High |
| TC-007 | US-003/AC-1 | FR-007, SCR-03 | Only 1 letter typed | 1. Type "T". | No suggestions yet; after a second letter, suggestions appear | Edge | Low |
| TC-008 | US-004/AC-1 | FR-010, SCR-02, API-010 | Tap a land point with a radar value | 1. Select the published Oct 7 → Oct 19 pair. 2. Tap a point in Daraga outside the danger zone. | Card shows "Daraga", a distance in km with 1 decimal, outside the danger zone, and a class (none, low or high) | Positive | High |
| TC-009 | US-004/AC-2 | FR-011, SCR-02, API-004, API-010 | Tap the sea | 1. Tap a sea point inside the site bounds. | "No radar data here" with the reason "sea" | Negative | High |
| TC-010 | US-004/AC-2 | FR-011, SCR-02, API-010 | Tap outside radar coverage | 1. Tap a point inside the site bounds but outside the radar frame (grid value 255). | "No radar data here" with the reason "outside radar coverage" | Edge | Medium |
| TC-011 | US-004/AC-2 | FR-011, FR-024, SCR-02, API-010 | Tap a cell the product flagged invalid | 1. Tap a cell with grid value 253 (find one with the fixture list). | "No radar data here" with the reason "the radar product marked this spot as invalid" | Edge | Medium |
| TC-012 | US-004/AC-3 | FR-012, SCR-02 | Tap inside the danger zone | 1. Tap a point 3 km from the summit. | Card shows "Inside the Permanent Danger Zone. Entry is not allowed." | Positive | High |
| TC-013 | US-005/AC-1 | FR-013, FR-014, SCR-01, API-007, API-008 | Pick an earlier pair | 1. Open the pair list. 2. Pick the pair spanning 2026-07-14. | Layers change; label shows both dates in Philippine time, the track, the frame and the direction | Positive | High |
| TC-014 | US-005/AC-2 | FR-015, SCR-01 | Next on the latest pair | 1. With the latest pair selected, press Next. | Selection doesn't change; "This is the latest pass" appears | Edge | Medium |
| TC-015 | US-005/AC-3 | FR-016, SCR-01, API-006 | Event markers | 1. Look at the timeline. | The pair whose dates contain 2026-10-30 is marked with the eruption's name; the pair containing 2026-07-14 is marked too | Positive | Medium |
| TC-016 | US-006/AC-1 | FR-017, SCR-01, API-007 | Latest pair by default | 1. Open the app fresh. | The selected pair is the one with the latest `after_acquired_start` in `pairs.json` | Positive | High |
| TC-017 | US-006/AC-2 | FR-018, SCR-01, API-007 | Site with no pairs | 1. On localhost, use the empty-pairs fixture. 2. Open the site. | "No radar passes processed yet for this site"; only base layers show | Edge | Medium |
| TC-018 | US-007/AC-1 | FR-019, SCR-04, API-009 | Compare before and after | 1. Tap Compare. 2. Drag the divider left and right. | Before image on the left, after image on the right, each labeled with its date | Positive | High |
| TC-019 | US-007/AC-2 | FR-020, SCR-04, API-009 | Missing image | 1. On localhost, use the missing-image fixture. 2. Tap Compare. | "Before/after images not available for this pair"; the map stays as it was | Negative | Medium |
| TC-020 | US-008/AC-1 | FR-025, SCR-01, API-008, API-009 | New-material layer and legend | 1. Select the eruption pair. 2. Check the map and legend. | Detected areas shaded; legend lists each class with its confidence and units; total area in km² with 2 decimals equals `new_material_area_km2` | Positive | High |
| TC-021 | US-008/AC-2 | FR-026, SCR-01 | Pair with nothing detected | 1. On localhost, use the zero-area fixture. | No shading; "No new material detected between <before date> and <after date>" with the real dates | Edge | Medium |
| TC-022 | US-008/AC-3 | FR-023 | Only brightness passes | 1. Run the `classify` unit tests with test arrays where only brightness passes. | Those cells get class 1 (low), never 2 (high) | Negative | High |
| TC-023 | US-008/AC-3 | FR-030, TBL-05 | No coherence data | 1. Process a pair whose GUNW is unavailable (fixture). | `coherence_used` is `false`; the grid has no class 2 cells; `high_confidence_area_km2` is 0 | Edge | High |
| TC-024 | US-009/AC-1 | FR-029, SCR-12, TBL-05, TBL-06 | Process a real pair | 1. Run the pipeline for track 111, 2026-10-07 → 2026-10-19. | Files written to `pipeline/out/`; summary shows status "ready", the granule IDs used (4 with coherence: 2 GCOV and 2 GUNW; 2 without) and areas in km² | Positive | High |
| TC-025 | US-009/AC-2 | FR-027, SCR-12 | Mixed tracks | 1. Run with a track 111 pass and a track 104 pass. | Stops with "Passes are not from the same track, frame and direction"; no files written | Negative | High |
| TC-026 | US-009/AC-3 | FR-028, SCR-12 | Product not on ASF | 1. Run with the fake granule ID fixture. | Stops with "Product not available yet: <granule_id>" naming that granule; no files written | Negative | High |
| TC-027 | US-009/AC-1 | FR-021 | Brightness change math | 1. Run the `gcov` unit tests: before 0.01, after 0.1 (linear power). | Change is +10.0 dB; NaN and zero inputs become no data, never ±infinity | Positive | High |
| TC-028 | US-012/AC-1 | FR-036, SCR-05 | Explainer content | 1. Open "What am I looking at?". | Sections for how radar sees, color meanings, confidence levels, at least 3 limitations, and a working PHIVOLCS link | Positive | High |
| TC-029 | US-012/AC-2 | FR-037, SCR-01 | Disclaimer always visible | 1. Turn each radar layer on in turn. 2. Open and close each panel. | "This is not an official warning. Follow PHIVOLCS and your LGU." stays visible on the main screen whenever a radar layer is on | Positive | High |
| TC-030 | US-012/AC-3 | FR-038 | No prediction wording | 1. Search `strings.js` and every page for "will", "expect", "forecast", "predict" next to lahar, eruption or flood. 2. Read each hit. | No text states that a lahar, eruption or flood will happen | Negative | High |
| TC-031 | US-013/AC-1 | FR-039, SCR-06, API-008 | Radar sources | 1. Open Data sources for the eruption pair. | Every radar layer lists product type, granule IDs, acquisition dates, PROVISIONAL, and an ASF link that opens the product | Positive | High |
| TC-032 | US-013/AC-2 | FR-040, SCR-06, API-002 | Context sources | 1. Scroll to "Context data". | Background map, borders, coastline and channels each listed with source and license, separate from radar data; NISAR is listed under "Radar data", not here | Positive | Medium |
| TC-033 | US-014/AC-1 | FR-041, SCR-08, API-001, API-007 | Switch to the second site | 1. Tap the site name. 2. Pick the second site. | Map moves there; its timeline and latest pair show | Positive | High |
| TC-034 | US-014/AC-2 | FR-042, SCR-08, API-007 | Site fails to load | 1. In DevTools, block the second site's `pairs.json`. 2. Pick that site. | "Couldn't load <site name>. Try again." with Retry; Mayon stays on screen | Negative | High |
| TC-035 | US-015/AC-1 | FR-043, SCR-12, TBL-01 | New site from config only | 1. Add the second site's config. 2. Run and publish. 3. Check `git diff` for code changes. | Site appears in the site list; no files under `pipeline/mrw/` or `site/js/` changed | Positive | High |
| TC-036 | US-015/AC-2 | FR-044, SCR-12 | Reversed bounds | 1. Run with the reversed-bounds config fixture. | Stops with "Invalid bounds in site config: <file>" naming the file | Negative | High |
| TC-037 | US-016/AC-1 | FR-045 | Public link, no login | 1. Open the public URL in a private window. | App loads; no login prompt | Positive | High |
| TC-038 | US-016/AC-2 | FR-046, SCR-09 | Unknown path | 1. Open `<public URL>/no-such-page`. | "Page not found" with a link that opens the map | Negative | Medium |
| TC-039 | US-016/AC-3 | FR-047 | Public repository | 1. Open the repository URL while signed out of GitHub. | Code and README visible | Positive | High |
| TC-040 | US-017/AC-1 | FR-048, SCR-07, API-011 | Validation shown | 1. Select a pair with a validation record. 2. Open "How we checked this". | Table lists each place, reported yes or no, detected yes, no or not visible to radar, and the source's name, date and link | Positive | High |
| TC-041 | US-017/AC-2 | FR-048, SCR-07, API-011 | No validation | 1. Select a pair without a record. 2. Open the panel. | "Not yet checked against an independent source" | Edge | Medium |
| TC-042 | US-018/AC-1 | FR-049, SCR-01 | Phone layout | 1. DevTools device mode at 360 px wide. 2. Use every control. 3. Measure tap targets. | No horizontal scrolling; every control reachable; every tap target at least 44 × 44 px | Positive | High |
| TC-043 | US-018/AC-2 | FR-050, SCR-01 | Color-blind check | 1. DevTools "Emulate vision deficiencies": deuteranopia, then protanopia. 2. Check map and legend. | Every class still distinguishable; each class has a text label | Positive | Medium |
| TC-044 | US-023/AC-1 | FR-056, SCR-01, SCR-02, API-005 | Channels and towns | 1. Turn the channel layer on. 2. Tap the Mi-isi line. | Each channel drawn with its name; the card lists the towns Mi-isi passes through | Positive | High |
| TC-045 | US-023/AC-2 | FR-057, SCR-02, API-010 | New material in a channel | 1. Tap a detected cell inside a named channel's strip. | "New material detected in or near <channel name>" | Positive | High |
| TC-046 | US-023/AC-2 | FR-057, SCR-02 | New material away from channels | 1. Tap a detected cell outside every channel's strip. | "Not in a named channel on this map" | Negative | Medium |
| TC-047 | US-023/AC-3 | FR-058, SCR-01, SCR-06, API-002 | Channel sources | 1. With channels on, open the legend and Data sources. | Sources of channel names and channel lines are shown | Positive | Medium |
| TC-048 | US-009/AC-1 | TBL-01, TBL-11, API-001, API-011 | All published files match the contract | 1. Run `contract_check` on `site/data/`. | 0 errors: every field, type, enum and constraint in 05 holds; image and grid sizes match their records | Positive | High |
| TC-049 | US-006/AC-1 | FR-059, API-007 | Unpublished pairs never shown | 1. Process a pair but don't publish it. 2. Deploy. 3. Check `pairs.json` and the timeline. | The pair isn't listed and its folder isn't under `site/data/` | Negative | High |
| TC-061 | US-004/AC-4 | FR-060, SCR-02, API-010 | Tap beyond the reach limit | 1. Tap a land point in Oas, about 13.5 km from the summit. | Card says "Not checked: this map only looks within 10 km of the summit"; it doesn't say "No new material detected" | Edge | High |
| TC-062 | US-008/AC-5 | FR-060, SCR-01, TBL-01, TBL-06 | Reach limit is drawn and stated | 1. Open the map and legend. 2. Run the contract check on published layers. | A dotted ring shows at the reach distance; every published `new_material` layer title states the limit | Positive | High |
| TC-063 | US-008/AC-4 | FR-023, TBL-06 | Only coherence loss passes | 1. Run the `classify` unit tests with test arrays where only coherence loss passes. | Those cells get class 0 (none) and add no area | Negative | High |
| TC-064 | US-024/AC-1 | FR-061, SCR-13, API-012 | Channels sorted | 1. Use a fixture with 3 channels with different areas and 1 with no radar data for the latest pair. 2. Open Channels. | Largest area first, 3 decimals, ties by name, the no-data channel last | Positive | High |
| TC-065 | US-024/AC-2 | FR-067, SCR-13, SCR-01 | No confirmed channels | 1. Use an empty-channels fixture. 2. Open Channels. 3. Switch to a site with no channel data. | "No confirmed channels yet for this site"; the other site shows no Channels button | Edge | Medium |
| TC-066 | US-024/AC-3 | FR-067, SCR-13, API-012 | List loading and failing | 1. Throttle, then block `channel_areas.json`. 2. Open Channels. | "Loading channel changes…", then "Couldn't load channel changes. Try again." with Retry; the map stays as it was | Negative | Medium |
| TC-067 | US-025/AC-1 | FR-062, SCR-14, API-012 | Bars per pass | 1. Open a channel. | One bar per published pair, in order of after date, labeled with its dates; each value equals its `flagged_area_km2` | Positive | High |
| TC-068 | US-025/AC-2 | FR-063, SCR-14, API-005 | Strip on the map | 1. Open a channel. 2. Go back. | Its strip shows and the map fits it; going back removes it | Positive | High |
| TC-069 | US-025/AC-3 | FR-067, SCR-14, API-012 | No radar data in a strip | 1. Use a fixture row with `checked_area_km2` 0. | The bar's place says "No radar data", never 0 km² | Edge | Medium |
| TC-070 | US-025/AC-4 | FR-066, SCR-14 | Unequal gap on the channel timeline | 1. Open a channel. 2. Find the 24-day pair. | Bar dimmed with "24-day gap, not comparable"; 12-day bars aren't dimmed | Edge | High |
| TC-071 | US-005/AC-4 | FR-066, SCR-01, API-007 | Unequal gap on the pass timeline | 1. Open the pair list. 2. Find the 24-day pair. | Pair dimmed with "24-day gap, not comparable"; 12-day pairs aren't dimmed | Edge | High |
| TC-072 | US-026/AC-1 | FR-064, FR-060, SCR-12, TBL-12, API-012 | Area in a strip | 1. Run the `channel_areas` unit tests with a small grid and a known strip, with flagged cells inside the strip, outside it and beyond the reach. | Only flagged cells inside the strip and the reach count; the area matches a hand calculation; one row per channel and pair | Positive | High |
| TC-073 | US-026/AC-2 | FR-064, SCR-12, TBL-01 | Strip width missing | 1. Run with a config that has channels and no width. | Stops with "Channel strip width missing in site config: <file>" | Negative | High |
| TC-074 | US-026/AC-3 | FR-065, TBL-03, API-005 | Confirmed channels only | 1. Run `contract_check` on a fixture with a channel without `confirmed_on`. 2. Check that no unconfirmed candidate from `channel_name_candidates.geojson` is in the published channel files. | The check fails on the fixture; no candidate is drawn or listed | Negative | High |
| TC-075 | US-012/AC-4 | FR-068 | No legal labels | 1. Search `strings.js`, every page and `site/data/` for "illegal", "unpermitted" and "violation". | No hits | Negative | High |
| TC-076 | US-004/AC-5 | FR-069, SCR-02, TBL-01 | Site with no summit | 1. Switch to Panama. 2. Tap a land point. | Card shows the town and the result, with no distance or danger-zone line | Edge | High |
| TC-077 | US-013/AC-3 | FR-040, SCR-01, SCR-06, TBL-10, API-001, API-002 | Credit and sources follow the site | 1. On Mayon, read the map credit and open Data sources. 2. Switch to a second site and do the same. | Each site shows its own boundary credit and sources plus the shared ones, never the other site's | Positive | High |
| TC-078 | US-014/AC-3 | FR-070, SCR-01, SCR-02, SCR-05, TBL-01, TBL-06, API-001 | A site's own wording | 1. Switch to Panama. 2. Read the legend, a card, the disclaimer, the help panel and the phone handle. 3. Switch back. | Panama says "change", names SINAPROC, titles the earthquake pair "Changed after the earthquake", and never says landslides there; Mayon's text comes back unchanged | Positive | High |
| TC-079 | US-001/AC-3 | FR-003, SCR-01, API-004 | No line along a clipped edge | 1. Build the coast and town lines for each site. | The real lines are there; no segment runs along the site's edge | Negative | Medium |
| TC-080 | US-017/AC-3 | FR-048, SCR-07, TBL-05, API-008 | A pair's check note | 1. Switch to Panama. 2. Select the quiet pair. 3. Open "How we checked this". | "Used as the 'before' comparison for the earthquake pair", not "Not yet checked" | Positive | Medium |
| TC-082 | US-001/AC-1 | FR-001, FR-004, SCR-01 | Short phone screen | 1. Open the site at 360 x 640. 2. Open it at 390 x 844 and at 1280 x 500. | At 360 x 640 the map opens one zoom step out, still centered, with the danger-zone label above the credits and Daraga, Legazpi City, Camalig and Santo Domingo visible, with no town name hidden; at 320 x 568 the label also clears the credits; the other two keep the default zoom | Positive | Medium |
| TC-083 | US-027/AC-1 | FR-072, TBL-13, API-013 | Histogram contract | 1. Run `contract_check` on a fixture with a wrong total, a wrong flagged count and a missing file. | Each one fails the check | Negative | High |
| TC-084 | US-027/AC-1 | FR-072, FR-075, TBL-13, TBL-14 | Numbers match the grid | 1. For every published pair, compare `flagged_cells` with the value grid, and each channel's with `channel_areas.json`. | They match | Positive | High |
| TC-085 | US-027/AC-2 | FR-073, SCR-01, API-013 | The chart | 1. Open the panel at 1280 and 360 px. 2. Compare the line's position with the site config's threshold. 3. Run axe. | Lines on both sides at the config's value, tails shaded, one sentence, and no serious or critical axe problem | Positive | High |
| TC-086 | US-027/AC-3, US-027/AC-4 | FR-073, FR-074, SCR-05 | No file, no slider | 1. Block `histogram.json`. 2. Read the help panel. | The pair still shows with the "not available" message; the help panel says why the line can't move, and the page has no control that moves it | Negative | Medium |
| TC-087 | US-027/AC-5 | FR-075, SCR-14, API-014 | Channel outline | 1. Open a channel at 1280 px. 2. Go back to the list. | The outline and its name show, and they go when the channel closes | Positive | Medium |
| TC-088 | US-028/AC-1 | FR-076, API-015 | Relief tiles and limit | 1. Run the download check with a size at the limit. 2. Run `contract_check` with a relief tile missing. 3. Check that the tiles cover the bounds at each zoom. | The download stops before it starts; the check fails; every tile is there | Negative | High |
| TC-089 | US-028/AC-1, US-028/AC-2, US-028/AC-4 | FR-005, FR-076, SCR-01 | Relief on the map | 1. Open Mayon at 360, 1280 and 2560 px. 2. Zoom out fully and pan to each corner. 3. Block the tiles. 4. Open Panama. | The view stays inside the tiles, with the Copernicus credit and no Esri request; the notice shows and the lines stay; Panama uses imagery | Positive | High |
| TC-090 | US-028/AC-3 | FR-077, SCR-01, SCR-13 | Layout | 1. Open Mayon at 360 and 1280 px. 2. Read the channel list and the panel. 3. Check the focus and the font. 4. Close the list on a phone. 5. Run axe. | The list is open and the focus hasn't moved; the panel is beside the map on a desktop; the pass controls return on a phone; the site's font is used; no serious or critical axe result | Positive | High |
| TC-091 | US-029/AC-1, US-029/AC-2, US-029/AC-3, US-029/AC-4 | FR-078 | Radar marks | 1. Count the flagged pixels in a pair's image. 2. Open it at 360 and 1280 px and measure a mark. 3. Read the legend. 4. Turn the layer off, and open compare. | One mark per flagged pixel, none under the minimum, each with its darker edge; the legend line shows; no marks with the layer off or in compare | Positive | High |
| TC-092 | US-030/AC-1, US-030/AC-2, US-030/AC-3 | FR-079, SCR-13, SCR-14 | Basketball courts | 1. Open the channel list and one channel. 2. Use areas of 0, 0.0001, 0.00042 and 0.12 km², and no data. | km² and the comparison show together, with singular, zero and under-half wording correct; no data shows none; a note gives the court's size | Positive | High |
| TC-081 | US-025/AC-5 | FR-071, FR-060, SCR-01, SCR-14, TBL-03, API-005 | A channel past the reach | 1. Look at the Mi-isi line on the map. 2. Open Mi-isi. 3. Tap the part past the reach. | That part is dashed and labeled "Not checked"; the strip stops at the reach; the card says "Not checked", never "No new material detected" | Edge | High |

## 4. Non-Functional Tests

| TC-ID | NFR-ID | Test | Pass condition |
| --- | --- | --- | --- |
| TC-050 | NFR-001 | Load the live site in Chrome with "Fast 4G" throttling and the cache disabled; record load time and bytes for the first view | Within the NFR-001 target ([TBD]; Suggestion: ≤ 5 s and ≤ 5 MB) |
| TC-051 | NFR-001 | Tap 10 points; measure the time from tap to card with the DevTools Performance panel | Within the NFR-001 target ([TBD]; Suggestion: ≤ 200 ms each) |
| TC-052 | NFR-002 | Run the secret scan on the whole repository history | 0 secrets found |
| TC-053 | NFR-002 | Open the site with `http://`; check every request in the Network panel | Redirects to `https://`; 100% of requests use HTTPS |
| TC-054 | NFR-003 | Open the public URL once a day during judging and log the result | Reachable every day; monthly target [TBD] (Suggestion: 99%) |
| TC-055 | NFR-004 | Run Lighthouse accessibility and check contrast of every text color; measure tap targets | Text contrast ≥ 4.5:1; tap targets ≥ 44 × 44 px |
| TC-056 | NFR-004 | Readability test with 10 residents or LGU staff (T-043) | ≥ 7 of 10 correctly say where new material is and which channel it's in |
| TC-057 | NFR-005 | Run the core journey (02 §5) on each browser in §6 | Every step works on every browser listed |
| — | NFR-006 | Not tested: the site is static files on the host's content network with no server of ours; the host's limits apply (verify) | — |
| TC-058 | NFR-007 | In DevTools, check Application > Cookies and storage, and every request while searching and tapping | 0 cookies; no request contains tapped coordinates or search text; requests go only to the site and the tile host |
| TC-059 | NFR-008 | `contract_check` rules for layers | 100% of radar layers have acquisition dates, units, maturity and a legend with confidence |
| TC-060 | NFR-009 | For the eruption pairs, record when both products appeared on ASF and when the pair was published | Within the NFR-009 target ([TBD]; Suggestion: ≤ 48 h) |

## 5. Test Data and Accounts

| Role | Test account | Data needed |
| --- | --- | --- |
| Visitor | None: no login | Published Mayon pairs: track 111, 2026-10-07 → 2026-10-19; the pair spanning 2026-07-14; the 24-day pair; at least 1 eruption pair; Panama with 2 pairs; at least 1 confirmed channel |
| Visitor (localhost only) | None | Fixtures in `pipeline/tests/fixtures/`, never deployed: a site with an empty `pairs.json`; a pair with `before_db.png` removed; a pair with 0 km² detected; a short list of grid cells with values 253, 254 and 255 |
| Maintainer | The maintainer's own Earthdata and GitHub accounts | Site config with reversed bounds; a track 111 pass and a track 104 pass; a fake granule ID; a pair whose GUNW is unavailable (or a flag that simulates it); small arrays for unit tests |

## 6. Environments and Devices

| Environment | Devices and browsers |
| --- | --- |
| Local | Windows laptop: Chrome with DevTools (device mode 360 px, throttling, request blocking, vision emulation) |
| Production | Android phone with Chrome; iPhone with Safari ([TBD]: is one available?); Windows with Chrome, Edge and Firefox |

There is no staging environment in the MVP (02 §7); risky changes are checked on localhost first.

## 7. Traceability Matrix

| US-ID | Acceptance criteria | TC-IDs |
| --- | --- | --- |
| US-001 | AC-1, AC-2, AC-3 | TC-001, TC-002, TC-079 |
| US-002 | AC-1, AC-2 | TC-003, TC-004 |
| US-003 | AC-1, AC-2 | TC-005, TC-007, TC-006 |
| US-004 | AC-1, AC-2, AC-3, AC-4, AC-5 | TC-008, TC-009, TC-010, TC-011, TC-012, TC-061, TC-076 |
| US-005 | AC-1, AC-2, AC-3, AC-4 | TC-013, TC-014, TC-015, TC-071 |
| US-006 | AC-1, AC-2 | TC-016, TC-049, TC-017 |
| US-007 | AC-1, AC-2 | TC-018, TC-019 |
| US-008 | AC-1, AC-2, AC-3, AC-4, AC-5 | TC-020, TC-021, TC-022, TC-023, TC-063, TC-062 |
| US-009 | AC-1, AC-2, AC-3 | TC-024, TC-027, TC-048, TC-025, TC-026 |
| US-012 | AC-1, AC-2, AC-3, AC-4 | TC-028, TC-029, TC-030, TC-075 |
| US-013 | AC-1, AC-2, AC-3 | TC-031, TC-032, TC-077 |
| US-014 | AC-1, AC-2, AC-3 | TC-033, TC-034, TC-078 |
| US-015 | AC-1, AC-2 | TC-035, TC-036 |
| US-016 | AC-1, AC-2, AC-3 | TC-037, TC-038, TC-039 |
| US-017 | AC-1, AC-2, AC-3 | TC-040, TC-041, TC-080 |
| US-018 | AC-1, AC-2 | TC-042, TC-043 |
| US-023 | AC-1, AC-2, AC-3 | TC-044, TC-045, TC-046, TC-047 |
| US-024 | AC-1, AC-2, AC-3 | TC-064, TC-065, TC-066 |
| US-025 | AC-1, AC-2, AC-3, AC-4, AC-5 | TC-067, TC-068, TC-069, TC-070, TC-081 |
| US-026 | AC-1, AC-2, AC-3 | TC-072, TC-073, TC-074 |
| US-027 | AC-1, AC-2, AC-3, AC-4, AC-5 | TC-083, TC-084, TC-085, TC-086, TC-087 |
| US-028 | AC-1, AC-2, AC-3, AC-4 | TC-088, TC-089, TC-090 |
| US-029 | AC-1, AC-2, AC-3, AC-4 | TC-091 |
| US-030 | AC-1, AC-2, AC-3 | TC-092 |

## 8. Exit Criteria

- [ ] All High-priority tests pass
- [ ] No open Critical or Major bugs
- [ ] `contract_check` reports 0 errors (TC-048)
- [ ] Secret scan finds 0 secrets (TC-052)
- [ ] Challenge requirements R1–R8 visibly met (checklist §10)

## 9. Bug Report Template

| Field | Content |
| --- | --- |
| Bug ID | BUG-001 |
| Title | Short description |
| Related IDs | TC, US, SCR, API |
| Steps to reproduce | 1. … |
| Expected | What should happen |
| Actual | What happened |
| Severity | Critical / Major / Minor |
| Evidence | Screenshot or log |

## 10. Assumptions

- The maintainer and the presenter are the only testers before the hackathon.
- Fixtures for edge cases are run on localhost and never deployed.
- The NFR targets marked `[TBD]` are set before TC-050, TC-051, TC-054 and TC-060 are run.

## 11. Open Questions

| # | Question | Affects |
| --- | --- | --- |
| 1 | Is an iPhone available for testing Safari? | §6, TC-057 |
| 2 | Closed on 2026-11-01: end-to-end tests are automated in Chromium and run in CI (§2). | §2 |
| 3 | What are the NFR-001, NFR-003 and NFR-009 targets? | TC-050, TC-051, TC-054, TC-060 |

## 12. Conflicts with Earlier Documents

None.

## 13. Revision History

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-31 | First draft |
| 0.2 | 2026-11-01 | TC-011, TC-022 and TC-024 updated. End-to-end tests are automated. Added TC-061 to TC-082. |

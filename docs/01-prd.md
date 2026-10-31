# PRD: Mayon Radar Watch

| Version | Status | Last updated | Based on |
| --- | --- | --- | --- |
| 0.1 | Draft | 2026-10-31 | 00-project-brief.md v0.3 (Draft) |

## 1. Overview

Mayon Radar Watch is a public web app that answers one question after every NISAR satellite pass: where did Mayon put new material, and which river channels and towns is it near? It compares NASA–ISRO NISAR radar images taken 12 days apart, maps fresh ash, rock and lava deposits, and shows them with the channels that drain the volcano. It is first built as an entry for the NASA Space Apps Challenge 2026 "Dancing with the SARs" challenge, and the same engine runs on a second site on another continent.

## 2. Objectives

| Objective | Supports goal |
| --- | --- |
| Ship a public app that meets every challenge requirement (R1–R8) | G-01 |
| Show the Oct 30, 2026 eruption with real NISAR pairs | G-02 |
| Explain radar results in plain words that residents and officials can repeat correctly | G-03 |

## 3. User Personas

### Channel resident, Visitor

- **Goals:** See whether new volcanic material landed near their town or in the channel that runs past it.
- **Pain points:** Can't see what changed on the ground after an eruption; clouds and ash block normal satellite photos.
- **Tech comfort:** [TBD]
- **Main device:** Phone (brief §7: "web app that works on phones")

### Barangay or LGU disaster official, Visitor

- **Goals:** Get a simple, honest picture of where new material is, to explain to residents.
- **Pain points:** Needs something they can explain to others without radar expertise.
- **Tech comfort:** [TBD]
- **Main device:** [TBD]

### Space Apps judge, Visitor

- **Goals:** Check that the app meets the challenge requirements and that the science holds up.
- **Pain points:** Needs to open the app from a public link quickly and see the NISAR data named and dated.
- **Tech comfort:** [TBD]
- **Main device:** [TBD]

### Project owner, Maintainer

- **Goals:** Process new NISAR pairs, add sites, and publish updates.
- **Pain points:** Beginner in Python and radar data; large downloads; Colab sessions reset.
- **Tech comfort:** Medium: beginner in Python and radar data (brief §7)
- **Main device:** Laptop with Windows, Google Colab and VS Code (brief §7)

## 4. User Roles and Permissions

| Role | Can do | Cannot do |
| --- | --- | --- |
| Visitor (residents, officials, judges) | Open the app without logging in; view maps, layers, timeline, readouts, panels; search towns; switch sites | Change, upload or delete any data |
| Maintainer (project owner) | Run the processing pipeline; edit site configs, events, channels and validation records; publish data and code through the repository | Change data on the live site except by publishing through the repository |

## 5. Features and User Stories

### F-01: Interactive map

**Priority:** Must
**Description:** A map of the site with town borders and the danger zone, so visitors can find their area (R1).

#### US-001: View the site map

As a visitor, I want to open the app and see a map of the Mayon area with town borders and the danger zone, so that I can find my area.

**Acceptance criteria**

- **US-001/AC-1:** Given the app loads the Mayon site, when the map appears, then it is centered on the site's center point at its default zoom and shows town borders, town names, the coastline, and a 6 km ring around the summit labeled "Permanent Danger Zone (6 km)".
- **US-001/AC-2:** Given background map imagery fails to load, when the map appears, then town borders, the coastline and the danger-zone ring still show and the notice "Background map unavailable" appears.

#### US-002: Pan and zoom

As a visitor, I want to pan and zoom the map, so that I can look closely at my town and its channels.

**Acceptance criteria**

- **US-002/AC-1:** Given the map is shown, when the visitor drags, pinches or scrolls, then the map moves or zooms and every layer stays aligned with the town borders.
- **US-002/AC-2:** Given the map is at the site's minimum zoom, when the visitor zooms out further, then the zoom level stays at the minimum.

### F-02: Place readout

**Priority:** Must
**Description:** Search a town or tap the map to get plain-language facts about that spot (R1, R8).

#### US-003: Find a town

As a visitor, I want to type my town's name, so that the map jumps to it.

**Acceptance criteria**

- **US-003/AC-1:** Given the town list is loaded, when the visitor types at least 2 letters (for example "Tab") and picks "Tabaco City" from the suggestions, then the map centers on Tabaco City and its readout opens.
- **US-003/AC-2:** Given the visitor types a name that matches no town and submits, then "No town found. Try another name or tap the map." appears and the map does not move.

#### US-004: Read a tapped spot

As a visitor, I want to tap a spot and see what the radar found there, so that I understand my area in plain words.

**Acceptance criteria**

- **US-004/AC-1:** Given a pair is selected, when the visitor taps a point inside the site, then a card shows the town name, the distance to the summit in km with 1 decimal, whether the point is inside the danger zone, and the new-material result with its confidence (none, low or high).
- **US-004/AC-2:** Given the tapped point has no radar value, when the card opens, then it says "No radar data here" and gives the reason: outside radar coverage, sea, or flagged invalid by the product.
- **US-004/AC-3:** Given the tapped point is within the danger-zone radius, when the card opens, then it shows "Inside the Permanent Danger Zone. Entry is not allowed."

### F-03: Pass timeline

**Priority:** Must
**Description:** Step through every same-track 12-day pair since June 2026, including the July 14, 2026 pyroclastic flow and the Oct 30, 2026 eruption (R4).

#### US-005: Step through passes

As a visitor, I want to step through every pair of passes, so that I can see how changes built up over time.

**Acceptance criteria**

- **US-005/AC-1:** Given a site has published pairs, when the visitor picks a pair on the timeline, then the map shows that pair's layers and the label shows the before and after dates in the site's local time zone, the track, the frame and the orbit direction.
- **US-005/AC-2:** Given the newest pair is selected, when the visitor presses "Next", then the selection does not change and "This is the latest pass" appears.
- **US-005/AC-3:** Given a recorded event falls between a pair's before and after dates, when the timeline shows, then that pair is marked with the event's name.

#### US-006: Open on the latest pass

As a visitor, I want the app to open on the newest pair, so that I see the most recent change first.

**Acceptance criteria**

- **US-006/AC-1:** Given a site has published pairs, when the site loads, then the selected pair is the one with the latest after date.
- **US-006/AC-2:** Given a site has no published pairs, when it loads, then "No radar passes processed yet for this site" appears and only the base map layers show.

### F-04: Before/after view

**Priority:** Must
**Description:** Swipe between the radar images of the two dates (R4, R5).

#### US-007: Compare before and after

As a visitor, I want to swipe between the radar images of the two dates, so that I can see the change with my own eyes.

**Acceptance criteria**

- **US-007/AC-1:** Given a pair is selected, when the visitor opens Compare and drags the divider, then the before radar image shows on the left and the after image on the right, each labeled with its date.
- **US-007/AC-2:** Given the before or after image is missing for the pair, when the visitor opens Compare, then "Before/after images not available for this pair" appears and the map view stays as it was.

### F-05: New-material layer

**Priority:** Must
**Description:** Areas where NISAR GCOV brightness change and coherence loss agree, with legend, units and confidence (R2, R3, R5, R6).

#### US-008: See new material

As a visitor, I want to see where new material was detected between two passes, so that I know where the volcano put fresh ash, rock or lava.

**Acceptance criteria**

- **US-008/AC-1:** Given a pair is selected and the new-material layer is on, when the map shows, then areas classed as new material show in the layer colors, and the legend names each class, its confidence level and units, plus the total detected area in km² with 2 decimals.
- **US-008/AC-2:** Given the pair's detected area is 0 km², when the layer is on, then no shading shows and "No new material detected between <before date> and <after date>" appears.
- **US-008/AC-3:** Given a pixel where only one of the two signals passes its threshold, or a pair with no coherence data, when the layer shows, then that pixel is shown as low confidence, never high.

#### US-009: Process a pair

As the maintainer, I want to run the pipeline for two passes, so that I get the new-material layer ready to publish.

**Acceptance criteria**

- **US-009/AC-1:** Given two GCOV products from the same track, frame and orbit direction, when the maintainer runs the pipeline for that pair, then it writes the pair's layer files and a pair record with status "ready", the granule IDs used, and the detected areas in km².
- **US-009/AC-2:** Given the two passes differ in track, frame or orbit direction, when the pipeline runs, then it stops with "Passes are not from the same track, frame and direction" and writes no files.
- **US-009/AC-3:** Given a needed GCOV product isn't available on ASF yet, when the pipeline runs, then it stops with "Product not available yet: <granule_id>" and writes no files.

### F-06: Ground-movement layer

**Priority:** Could
**Description:** Line-of-sight movement in cm from NISAR GUNW, labeled "within the noise" when no clear signal shows.

#### US-010: See ground movement

As a visitor, I want to see whether the ground moved toward or away from the satellite, so that I know if my area shifted.

**Acceptance criteria**

- **US-010/AC-1:** Given a pair with a movement layer, when the visitor turns it on, then movement shows in cm on a two-color scale, with pixels of coherence below 0.3 hidden.
- **US-010/AC-2:** Given the movement at a tapped point is smaller than the pair's noise level, when the card opens, then it says "Within the noise: no clear movement".

### F-07: Flood layer

**Priority:** Could
**Description:** Open water in the Albay lowlands after typhoons, using the same change engine.

#### US-011: See flooded areas

As a visitor, I want to see land that became open water after a typhoon, so that I know which areas flooded.

**Acceptance criteria**

- **US-011/AC-1:** Given a lowlands pair with a flood layer, when the visitor turns it on, then land that became open water between the two dates shows, with its area in km².
- **US-011/AC-2:** Given a pixel is sea, when the flood layer is computed, then it is never shown or counted as new water.

### F-08: "What am I looking at?" panel

**Priority:** Must
**Description:** How radar sees, what the colors mean, confidence levels, limitations, and that official warnings come from PHIVOLCS and LGUs (R8).

#### US-012: Understand the map

As a visitor, I want a short explanation of the map, so that I read it correctly and know where official warnings come from.

**Acceptance criteria**

- **US-012/AC-1:** Given the visitor opens "What am I looking at?", when the panel shows, then it explains how radar sees, what each color means, the confidence levels, and at least 3 limitations, with a link to PHIVOLCS.
- **US-012/AC-2:** Given any radar layer is on screen, when the visitor looks at the main screen, then the line "This is not an official warning. Follow PHIVOLCS and your LGU." is visible without opening a panel.
- **US-012/AC-3:** Given any screen of the app, when its text is reviewed, then no text states that a lahar, eruption or flood will happen.

### F-09: Data sources panel

**Priority:** Must
**Description:** Product name, granule ID, acquisition dates, provisional status and link for every layer (R2, R3).

#### US-013: Check the data sources

As a visitor or judge, I want to see exactly which NISAR products made each layer, so that I can check the data.

**Acceptance criteria**

- **US-013/AC-1:** Given a pair is selected, when the visitor opens "Data sources", then each radar layer lists its product type, granule IDs, acquisition dates, maturity (for example PROVISIONAL) and a link to the product on ASF.
- **US-013/AC-2:** Given context data is used (background map, borders, coastline, channels), when the panel shows, then it is listed separately under "Context data" with its source and license.

### F-10: Second showcase site

**Priority:** Must
**Description:** The same new-material engine run on one site on another continent (R7).

#### US-014: Switch sites

As a visitor, I want to switch between Mayon and the second site, so that I can see the same method elsewhere.

**Acceptance criteria**

- **US-014/AC-1:** Given 2 published sites, when the visitor picks the other site, then the map moves to that site and shows its timeline and latest pair.
- **US-014/AC-2:** Given the chosen site's data fails to load, when the visitor picks it, then "Couldn't load <site name>. Try again." appears with a Retry button and the previous site stays on screen.

#### US-015: Add a site without code changes

As the maintainer, I want to add a site by writing one config file, so that the same engine runs anywhere without code changes.

**Acceptance criteria**

- **US-015/AC-1:** Given a new site config file with valid bounds, when the maintainer runs the pipeline and publishes, then the site appears in the site list with no code changes.
- **US-015/AC-2:** Given a site config where west ≥ east or south ≥ north, when the pipeline runs, then it stops with "Invalid bounds in site config: <file>".

### F-11: Public app and code

**Priority:** Must
**Description:** A public link and a public code repository that judges can open.

#### US-016: Open the public app

As a judge, I want to open the app and its code from public links without logging in, so that I can review the project.

**Acceptance criteria**

- **US-016/AC-1:** Given the public URL, when a judge opens it in a private browser window, then the app loads with no login prompt.
- **US-016/AC-2:** Given a path that doesn't exist on the site, when it's opened, then a "Page not found" page shows with a link back to the map.
- **US-016/AC-3:** Given the public repository URL, when it's opened while signed out of GitHub, then the code and README are visible.

### F-12: Validation check

**Priority:** Should
**Description:** At least one result compared with an independent source, such as the gullies named in PHIVOLCS bulletins for the same dates.

#### US-017: See how a result was checked

As a visitor or judge, I want to see a result compared with an independent source, so that I can judge whether to trust it.

**Acceptance criteria**

- **US-017/AC-1:** Given a pair with a validation record, when the visitor opens "How we checked this", then a table lists each place from the independent source, whether the source reported activity there, whether the app detected new material there (yes, no, or not visible to radar), and the source's name, date and link.
- **US-017/AC-2:** Given a pair with no validation record, when the visitor opens the panel, then "Not yet checked against an independent source" appears.

### F-13: Mobile-friendly, color-blind-safe design

**Priority:** Should
**Description:** Readable on a phone, with a color-blind-safe palette.

#### US-018: Use it on a phone

As a resident, I want the app to work on my phone and be readable without relying on color alone, so that everyone can use it.

**Acceptance criteria**

- **US-018/AC-1:** Given a screen 360 px wide, when the app opens, then every control is reachable without horizontal scrolling and every tap target is at least 44 × 44 px.
- **US-018/AC-2:** Given the layer colors are viewed through a red-green color-blindness simulation, when the legend and map are checked, then every class stays distinguishable and each class also has a text label.

### F-14: Point time series

**Priority:** Could
**Description:** Chart of change at a tapped point across every pass since June 2026.

#### US-019: See a point's history

As a visitor, I want to see how a spot changed across every pass, so that I can tell one-off changes from steady ones.

**Acceptance criteria**

- **US-019/AC-1:** Given a site with at least 2 pairs, when the visitor taps a point and opens History, then a chart shows that point's value for every pair by date.
- **US-019/AC-2:** Given a site with only 1 pair, when the visitor opens History, then "History needs at least two passes" appears.

### F-15: Past-years water comparison

**Priority:** Removed (brief v0.2)
**Description:** Removed in brief v0.2 and moved to Out of Scope. No stories.

### F-16: Filipino and Bikol language option

**Priority:** Could
**Description:** Switch the app's text to Filipino or Bikol.

#### US-020: Use the app in Filipino or Bikol

As a resident, I want the app in Filipino or Bikol, so that I understand it fully.

**Acceptance criteria**

- **US-020/AC-1:** Given the language menu, when the visitor picks Filipino, then all interface text shows in Filipino and data values don't change.
- **US-020/AC-2:** Given a text with no translation, when it shows, then the English text appears instead of a blank.

### F-17: Automatic updates

**Priority:** Could
**Description:** A scheduled pipeline that finds and processes new NISAR passes.

#### US-021: Update automatically

As the maintainer, I want new passes processed on a schedule, so that the app stays current without manual runs.

**Acceptance criteria**

- **US-021/AC-1:** Given a scheduled run, when a new pass is available for a configured site, then the new pair is processed and published without manual steps.
- **US-021/AC-2:** Given a scheduled run fails, when it ends, then nothing new is published and the maintainer is notified.

### F-18: More change types and places

**Priority:** Could
**Description:** Farming shifts, wetland loss and earthquakes at other sites.

#### US-022: See other change types

As a visitor, I want to see other kinds of surface change at other sites, so that I can explore beyond volcanoes.

**Acceptance criteria**

- **US-022/AC-1:** Given a site configured with another change type, when the visitor opens its layers, then that layer shows with its own legend and units.
- **US-022/AC-2:** Given a change type is not configured for a site, when the visitor opens that site's layers, then the change type is not listed.

### F-19: Channels and towns

**Priority:** Must
**Description:** Draw the PHIVOLCS-named channels that drain Mayon and the towns along each; tapping a changed area shows which channel it's in (R8).

#### US-023: See channels and towns

As a visitor, I want to see the channels that drain Mayon and the towns along each, so that I can tell which channel new material sits in.

**Acceptance criteria**

- **US-023/AC-1:** Given the channel layer is on, when the map shows, then each named channel shows as a line with its name, and tapping a channel lists the towns it passes through.
- **US-023/AC-2:** Given the visitor taps a new-material area, when it lies within the channel distance [TBD] of a named channel, then the card says "New material detected in or near <channel name>"; otherwise it says "Not in a named channel".
- **US-023/AC-3:** Given the channel layer is on, when the visitor checks the legend or Data sources, then the source of the channel names and of the channel lines is shown.

## 6. Functional Requirements

| FR-ID | Requirement | F-ID | US-ID |
| --- | --- | --- | --- |
| FR-001 | The system shall center the map on the selected site's center point at the site's default zoom. | F-01 | US-001 |
| FR-002 | The system shall draw town borders and town names for the selected site. | F-01 | US-001 |
| FR-003 | The system shall draw the coastline from the app's own land data, not from background imagery. | F-01 | US-001 |
| FR-004 | The system shall draw a ring of the site's danger-zone radius around the summit, labeled with the site's danger-zone label, when the site defines one. | F-01 | US-001 |
| FR-005 | The system shall show "Background map unavailable" when background imagery fails to load, while keeping borders, coastline and the danger-zone ring visible. | F-01 | US-001 |
| FR-006 | The system shall let the visitor pan and zoom only between the site's minimum and maximum zoom levels. | F-01 | US-002 |
| FR-007 | The system shall suggest matching town names once the visitor has typed at least 2 letters. | F-02 | US-003 |
| FR-008 | The system shall center the map on a chosen town and open that town's readout. | F-02 | US-003 |
| FR-009 | The system shall show "No town found. Try another name or tap the map." when a submitted name matches no town. | F-02 | US-003 |
| FR-010 | The system shall show, for a tapped point, the town name, distance to the summit in km with 1 decimal, danger-zone status, and the new-material class with its confidence. | F-02 | US-004 |
| FR-011 | The system shall show "No radar data here" with one of three reasons (outside radar coverage, sea, flagged invalid by the product) when the tapped point has no valid value. | F-02 | US-004 |
| FR-012 | The system shall show "Inside the Permanent Danger Zone. Entry is not allowed." when a tapped point is within the danger-zone radius. | F-02 | US-004 |
| FR-013 | The system shall list every published pair of the selected site on the timeline, in order of after date. | F-03 | US-005 |
| FR-014 | The system shall label the selected pair with its before and after dates in the site's local time zone, its track, its frame and its orbit direction. | F-03 | US-005 |
| FR-015 | The system shall keep the newest pair selected and show "This is the latest pass" when the visitor presses Next on it. | F-03 | US-005 |
| FR-016 | The system shall mark each pair whose date range contains a recorded event with that event's name. | F-03 | US-005 |
| FR-017 | The system shall select the published pair with the latest after date when a site loads. | F-03 | US-006 |
| FR-018 | The system shall show "No radar passes processed yet for this site" and only base layers when a site has no published pairs. | F-03 | US-006 |
| FR-019 | The system shall show the before and after radar brightness images on either side of a draggable divider, each labeled with its date. | F-04 | US-007 |
| FR-020 | The system shall show "Before/after images not available for this pair" and leave the map unchanged when either image is missing. | F-04 | US-007 |
| FR-021 | The pipeline shall compute brightness change in dB as 10 × log10(after / before) from speckle-filtered GCOV backscatter. | F-05 | US-009 |
| FR-022 | The pipeline shall compute coherence loss as the coherence of the previous pair on the same track minus the coherence of the current pair, only when both pairs span the same number of days. Otherwise it shall treat the pair as having no coherence data (FR-030). | F-05 | US-009 |
| FR-023 | The pipeline shall class a pixel as high confidence when brightness change and coherence loss both pass their thresholds, low confidence when only one passes or no coherence data exists, and none otherwise. | F-05 | US-008 |
| FR-024 | The pipeline shall mark sea pixels, pixels outside radar coverage, and pixels flagged invalid by the product as no data, each with its reason. | F-05 | US-008 |
| FR-025 | The system shall show the new-material layer with a legend naming each class, its confidence and units, and the total detected area in km² with 2 decimals. | F-05 | US-008 |
| FR-026 | The system shall show "No new material detected between <before date> and <after date>" when a pair's detected area is 0 km². | F-05 | US-008 |
| FR-027 | The pipeline shall stop with "Passes are not from the same track, frame and direction" and write no files when two passes differ in track, frame or orbit direction. | F-05 | US-009 |
| FR-028 | The pipeline shall stop with "Product not available yet: <granule_id>" and write no files when a needed GCOV product can't be found on ASF. | F-05 | US-009 |
| FR-029 | The pipeline shall write, for each processed pair, a pair record with status "ready", the granule IDs used and the detected areas in km². | F-05 | US-009 |
| FR-030 | The pipeline shall still process a pair when its GUNW product is unavailable, or when FR-022 excludes its baseline, classing every detection as low confidence and recording that no coherence data was used. | F-05 | US-008 |
| FR-031 | The system shall show line-of-sight movement in cm on a two-color scale, hiding pixels with coherence below 0.3. | F-06 | US-010 |
| FR-032 | The pipeline shall remove a best-fit plane from movement using valid land more than 6 km from the summit and record the remaining noise in cm. | F-06 | US-010 |
| FR-033 | The system shall show "Within the noise: no clear movement" when movement at a tapped point is smaller than the pair's noise level. | F-06 | US-010 |
| FR-034 | The system shall show land that became open water between two dates, with its area in km². | F-07 | US-011 |
| FR-035 | The pipeline shall never count sea pixels as new water. | F-07 | US-011 |
| FR-036 | The system shall provide a "What am I looking at?" panel explaining how radar sees, what each color means, the confidence levels and at least 3 limitations, with a link to PHIVOLCS. | F-08 | US-012 |
| FR-037 | The system shall show "This is not an official warning. Follow PHIVOLCS and your LGU." on the main screen whenever a radar layer is shown. | F-08 | US-012 |
| FR-038 | The system shall not display any text stating that a lahar, eruption or flood will happen. | F-08 | US-012 |
| FR-039 | The system shall list, for each radar layer of the selected pair, its product type, granule IDs, acquisition dates, maturity and a link to ASF. | F-09 | US-013 |
| FR-040 | The system shall list context data separately under "Context data", each with its source and license. | F-09 | US-013 |
| FR-041 | The system shall let the visitor switch between published sites. | F-10 | US-014 |
| FR-042 | The system shall show "Couldn't load <site name>. Try again." with a Retry button, keeping the previous site shown, when a site's data fails to load. | F-10 | US-014 |
| FR-043 | The pipeline shall read each site's settings from one config file per site, with no code changes per site. | F-10 | US-015 |
| FR-044 | The pipeline shall stop with "Invalid bounds in site config: <file>" when a site config has west ≥ east or south ≥ north. | F-10 | US-015 |
| FR-045 | The system shall be reachable at a public URL with no login. | F-11 | US-016 |
| FR-046 | The system shall show a "Page not found" page with a link back to the map for unknown paths. | F-11 | US-016 |
| FR-047 | The system's code shall be in a public repository with a README. | F-11 | US-016 |
| FR-048 | The system shall show a pair's validation table when a validation record exists, and "Not yet checked against an independent source" otherwise. | F-12 | US-017 |
| FR-049 | The system shall fit screens 360 px wide without horizontal scrolling, with every tap target at least 44 × 44 px. | F-13 | US-018 |
| FR-050 | The system shall use color-blind-safe palettes and give every color class a text label. | F-13 | US-018 |
| FR-051 | The system shall chart the value at a tapped point across all pairs of the site, or show "History needs at least two passes". | F-14 | US-019 |
| FR-052 | The system shall switch interface text among English, Filipino and Bikol, falling back to English when a translation is missing. | F-16 | US-020 |
| FR-053 | The pipeline shall check configured sites for new passes on a schedule and process and publish new pairs. | F-17 | US-021 |
| FR-054 | The pipeline shall publish nothing and notify the maintainer when a scheduled run fails. | F-17 | US-021 |
| FR-055 | The system shall show each additional change-type layer configured for a site with its own legend and units, and list only configured types. | F-18 | US-022 |
| FR-056 | The system shall draw each named channel as a labeled line and list the towns it passes through when the channel is tapped. | F-19 | US-023 |
| FR-057 | The system shall name the channel within the channel distance of a tapped new-material area, or say "Not in a named channel". | F-19 | US-023 |
| FR-058 | The system shall show the source of the channel names and of the channel lines. | F-19 | US-023 |
| FR-059 | The system shall show visitors only pairs whose status is "published". | F-03 | US-006 |

## 7. Non-Functional Requirements

| NFR-ID | Category | Requirement | Measure |
| --- | --- | --- | --- |
| NFR-001 | Performance | The first view (map plus latest pair) loads quickly on a phone; a tap readout appears quickly. | [TBD]. Suggestion: first view ≤ 5 s on Chrome DevTools "Fast 4G" throttling; ≤ 5 MB downloaded for the first view; readout ≤ 200 ms after a tap. |
| NFR-002 | Security | No secrets in the repository or the published site; the site is served only over HTTPS. | 0 secrets found by a secret scan before each release; 100% of site requests over HTTPS. |
| NFR-003 | Availability | The public site stays reachable during judging and after. | [TBD]. Suggestion: 99% monthly uptime, depending on the host (verify). |
| NFR-004 | Usability and Accessibility | Text is readable and controls are usable on phones; non-experts read the map correctly. | Text contrast ≥ 4.5:1 (WCAG 2.1 AA); tap targets ≥ 44 × 44 px; ≥ 7 of 10 testers explain the map correctly (G-03). |
| NFR-005 | Compatibility | Works on common phone and desktop browsers. | [TBD]. Suggestion: latest 2 major versions of Chrome (Android, Windows), Safari (iOS), Edge and Firefox; screen widths 360–1920 px. |
| NFR-006 | Scalability | Handles visitor spikes after an eruption without changes. | [TBD]. Suggestion: 1,000 visits/day with no code or hosting change (verify host bandwidth limits). |
| NFR-007 | Data Privacy | No personal data is collected or stored. | 0 personal-data fields stored; 0 cookies set; tapped coordinates never sent to any server. |
| NFR-008 | Data quality | Every radar value shown is traceable and labeled. | 100% of radar layers show acquisition dates, units, maturity and confidence. |
| NFR-009 | Data freshness | New pairs are published soon after the products appear on ASF. | [TBD]. Suggestion: ≤ 48 h after both products of a pair appear on ASF, during the MVP. |

## 8. Integrations and Dependencies

| Integration | Purpose | Needed for (F-IDs) |
| --- | --- | --- |
| ASF DAAC (Vertex, ASF Search API, `asf_search`) | Find and download NISAR GCOV and GUNW products; product links for visitors | F-03, F-05, F-06, F-07, F-09, F-17 |
| NASA Earthdata Login | Authentication for downloading NISAR data (maintainer only) | F-05, F-06, F-07, F-17 |
| Background map imagery (Esri tiles, per the progress notes) | Visual base map under the radar layers (terms of use: verify) | F-01 |
| Albay municipal boundaries (NAMRIA/PSA via OCHA COD-AB, CC BY-IGO, through GitHub `faeldon/philippines-json-maps`) | Town borders, town names, land mask and coastline for Mayon | F-01, F-02, F-05 |
| PHIVOLCS bulletins (read by the maintainer) | Channel names, event dates, validation records | F-03, F-12, F-19 |
| Channel line data [TBD] | Lines for the named channels | F-19 |
| Boundary data for the second site [TBD] | Borders and land mask outside the Philippines | F-10 |
| Public code hosting and static web hosting (GitHub; host choice in step 04) | Public repository and public link | F-11 |
| Google Colab | Where the maintainer runs the pipeline | F-05, F-10 |

## 9. Release Criteria

- [ ] All Must features meet their acceptance criteria
- [ ] Challenge requirements R1–R8 are visibly met in the app (G-01)
- [ ] At least 1 post-eruption pair is published (G-02)
- [ ] The disclaimer line shows whenever a radar layer is on screen (US-012/AC-2)
- [ ] A secret scan finds 0 secrets (NFR-002)
- [ ] The public link and repository open in a private browser window (US-016)

## 10. Suggestions

- Suggestion: Barangay-level borders and search. Residents often think in barangays, not towns; it needs a barangay boundary source.
- Suggestion: A "Use my location" button that works only inside the browser and sends nothing to a server, so residents find their spot faster without breaking NFR-007.
- Suggestion: Shareable links that open a specific site, pair and spot, so officials can send exactly what they're looking at.
- Suggestion: An optical-image toggle for clear days, to show judges that radar sees through clouds and ash (listed as "Should" in the challenge checklist).

## 11. Assumptions

- Visitors don't need accounts; every visitor has the same read-only permissions.
- The maintainer is the only person who processes and publishes data.
- Pairs are consecutive passes on the same track, usually 12 days apart. A missed pass makes the gap longer, as on track 111 from 2026-07-27 to 2026-08-20 (24 days).
- The first pair on each track has no previous pair, so its coherence loss can't be computed and its detections are low confidence at most.
- Thresholds for brightness change and coherence loss are fixed before the eruption data is examined (brief Open Question 7).

## 12. Open Questions

| # | Question | Affects |
| --- | --- | --- |
| 1 | How comfortable with technology are residents, officials and judges, and which device does each mainly use? | §3 Personas |
| 2 | What brightness-change and coherence-loss thresholds count as new material? | FR-023, US-008 |
| 3 | What distance from a channel counts as "in or near" it? | US-023/AC-2, FR-057 |
| 4 | Where do the channel lines come from (for example OpenStreetMap waterways, or traced by hand)? | F-19, §8 |
| 5 | Which second site, and which boundary data for it? | F-10, §8 |
| 6 | What are the performance, availability, compatibility and scalability targets? (Suggestions given in §7.) | NFR-001, NFR-003, NFR-005, NFR-006 |
| 7 | What is the data-freshness target? | NFR-009 |

## 13. Conflicts with Earlier Documents

- **Brief v0.3, §5, F-05:** says brightness change and coherence loss "agree between two passes". Measuring coherence loss needs the coherence of the previous pair as a baseline, which means three passes. Proposed fix: change F-05's description to "Areas where NISAR GCOV brightness change and GUNW coherence loss agree, with legend, units and confidence". FR-022 and FR-030 follow this.

## 14. Revision History

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-31 | First draft |

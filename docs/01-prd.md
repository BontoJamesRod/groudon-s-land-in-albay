# PRD: Mayon Radar Watch

| Version | Status | Last updated | Based on |
| --- | --- | --- | --- |
| 0.2 | Draft | 2026-11-01 | 00-project-brief.md v0.4 (Draft) |

## 1. Overview

Mayon Radar Watch is a public web app that watches how Mayon's river channels change between NISAR satellite passes. It compares NASA–ISRO NISAR radar images, usually taken 12 days apart, maps possible fresh ash, rock and lava deposits, and shows how much changed along each channel that drains the volcano. It is first built as an entry for the NASA Space Apps Challenge 2026 "Dancing with the SARs" challenge, and the same engine runs on a second site on another continent.

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

- **US-001/AC-1:** Given the app loads the Mayon site, when the map appears, then it is centered on the site's center point at its default zoom, or one zoom step further out on a short phone screen where the danger-zone ring wouldn't clear the map credits, and shows town borders, town names, the coastline, and a 6 km ring around the summit labeled "Permanent Danger Zone (6 km)".
- **US-001/AC-2:** Given background map imagery fails to load, when the map appears, then town borders, the coastline and the danger-zone ring still show and the notice "Background map unavailable" appears.
- **US-001/AC-3:** Given the site's land file stops at the site's edge, when the map appears, then no coastline or town border is drawn along that edge.

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
- **US-004/AC-4:** Given a site whose config sets a reach distance and a tapped point beyond it, when the card opens, then it says "Not checked: this map only looks within 10 km of the summit" (with the site's distance) instead of a new-material result.
- **US-004/AC-5:** Given a site with no summit, such as Panama, when the card opens, then it leaves out the distance and danger-zone lines and still shows the town and the new-material result.

### F-03: Pass timeline

**Priority:** Must
**Description:** Step through every same-track 12-day pair since June 2026, including the July 14, 2026 pyroclastic flow and the Oct 30, 2026 eruption (R4).

#### US-005: Step through passes

As a visitor, I want to step through every pair of passes, so that I can see how changes built up over time.

**Acceptance criteria**

- **US-005/AC-1:** Given a site has published pairs, when the visitor picks a pair on the timeline, then the map shows that pair's layers and the label shows the before and after dates in the site's local time zone, the track, the frame and the orbit direction.
- **US-005/AC-2:** Given the newest pair is selected, when the visitor presses "Next", then the selection does not change and "This is the latest pass" appears.
- **US-005/AC-3:** Given a recorded event falls between a pair's before and after dates, when the timeline shows, then that pair is marked with the event's name.
- **US-005/AC-4:** Given a pair whose gap isn't 12 days, when the timeline shows, then that pair is dimmed and has a short note such as "24-day gap, not comparable".

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
**Description:** Areas where NISAR GCOV brightness change shows new material. GUNW coherence loss only raises a flagged area to high confidence and never adds area. Shown with legend, units and confidence (R2, R3, R5, R6).

#### US-008: See new material

As a visitor, I want to see where new material was detected between two passes, so that I know where the volcano put fresh ash, rock or lava.

**Acceptance criteria**

- **US-008/AC-1:** Given a pair is selected and the new-material layer is on, when the map shows, then areas classed as new material show in the layer colors, and the legend names each class, its confidence level and units, plus the total detected area in km² with 2 decimals.
- **US-008/AC-2:** Given the pair's detected area is 0 km², when the layer is on, then no shading shows and "No new material detected between <before date> and <after date>" appears.
- **US-008/AC-3:** Given a pixel whose brightness change passes its threshold while its coherence loss doesn't, or a flagged pixel in a pair with no coherence data, when the layer shows, then that pixel is shown as low confidence, never high.
- **US-008/AC-4:** Given a pixel where only coherence loss passes its threshold, when the layer shows, then that pixel isn't shaded and adds no area.
- **US-008/AC-5:** Given a site whose config sets a reach distance, when the layer shows, then nothing is shaded beyond that distance from the summit, the limit is drawn as a ring, and the legend states it.

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

- **US-010/AC-1:** Given a pair with a movement layer, when the visitor turns it on, then movement shows in cm on a two-color scale, with pixels hidden where coherence is below the mask set in the site config.
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
- **US-012/AC-4:** Given any screen of the app or any published file, when its text is reviewed, then no change is labeled illegal or unpermitted.

### F-09: Data sources panel

**Priority:** Must
**Description:** Product name, granule ID, acquisition dates, provisional status and link for every layer (R2, R3).

#### US-013: Check the data sources

As a visitor or judge, I want to see exactly which NISAR products made each layer, so that I can check the data.

**Acceptance criteria**

- **US-013/AC-1:** Given a pair is selected, when the visitor opens "Data sources", then each radar layer lists its product type, granule IDs, acquisition dates, maturity (for example PROVISIONAL) and a link to the product on ASF.
- **US-013/AC-2:** Given context data is used (background map, borders, coastline, channels), when the panel shows, then it is listed separately under "Context data" with its source and license.
- **US-013/AC-3:** Given a site is selected, when the visitor opens "Data sources" or reads the map credit, then only that site's sources and the shared ones are listed, and the map credit names that site's boundary source.

### F-10: Second showcase site

**Priority:** Must
**Description:** Two pairs on the Azuero Peninsula, Panama, a quiet pair and the earthquake pair, using the same engine and the plain change map, with no channels (R7).

#### US-014: Switch sites

As a visitor, I want to switch between Mayon and the second site, so that I can see the same method elsewhere.

**Acceptance criteria**

- **US-014/AC-1:** Given 2 published sites, when the visitor picks the other site, then the map moves to that site and shows its timeline and latest pair.
- **US-014/AC-2:** Given the chosen site's data fails to load, when the visitor picks it, then "Couldn't load <site name>. Try again." appears with a Retry button and the previous site stays on screen.
- **US-014/AC-3:** Given a site whose map shows change in general, such as Panama, when the visitor reads its map, card and help, then they say "change" instead of "new material", name that site's official source, and the earthquake pair is titled "Changed after the earthquake" and is never called landslides.

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
- **US-017/AC-3:** Given a pair with no validation record and a check note, when the visitor opens the panel, then the note appears instead, for example "Used as the 'before' comparison for the earthquake pair".

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
- **US-023/AC-2:** Given the visitor taps a new-material area, when it lies inside a named channel's strip, then the card says "New material detected in or near <channel name>"; otherwise it says "Not in a named channel on this map".
- **US-023/AC-3:** Given the channel layer is on, when the visitor checks the legend or Data sources, then the source of the channel names and of the channel lines is shown.

### F-20: Channel timeline

**Priority:** Must
**Description:** A list of the owner-confirmed channels, sorted by how much changed since the last pass. Each channel has one bar per radar pass showing the area flagged inside its channel strip, and opening a channel shows its strip on the map (R4, R8). Builds on F-19.

#### US-024: See which channels changed most

As a visitor, I want a list of Mayon's channels with the most changed first, so that I can see where to look after the latest pass.

**Acceptance criteria**

- **US-024/AC-1:** Given a site with confirmed channels and published pairs, when the visitor opens the channel list, then each confirmed channel shows with its flagged area in km² (3 decimals) for the latest pair, largest first, and channels with no radar data for that pair come last.
- **US-024/AC-2:** Given a site with no confirmed channels, when the visitor opens the channel list, then "No confirmed channels yet for this site" appears, and a site with no channel data shows no channel-list button.
- **US-024/AC-3:** Given the channel areas are still downloading or fail to load, when the list shows, then "Loading channel changes…" appears, or "Couldn't load channel changes. Try again." with a Retry button, and the map stays as it was.

#### US-025: Read one channel's timeline

As a visitor, I want to open a channel and see its change across every pass, so that I can tell a one-off change from a steady one.

**Acceptance criteria**

- **US-025/AC-1:** Given a channel in the list, when the visitor opens it, then one bar per published pair shows the flagged area in its strip in km² with 3 decimals, in order of after date, each labeled with its dates.
- **US-025/AC-2:** Given a channel is open, when the map shows, then that channel's strip is drawn on the map and the map fits it.
- **US-025/AC-3:** Given a pair with no valid radar value inside the channel's strip, when its bar would show, then the bar's place says "No radar data" instead of 0 km².
- **US-025/AC-4:** Given a pair whose gap isn't 12 days, when its bar shows, then the bar is dimmed and has a short note such as "24-day gap, not comparable".
- **US-025/AC-5:** Given a channel that continues past the reach distance, when it shows on the map, then that part is dashed and labeled "Not checked", and no bar counts it as zero change.
- **US-025/AC-6:** Given a channel view is open, when it opens or the map's pass changes, then the highlighted bar is the pass the map is showing, it's scrolled into view, and no other bar looks highlighted.

#### US-026: Compute channel areas

As the maintainer, I want the pipeline to compute each channel's flagged area for each pair, so that the browser only reads the results.

**Acceptance criteria**

- **US-026/AC-1:** Given a site config with a strip width and a confirmed channel, when the maintainer publishes a pair, then `channel_areas.json` has one row for that channel and pair, computed from the final rule's flagged grid inside the strip and within the reach distance.
- **US-026/AC-2:** Given a site with channels whose config has no strip width, when the pipeline runs, then it stops with "Channel strip width missing in site config: <file>".
- **US-026/AC-3:** Given a channel without a recorded confirmation, or an unconfirmed candidate from `pipeline/context/channel_name_candidates.geojson`, when the contract check runs on the published channel files, then it fails if that channel is in them.

### F-21: Brightness histogram

**Priority:** Must
**Description:** A small chart for the selected pair showing how the ground's brightness changed, with the flag line and the flagged tails marked. The flag line can't be moved.

#### US-027: See why a spot counted as changed

As a visitor, I want to see how much the ground's brightness changed and where the flag line falls, so that I understand why some spots are flagged.

**Acceptance criteria**

- **US-027/AC-1:** Given a published pair, when the maintainer publishes it, then the pair has a file with the distribution of brightness change for checked land inside the reach distance, in fixed bins, whose flagged cells match the pair's value grid.
- **US-027/AC-2:** Given a pair is selected, when the visitor reads the panel, then a histogram shows the distribution, a line on each side at the pair's brightness threshold, the flagged tails shaded in the "possible new material" colour, and one plain sentence saying what it means.
- **US-027/AC-3:** Given the histogram file can't be loaded, when the panel shows, then the rest of the pair still works and the panel says "Brightness chart not available for this pair".
- **US-027/AC-4:** Given the visitor reads the help panel, then one line says why there's no way to move the flag line.
- **US-027/AC-5:** Given a channel is opened where the panel is on screen, when the histogram shows, then the channel's strip is drawn as a thin outline on the same chart.
### F-22: Field map design

**Priority:** Must
**Description:** The design the owner chose on 2026-11-02. A light relief map from elevation data, with its controls and channel list beside the map, or under it on a phone. It changes how the data looks and never the data. The owner approved Panama's relief on 2026-11-02, so both sites open on it.

#### US-028: Read the map outdoors

As a resident on a phone outdoors, I want a light, high-contrast map of the ground, so that I can read it in sunlight.

**Acceptance criteria**

- **US-028/AC-1:** Given a site with relief tiles, when the map opens, then the background is the relief, with no plain band at any edge at any zoom or pan the map allows, and the map credits the Copernicus DEM.
- **US-028/AC-2:** Given the relief tiles can't load, when the map shows, then the borders, coastline and ring stay visible and "Background map unavailable" shows (FR-005).
- **US-028/AC-3:** Given a site with channels, when it opens, then the channel list is open beside the map, or under it on a phone, without taking the keyboard focus. A phone shorter than 700 px opens on the map instead, with the list one tap away, because too little of the map would show.
- **US-028/AC-4:** Given a site config with no relief tiles, when it opens, then it uses the Satellite background with no switcher, and its map lines stay readable on it.

#### US-029: See small flagged spots

As a visitor, I want flagged change to stand out on the light map at any zoom, so that small spots aren't lost.

**Acceptance criteria**

- **US-029/AC-1:** Given a pair is shown, when a flagged cell would be smaller than the minimum mark on screen, then it's drawn at the minimum mark's size, with a darker edge, in its class colour.
- **US-029/AC-2:** Given marks are drawn, then there's one for each flagged cell in the pair's image, and no published image, grid or area changes.
- **US-029/AC-3:** Given the visitor reads the legend, then one line says that small spots are drawn larger than life so they can be seen, and that the areas don't change.
- **US-029/AC-4:** Given the layer toggle is off, or the compare view is open, then no marks show.

#### US-030: Picture a channel's area

As a resident, I want each channel's area compared with something familiar, so that I can picture its size.

**Acceptance criteria**

- **US-030/AC-1:** Given a channel area is shown in the list or the bars, then "about N basketball courts" is next to it, using 1 court = 28 × 15 m = 420 m², and the km² value stays.
- **US-030/AC-2:** Given an area of 0, or under half a court, then it reads "0 basketball courts" or "less than 1 basketball court", and a channel with no radar data shows no comparison.
- **US-030/AC-3:** Given the visitor reads the channel screens, then a note states the size of the court used.

### F-23: Map switcher

**Priority:** Must
**Description:** A small Relief or Satellite choice on the map. Relief is the default. Satellite shows real imagery under the same channels, radar marks, rings and labels.

#### US-031: Choose the background

As a visitor, I want to switch between a relief map and real imagery, so that I can recognise the ground.

**Acceptance criteria**

- **US-031/AC-1:** Given a site with both backgrounds, when the map shows, then "Relief" and "Satellite" buttons of at least 44 px are on it, usable by keyboard, with `aria-pressed` saying which is on, and Relief is on for a first visit.
- **US-031/AC-2:** Given the visitor chooses a background, when they reload or change site, then the same one is on. If the browser's storage can't be used, the app still works and opens on Relief.
- **US-031/AC-3:** Given Satellite is on, then channels, marks, rings and labels use the bright colours made for imagery, the imagery's credit shows, and no imagery is requested while Relief is on. Given Relief is on, then the Field map colours show and the imagery's credit doesn't.
- **US-031/AC-4:** Given the radar marks show, then they're visible on both backgrounds.
- **US-031/AC-5:** Given Satellite is on and its tiles are slow or fail, then the relief shows under it, a low-detail layer covers the view first, the map says "Loading satellite imagery: N tiles to go" until the sharp tiles are in, and after a run of failures it says "Satellite map unavailable. Showing the relief map."

## 6. Functional Requirements

| FR-ID | Requirement | F-ID | US-ID |
| --- | --- | --- | --- |
| FR-001 | The system shall center the map on the selected site's center point at the site's default zoom, or one zoom step further out on a short phone screen where the danger-zone ring wouldn't clear the map credits. | F-01 | US-001 |
| FR-002 | The system shall draw town borders and town names for the selected site. | F-01 | US-001 |
| FR-003 | The system shall draw the coastline from the app's own land data, not from background imagery, and shall not draw a coastline or town border where the data is only clipped to the site's edge. | F-01 | US-001 |
| FR-004 | The system shall draw a ring of the site's danger-zone radius around the summit, labeled with the site's danger-zone label, when the site defines one. On a phone the label sits inside the ring, so that town names keep their places at the opening view. | F-01 | US-001 |
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
| FR-023 | The pipeline shall flag a pixel by its brightness change alone. A flagged pixel is high confidence when coherence loss also passes its threshold, and low confidence when it doesn't or no coherence data exists; every other pixel is none. Coherence loss never adds area. The thresholds are final, set on 2026-11-01 before the post-eruption passes were opened, and their values live in the site config. | F-05 | US-008 |
| FR-024 | The pipeline shall mark sea pixels, pixels outside radar coverage, and pixels flagged invalid by the product as no data, each with its reason. | F-05 | US-008 |
| FR-025 | The system shall show the new-material layer with a legend naming each class, its confidence and units, and the total detected area in km² with 2 decimals. | F-05 | US-008 |
| FR-026 | The system shall show "No new material detected between <before date> and <after date>" when a pair's detected area is 0 km². | F-05 | US-008 |
| FR-027 | The pipeline shall stop with "Passes are not from the same track, frame and direction" and write no files when two passes differ in track, frame or orbit direction. | F-05 | US-009 |
| FR-028 | The pipeline shall stop with "Product not available yet: <granule_id>" and write no files when a needed GCOV product can't be found on ASF. | F-05 | US-009 |
| FR-029 | The pipeline shall write, for each processed pair, a pair record with status "ready", the granule IDs used and the detected areas in km². | F-05 | US-009 |
| FR-030 | The pipeline shall still process a pair when its GUNW product is unavailable, or when FR-022 excludes its baseline, classing every detection as low confidence and recording that no coherence data was used. | F-05 | US-008 |
| FR-031 | The system shall show line-of-sight movement in cm on a two-color scale, hiding pixels where coherence is below the mask set in the site config. | F-06 | US-010 |
| FR-032 | The pipeline shall remove a best-fit plane from movement using valid land more than 6 km from the summit and record the remaining noise in cm. | F-06 | US-010 |
| FR-033 | The system shall show "Within the noise: no clear movement" when movement at a tapped point is smaller than the pair's noise level. | F-06 | US-010 |
| FR-034 | The system shall show land that became open water between two dates, with its area in km². | F-07 | US-011 |
| FR-035 | The pipeline shall never count sea pixels as new water. | F-07 | US-011 |
| FR-036 | The system shall provide a "What am I looking at?" panel explaining how radar sees, what each color means, the confidence levels and at least 3 limitations, with a link to PHIVOLCS. | F-08 | US-012 |
| FR-037 | The system shall show "This is not an official warning. Follow PHIVOLCS and your LGU." on the main screen whenever a radar layer is shown. | F-08 | US-012 |
| FR-038 | The system shall not display any text stating that a lahar, eruption or flood will happen. | F-08 | US-012 |
| FR-039 | The system shall list, for each radar layer of the selected pair, its product type, granule IDs, acquisition dates, maturity and a link to ASF. | F-09 | US-013 |
| FR-040 | The system shall list context data separately under "Context data", each with its source and license, showing only the selected site's sources and the shared ones, with a radar source under "Radar data", and shall credit the selected site's boundary source on the map. | F-09 | US-013 |
| FR-041 | The system shall let the visitor switch between published sites. | F-10 | US-014 |
| FR-042 | The system shall show "Couldn't load <site name>. Try again." with a Retry button, keeping the previous site shown, when a site's data fails to load. | F-10 | US-014 |
| FR-043 | The pipeline shall read each site's settings from one config file per site, with no code changes per site. | F-10 | US-015 |
| FR-044 | The pipeline shall stop with "Invalid bounds in site config: <file>" when a site config has west ≥ east or south ≥ north. | F-10 | US-015 |
| FR-045 | The system shall be reachable at a public URL with no login. | F-11 | US-016 |
| FR-046 | The system shall show a "Page not found" page with a link back to the map for unknown paths. | F-11 | US-016 |
| FR-047 | The system's code shall be in a public repository with a README. | F-11 | US-016 |
| FR-048 | The system shall show a pair's validation table when a validation record exists, a note saying what the pair was used for when it has one and no record, and "Not yet checked against an independent source" otherwise. | F-12 | US-017 |
| FR-049 | The system shall fit screens 360 px wide without horizontal scrolling, with every tap target at least 44 × 44 px. | F-13 | US-018 |
| FR-050 | The system shall use color-blind-safe palettes and give every color class a text label. | F-13 | US-018 |
| FR-051 | The system shall chart the value at a tapped point across all pairs of the site, or show "History needs at least two passes". | F-14 | US-019 |
| FR-052 | The system shall switch interface text among English, Filipino and Bikol, falling back to English when a translation is missing. | F-16 | US-020 |
| FR-053 | The pipeline shall check configured sites for new passes on a schedule and process and publish new pairs. | F-17 | US-021 |
| FR-054 | The pipeline shall publish nothing and notify the maintainer when a scheduled run fails. | F-17 | US-021 |
| FR-055 | The system shall show each additional change-type layer configured for a site with its own legend and units, and list only configured types. | F-18 | US-022 |
| FR-056 | The system shall draw each named channel as a labeled line and list the towns it passes through when the channel is tapped. | F-19 | US-023 |
| FR-057 | The system shall name the channel whose strip holds a tapped new-material area, or say "Not in a named channel on this map". | F-19 | US-023 |
| FR-058 | The system shall show the source of the channel names and of the channel lines, and credit OpenStreetMap on the map while its lines are shown. | F-19 | US-023 |
| FR-059 | The system shall show visitors only pairs whose status is "published". | F-03 | US-006 |
| FR-060 | The site config shall set a reach distance from the summit. The pipeline shall not flag anything beyond it, the system shall draw and state the limit, and a tap beyond it shall say "Not checked: this map only looks within 10 km of the summit" (with the site's distance). | F-02, F-05 | US-004, US-008 |
| FR-061 | The system shall list a site's confirmed channels with the flagged area of the latest pair in km² with 3 decimals, largest first, ties by name, with channels that have no radar data for that pair last. | F-20 | US-024 |
| FR-062 | The system shall show, for an opened channel, one bar per published pair with the flagged area in its strip, in order of after date. | F-20 | US-025 |
| FR-063 | The system shall draw an opened channel's strip on the map and fit the map to it. | F-20 | US-025 |
| FR-064 | The pipeline shall compute each channel's flagged area per pair from the final rule's flagged grid, inside a strip of the width set in the site config (measured on each side of the line) and within the reach distance (FR-060), and shall stop with "Channel strip width missing in site config: <file>" when a site with channels has no width. The browser shall never compute these areas. | F-20 | US-026 |
| FR-065 | The system shall show and publish only channels whose line the owner has confirmed, with the source and the confirmation recorded in the data. Unconfirmed candidates shall never be drawn or listed as channels; a validation may cite such a name as a place. | F-19, F-20 | US-023, US-026 |
| FR-066 | The system shall dim a pair whose gap isn't 12 days and show a short note such as "24-day gap, not comparable", on the channel timeline and on the pass timeline. | F-03, F-20 | US-005, US-025 |
| FR-067 | The system shall show the channel list's empty, loading and error states, and "No radar data" for a pair with no valid radar value in a channel's strip. | F-20 | US-024, US-025 |
| FR-068 | The system shall never label any change as illegal or unpermitted. | F-08 | US-012 |
| FR-069 | The system shall leave the distance and danger-zone lines out of the readout for a site with no summit. | F-02, F-10 | US-004 |
| FR-070 | The system shall show a site's own wording for its change layer, limits and official source when its config sets one, and shall title the Panama earthquake pair "Changed after the earthquake", never landslides. | F-10 | US-014 |
| FR-071 | The system shall draw the part of a channel past the reach distance (FR-060) as "Not checked", and shall never count that part or show it as zero change. | F-20 | US-025 |
| FR-072 | The pipeline shall write, for each published pair, the distribution of brightness change in dB for checked land inside the reach distance (FR-060), in fixed bins, with the flagged cells and their share, matching the pair's value grid. | F-21 | US-027 |
| FR-073 | The system shall show that distribution as a histogram for the selected pair, with a line on each side at the pair's brightness threshold, the flagged tails shaded in the "possible new material" colour, and one plain sentence. | F-21 | US-027 |
| FR-074 | The system shall not let a visitor move the flag line, and the help panel shall say why. | F-21 | US-027 |
| FR-075 | The pipeline shall write the same distribution for each channel's strip, and the system shall draw an opened channel's strip as a thin outline on the histogram, each scaled to its own ground. | F-21 | US-027 |
| FR-076 | The system shall show a site's relief tiles as its background when its config has them, shall keep the view inside the tiles' bounds so that no plain band shows, and shall credit the Copernicus DEM on the map. | F-22 | US-028 |
| FR-077 | The system shall open a site with channels with the channel list showing, shall put the controls beside the map on a desktop and under it on a phone, and shall load its own open-licensed fonts. | F-22 | US-028 |
| FR-078 | The system shall draw each flagged cell of the selected pair at no less than a minimum size on screen, with a darker edge, in its class colour, reading them from the pair's image and changing no data. | F-22 | US-029 |
| FR-079 | The system shall show each channel area in km² and as "about N basketball courts", with 1 court = 28 × 15 m = 420 m². | F-22 | US-030 |
| FR-080 | The system shall highlight, in a channel's view, only the bar of the pass the map is showing, and shall scroll it into view. | F-20 | US-025 |
| FR-081 | The system shall offer a Relief or Satellite choice on the map, with Relief as the default, and shall remember each visitor's choice in the browser, working normally if that storage is blocked. | F-23 | US-031 |
| FR-082 | The system shall use bright overlay colours on Satellite and the Field map colours on Relief, and shall keep radar marks visible on both. | F-23 | US-031 |
| FR-083 | The system shall request imagery only while Satellite is on, shall show its credit only then, and shall show the relief under it while it loads or if it fails. | F-23 | US-031 |

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
| Background map imagery (EOxCloudless tiles, ADR-013) | Satellite background under the radar layers, CC BY-NC-SA 4.0 for non-commercial use | F-01, F-23 |
| Albay municipal boundaries (NAMRIA/PSA via OCHA COD-AB, CC BY-IGO, through GitHub `faeldon/philippines-json-maps`) | Town borders, town names, land mask and coastline for Mayon | F-01, F-02, F-05 |
| PHIVOLCS bulletins (read by the maintainer) | Channel names, event dates, validation records | F-03, F-12, F-19, F-20 |
| Channel line data: OpenStreetMap candidates, confirmed by the owner (`pipeline/context/channel_name_candidates.geojson`) | Lines for the named channels | F-19, F-20 |
| Boundary data for Panama: geoBoundaries gbOpen ADM2, under CC BY-SA 4.0 by owner decision (the terms its upstream source states) | Borders and land mask outside the Philippines | F-10 |
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
- Thresholds for brightness change and coherence loss are final, set on 2026-11-01 before the post-eruption passes were opened (brief Open Question 7). NISAR products are still PROVISIONAL.

## 12. Open Questions

| # | Question | Affects |
| --- | --- | --- |
| 1 | How comfortable with technology are residents, officials and judges, and which device does each mainly use? | §3 Personas |
| 2 | Closed on 2026-11-01: the owner set the final thresholds and rule; the values live in the site config. | FR-023, US-008 |
| 3 | Answered on 2026-11-01 for now, and the owner can change it: "in or near" means inside the channel's strip, the same ground its bars count, so there's no second distance. | US-023/AC-2, FR-057 |
| 4 | Closed on 2026-11-01: lines come from OpenStreetMap, and the owner confirmed Basud, Lidong, Mi-isi and Padang (`pipeline/reports/owner-checks.md`). | F-19, F-20, §8 |
| 5 | Partly closed on 2026-11-01: Panama, same final rule, no per-site tuning. The owner accepted CC BY-SA 4.0 for the borders. | F-10, §8 |
| 6 | What are the performance, availability, compatibility and scalability targets? (Suggestions given in §7.) | NFR-001, NFR-003, NFR-005, NFR-006 |
| 7 | What is the data-freshness target? | NFR-009 |
| 8 | Closed on 2026-11-01: the owner chose the same width as the channel test. The value is in the site config. | FR-064, T-074 |

## 13. Conflicts with Earlier Documents

- **Brief v0.3, §5, F-05:** says brightness change and coherence loss "agree between two passes". Measuring coherence loss needs the coherence of the previous pair as a baseline, which means three passes. Closed on 2026-11-01: brief v0.4 and F-05 above now describe the final rule, so the two signals no longer need to agree.

## 14. Revision History

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-31 | First draft |
| 0.2 | 2026-11-01 | Applied changes 1 and 2 of `docs/notes/proposed-doc-changes.md`. Final rule in FR-023 and US-008. Added FR-060 to FR-071, US-024 to US-026, and new acceptance criteria on US-004, US-005, US-008 and US-012. |

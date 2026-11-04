# Plan 8: the calm redesign (2026-11-04)

The owner approved the "calm redesign" mockups and wants the live app to look like them. The look is quiet, like a settings page: a warm off-white page, white cards with thin lines, one blue accent, and the map doing the talking. This plan builds it in five phases, so that an unfinished later phase can be dropped without losing the earlier ones. **The freeze is Nov 10.**

The reference pictures are in `plans/calm/`:

| Picture | What it shows |
| --- | --- |
| `calm-desktop-home.png` | Desktop home at 1280×800 |
| `calm-desktop-home-popover.png` | The same, with an info popover open and the bottom bar slid up |
| `calm-desktop-miisi.png` | Desktop, Mi-isi channel page |
| `calm-phone-home.png` | Phone home at 390×844, sheet closed |
| `calm-phone-home-open.png` | Phone home, sheet open |
| `calm-phone-miisi.png` | Phone, Mi-isi channel page |

The map in the pictures is a still screenshot of our own app. In the real app it stays the live Leaflet map.

## Hard rules

1. Work on `night-1`. First bring it up to date: `git switch night-1`, `git pull`, `git merge main`. Push `night-1` after each phase. **Never merge into `main`.**
2. This is our own look. No other company's logo, colours or fonts, and nothing copied from any other team's project.
3. Docs first, following CLAUDE.md: add the feature, requirements, tasks and tests to the docs with the next free IDs before building (F-24, FR-092 on, T-137 on). Never write threshold values into `docs/`.
4. **Site only.** Don't touch `pipeline/mrw`, the data files, the publish rules, the hold rule or `BLIND_CUTOFF`. The eruption run must still be able to publish a new pair into the redesigned app with no change to the pipeline.
5. Keep every rule the tests protect: the disclaimer tag on every screen, the NISAR label on the map, the 6 km ring, **Not checked** past the reach, only the checked channels, plain words (T-078), the EOX credit fully visible on Satellite, 44 px targets, popovers on hover, focus and tap with Esc to close, axe passing. If a test breaks only because the layout moved, update it to check the same rule in the new layout. Never delete a rule's check.
6. `pytest -q` and the contract check exit 0, and axe passes, before every push.
7. Screenshots go to the gitignored `pipeline/out/screens/calm/`.
8. If something needs the owner's decision, write it in `NIGHT_REPORT.md` and stop that part. Don't guess.
9. If phase D or E isn't done by the end of Nov 8, stop, push what passes, and report. Phases A to C are the must-haves.
10. **The eruption comes first.** If the Oct 31 passes appear on ASF while you work, stop the redesign, push what passes, and tell the owner. Don't run the eruption steps yourself.

## The look (tokens)

Put these in `:root` in `site/css/app.css` and use them everywhere in the panels and top bar.

| Token | Value | Used for |
| --- | --- | --- |
| `--ground` | `#FAF9F7` | Page and side column background |
| `--surface` | `#FFFFFF` | Cards, top bar, sheet, popovers |
| `--line` | `#E7E3DC` | Card borders and dividers (decoration only) |
| `--ink` | `#1C1B19` | Main text |
| `--ink-2` | `#5F5B55` | Secondary text, section titles |
| `--ink-3` | `#6F6B64` | Small print (5.0:1 on `--ground`) |
| `--accent` | `#1F5A8C` | Links, selected items, switches that are on |
| `--accent-soft` | `#EAF1F8` | Selected rows, soft notes (note text `#1F4A70`) |
| `--warn-bg` / `--warn-ink` | `#FDF3E4` / `#7A4510` | The disclaimer tag |
| `--switch-off` | `#8A847B` | Switch track when off (3.7:1, passes the 3:1 rule for controls) |

- **Font:** the vendored IBM Plex Sans only (400, 600, 700). Plex 500 isn't vendored, so use 600 where the mockups look medium. Don't add a font request. Numbers use `font-variant-numeric: tabular-nums`.
- **Shapes:** 12 px corners on cards and the sheet, 8 px on buttons and inputs, thin 1 px lines, soft shadows only on floating things (popovers, map controls, the bottom bar).
- **Map colours stay as they are.** The radar marks, channel lines, ring, towns and coast were tuned for the Field map and are covered by `test_field_map`. The legend dots in the panel must use the same colours as the marks on the map, not the mockup's.

## Phase A: the look (CSS and small markup changes)

Everything still works the same way. Only how it looks changes.

1. **Top bar:** white, 56 px on desktop, with a thin bottom line. From left to right:
   - the site name button, shown as a chip with a down arrow ("Mayon Volcano, Albay ▾"). It still opens the site picker.
   - the search button, shown like a search box: a magnifier and the grey text "Find a town or channel". It still opens the search panel. On a phone it's a 44 px magnifier button with a hidden label.
   - the disclaimer tag as an amber pill (`--warn-bg`, `--warn-ink`) with its ⓘ.
   - help as a round "?" button. Its accessible name stays the help text.
2. **Cards:** the side column becomes a stack of white cards on `--ground`, each with a small section title above it in `--ink-2`.
3. **Switches:** the layer checkboxes become switches (`<input type="checkbox" role="switch">`, styled). The label is on the left, the switch on the right, the whole row is a 44 px target, and there's a visible focus ring.
4. **Relief / Satellite:** a white segmented control. The pressed one is dark (`--ink` background, white text).
5. **Map controls:** zoom buttons white with rounded corners, 44 px. The NISAR label is a white pill with a small radar mark.
6. **Info buttons and popovers:** the glyph is a plain sans "i" in a 18 px ring. The popover is a white card with 10 px corners, a soft shadow and 13–14 px text. Keep `popover.js` behaviour, and keep every popover inside the viewport.
7. **Bottom bar (desktop):** white with a soft shadow. When hidden, show a short centred handle (56×4 px) instead of the full-width grey strip. The slide-up mechanism stays.

Commit, run the tests, take desktop and phone screenshots, push.

## Phase B: the desktop panel

The side column (380 px) shows four cards in this order. Compare with `calm-desktop-home.png`.

1. **This pass**
   - ‹ and › icon buttons around the pass. Their accessible names stay Previous and Next.
   - Keep the pass `<select>`, so people can jump to any pass, but style it as the centred title ("Oct 8 – 20, 2026").
   - Under it: "Track 111 · morning pass, 5:13 AM" (local time) and the pass ⓘ.
   - Then the big number: the area in about 34 px, with a smaller "km²".
   - Then "changed within 10 km of the summit" with the area ⓘ, then "About N basketball courts" from the existing `courtsText`.
   - Then a thin bar split into Likely and Possible, from the pair's `high_confidence_area_km2` and `low_confidence_area_km2`, with both numbers under it.
   - The existing gap or brightness-only note (`pair-gap`) goes in a soft blue box.
   - Keep the Compare button here as a quiet secondary button.
2. **Layers**
   - New material, with a switch and the Likely and Possible dots.
   - Channels, with a switch and "N checked by eye", counted from the channel file.
   - Permanent Danger Zone, **with no switch**. Its row says "Always shown": the ring must stay on the map. (The mockup's switch here is a mistake; don't build it.)
3. **Channels since the last pass**, with an ⓘ holding `channelsOnlyConfirmed`, `channelsHow` and `channelCourtSize`.
   - The channel list sits here, always open on desktop.
   - Each row has the name, the towns, km², courts, a tiny bar on the same shared scale, and a chevron. Order: largest first, as now.
   - Tapping a row opens that channel's page in the same column.
   - On desktop, the Channels button in the top bar goes away. Sites with no channels (Panama) hide this card.
4. **Brightness change:** the histogram, restyled. Its sentence and note stay in its ⓘ.

Check Panama too: no channel card, SINAPROC in the tag, its own wording ("change", not "new material").

## Phase C: the phone sheet

Compare with `calm-phone-home.png` and `calm-phone-home-open.png`.

1. The disclaimer becomes a full-width amber strip under the top bar.
2. The map is on top. Below it, the existing drawer becomes a white sheet with 18 px top corners and a grab handle. Swiping still works.
3. **Closed:** the pass row, the big number line, the Likely/Possible bar, the first 3 channels, and a link "Show all N channels and layers" that opens the sheet.
4. **Open:** everything, including all channels, Layers, the histogram, Compare, and the help links.
5. A channel's page opens in the same sheet, with a back chevron.
6. Credits stay folded behind a Credits button, except the EOX line when Satellite is on (T-135).
7. Check at 390×844 and 360×740. The map must keep at least 45% of the screen when the sheet is closed. Every target is 44 px.

## Phase D: the channel page

Compare with `calm-desktop-miisi.png` and `calm-phone-miisi.png`.

1. **Header:** "‹ All channels", the name at 24 px, then the towns.
2. **Pass card:** the selected pass's area, courts, and the strip note (`channelsHow`).
3. **"Every pass since June"**, with an ⓘ that explains the bars:
   - one vertical bar per published pair, oldest on the left, on the existing shared scale
   - the selected bar in `--accent`; track 104 lighter than track 111
   - a pair that `gapNote` marks is drawn dashed and hollow
   - each bar is a button with an accessible name (dates, track, km²), and tapping it shows that pair on the map, as now
4. **"Newest first":** the existing bar rows, restyled as list rows. Dates and track go on the left, km² and courts on the right. The selected row gets an `--accent-soft` tint. A dimmed row puts its gap note in an ⓘ.
5. **"Not checked" card:** a small dashed-line icon and `channelNotCheckedNote`.
6. **Source line:** the channel's name source and the OSM credit.

## Phase E: check and report

1. Screenshots at 1280×800, 390×844 and 360×740 of:
   - home, Mayon
   - home with a popover open
   - Mi-isi
   - the Jul 28 – Aug 21 pair (24 days)
   - Panama home
   - the compare view
   - a load error with Retry
2. Put each next to its reference picture and list the differences that remain and why.
3. Run the drill in `pipeline/RUNBOOK-eruption.md` ("Practise with a drill"), through `preview`, to show that a new pair appears in the new layout. The drill publishes nothing.
4. `pytest -q`, the contract check and axe all pass.
5. Add a "Plan 8" section to `NIGHT_REPORT.md` with the following, in plain words:
   - what was built
   - which phases are done
   - the screenshot list
   - the remaining differences from the mockups
   - anything for the owner to decide

## What not to copy from the mockups

- The Danger Zone switch (the ring is always on).
- The "Mockup: …" notes.
- The total courts rounded to tens. Use `courtsText`.
- Any number typed into the mockups. The app reads everything from its data files.
- Popover wording. Keep the app's own strings in `strings.js`. If a threshold appears in a popover, it must come from the pair record, never typed in.
- Google Fonts.

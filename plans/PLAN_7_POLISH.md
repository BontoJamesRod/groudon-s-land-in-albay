# Plan 7: brightness histogram, design directions, and a breadth check (2026-11-02)

The owner wants three things: visual polish, the brightness histogram, and breadth. This run builds the histogram, makes **two design directions as screenshots** for the owner to choose from (it doesn't build either one), and checks whether a light "breadth" feature is possible. Nothing goes to `main`.

## Hard rules

1. Work on `night-1`, push `night-1`, **never merge into `main`**.
2. **This is our own work.** Don't copy code, text, layouts, colours or wording from any other team's project. Use only open-source libraries with their licenses credited in `CREDITS.md`.
3. Docs first: add new features, requirements, data files, tasks and tests to the docs with new IDs before building, following CLAUDE.md. Never write threshold values into `docs/`.
4. No post-eruption products. The cutoff and the publish rules stay as they are.
5. `pytest -q` and the contract check must exit 0 before every push. Keep the axe accessibility tests passing.
6. Screenshots go to the gitignored `pipeline/out/screens/`.
7. If something needs the owner's decision, write it in `NIGHT_REPORT.md` and stop. Don't wait, and don't guess.

## Part A: Brightness histogram (build it)

**Why:** it answers "why did this spot count as changed?" for residents and judges.

1. **Pipeline:** for each published pair, write the distribution of brightness change (dB) for land inside the 10 km reach, as fixed bins (for example 0.25 dB wide). Include the share of pixels past the flag line. It's a small JSON per pair. Add it to 05 and 06, and to the contract check.
2. **App:** in the legend panel, a small histogram for the selected pair:
   - one vertical line at the **site's final threshold, read from the config** (both directions, since the rule flags brighter and darker)
   - the flagged tails shaded in the "possible new material" colour
   - one plain sentence under it, for example "Most of the ground barely changed. The shaded edges changed by more than the line, so they're flagged."
3. **No threshold slider.** The rule was locked before the eruption data, so letting visitors move it would undo that. Say this in one line of the help panel.
4. **Channels:** when a channel is selected, also show that channel's strip as a second, thin outline on the same histogram, if it stays readable. If it doesn't, leave it out and say so in the report.
5. **Tests:** data contract, numbers matching the published grid, the line at the config value, axe passing, and desktop and phone screenshots.

## Part B: Two design directions (screenshots only, don't build)

**The user:** a resident or a barangay disaster officer opens the app on a phone and wants to know "Is my channel changing, and is my town near it?" within 5 seconds.

**Make two clearly different directions.** Each is a set of static screenshots made from the real app with real data: the opening view, a selected channel, and the compare view. Show each at 360×740 and 1280×800. Use a throwaway branch or a local-only stylesheet, and keep `night-1`'s app unchanged.

Both directions must follow these principles:

- **The map is the hero.** Add **relief shading** (a hillshade from the Copernicus DEM, which the project already credits) so Mayon's cone and gullies read in 3D, like the owner's Google Earth view. Draw the channels clearly on the relief, with radar change on top.
- **Real radar imagery, no decoration.** No fake data, no generic "space" glow, no neon gradients.
- **Colour carries meaning only:** change classes (colour-blind safe), channels, the danger zone, towns. Town names must be high contrast and readable on a phone.
- **Big, plain numbers and words.** One readable typeface for text and one for numbers, at most.
- **Phone first:** map on top, the channel list in a bottom sheet. On desktop: map left, panel right.
- **Keep everything that works:** the danger-zone ring, the 10 km "not checked" rule, the disclaimer always visible, 44 px tap targets, the axe checks.

**Direction 1, "Field map":** light and print-like, like a good hazard map or topographic sheet. Calm, high contrast, readable in sunlight outdoors.

**Direction 2, "Night watch":** a dark map where the radar change and channels glow against the relief. Strong for a projector demo. It must still pass contrast checks, and it must not look like a generic dark dashboard.

Put the screenshots in `pipeline/out/screens/design/` with a short `README` that explains each direction in 3 lines. **Stop there for the owner to choose.** Building the chosen direction is the next plan.

## Part C: Breadth check (investigate, don't build)

The idea is a light **"NISAR coverage anywhere"** view. A visitor taps any point on Earth and sees which NISAR passes exist there and when, from ASF's public search (metadata only). Change maps stay for the showcase sites, and the view says so plainly.

1. Test whether ASF's public search API can be called directly from a browser on a static site (CORS), with no credentials. Use a tiny local test page, and don't add it to the app.
2. Report: does it work, how fast is it, what fields come back, and what would break it (rate limits, CORS, an outage). Then estimate the build size in tasks.
3. Don't add anything to the app or the docs for this part. The owner decides after reading.

## Report

Add a "Plan 7" section to `NIGHT_REPORT.md` with:

- the histogram result, plus one screenshot path for each size
- the two design directions, with their screenshot folder and README
- the breadth check's answer and estimate
- the decisions for the owner
- the test and contract-check results and the commit hashes

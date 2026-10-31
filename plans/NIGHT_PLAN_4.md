# Night plan 4: can radar see channels change? (2026-10-31)

Goal for tonight: answer one question with data you already have. **Do Mayon's river channels, and the quarry stretches in them, change more between radar passes than the land around them?**

This is a test, not a feature. Nothing on the live site changes tonight.

The owner reads your report on Sunday morning, Nov 1, and decides gate 1 of the plan: build Channel Watch, build it without the quarry part, or keep Mayon Radar Watch as it is.

## Hard rules (stop and write it in the report rather than break one)

1. **Do not search for, download or open any NISAR product tonight.** You don't need any: use only what is already in `raw/` and `pipeline/out/`. The 2026-10-30 cutoff in CLAUDE.md still applies.
2. Never open, print or copy `~/.netrc` or `~/_netrc`. Never print Earthdata credentials.
3. Never commit `raw/`, `*.h5`, `*.nc`, `*.nc4` or `pipeline/out/`.
4. Work on `night-1`. Commit there and push `night-1`. **Do not merge into `main`.** Never force-push or rewrite history.
5. Do not change `site/`, the site config, `classify.py`, thresholds, or anything in `docs/`. If the optional part E runs, it goes on its own branch.
6. **Never write "illegal", "unpermitted" or "violation" in any output.** Radar can't see permits. Say "quarry mapped in OpenStreetMap" and "change".
7. OpenStreetMap data is © OpenStreetMap contributors, ODbL. Credit it in the report.
8. Rain data: **1.5 GB download limit**, and only the days inside the 9 pair windows (2026-06-21 to 2026-10-19 UTC). Log the size.
9. The verdict rules below are fixed before you look at any results. Don't change them after seeing numbers. If one turns out to be impossible to apply, say so and report the numbers without a verdict.
10. Keep code simple, with plain comments that explain each radar step. The owner is a Python beginner.

## What to use

- **Radar pairs:** the 9 track 111 pairs (UTC): 06-21→07-03, 07-03→07-15, 07-15→07-27, 07-27→08-20 (24 days), 08-20→09-01, 09-01→09-13, 09-13→09-25, 09-25→10-07, 10-07→10-19. Use the 2 published track 104 pairs as a cross-check only.
- **The change layer, before any reach mask:** speckle-filtered brightness change in dB, the same as the pipeline computes, **without** the 10 km limit. Channels run past 10 km. Reuse cached rasters if they're unmasked, otherwise recompute from `raw/` with the existing modules.
- **Flagged pixel (fixed for the verdict):** brightness change of at least 3.0 dB in either direction, coherence ignored. Report brighter (≥ +3.0) and darker (≤ −3.0) separately as well as combined. Also report 4.0 and 5.0 dB, and the site's current provisional rule, as a sensitivity check. The verdict uses 3.0 dB combined only.
- **Channel lines:** `pipeline/context/mayon_waterways_osm_candidate.geojson` (714 segments, mostly unnamed; that's fine for tonight).
- **Farmland and other context:** whatever the false-alarm study already used.

## Part A: quarry stretches against quiet stretches

1. Get quarries from OpenStreetMap for the radar extent with Overpass: `landuse=quarry` ways and relations, with geometry. Save them as `pipeline/context/osm_quarries_candidate.geojson`.
2. Keep quarries of at least 50 radar pixels that lie within 300 m of a channel line. List every quarry kept and dropped in a table with: OSM id, name if any, area (ha), distance from the summit (km), distance to the nearest channel line (m), and the nearest OSM place name. Say which ones are nearest Budiao (Daraga) and Maninila (Guinobatan), if any are.
3. **Quiet stretches (controls):** cells within 200 m of a channel line, more than 500 m from any quarry, and in the same summit-distance band (±1 km) as the quarry they're matched with. Aim for the same total area as the quarries, or more.
4. For each pair, compute the flagged fraction (flagged pixels ÷ all pixels) in the quarry polygons and in the quiet stretches, and the ratio between them.
5. Save the test areas as `pipeline/context/channel_test_sites.geojson` **and** as `.kml`, so the owner can open them in Google Earth and check them by eye.

**If OpenStreetMap has no usable quarries:** say so at the top of the report and skip to Part C. Also create `pipeline/context/owner_quarry_sites.geojson`, an empty template with one example feature and comments on how to draw sites in geojson.io. Make Part A's script run on that file with one command, so the owner can draw sites on Sunday and run it.

## Part B: rain between passes

1. Use NASA GPM IMERG Late Run daily precipitation through `earthaccess`. The short name is probably `GPM_3IMERGDL`; confirm it and the version with a search. Prefer reading only the Mayon subset over downloading whole files.
2. For each of the 9 pairs, give the total rain (mm) between the two dates, averaged over the channel extent, and the wettest day in the window.
3. Label each pair's rain as low, middle or high by thirds of the 9 totals. This is for the report only. The owner picks the real "heavy rain" amount on Monday.
4. Add one line on the Oct 8 → Oct 20 pair: was it unusually wet or dry? This answers an open question from the evening run.

If IMERG access fails, say so, skip Part B, and carry on.

## Part C: channels against the land around them

1. For each pair, compute the flagged fraction in all channel strips (within 200 m of any channel line) and on land more than 500 m from any channel line, in matched summit-distance bands (2–4, 4–6, 6–8, 8–10, 10–14 km).
2. Report the ratio per pair and per band. Say how much of the remaining channel-strip area is farmland.
3. Compare the channel-strip result with the current 10 km circle. What share of the circle's flagged area would a strip mask keep?

## Verdict rules (fixed now)

- **GO:** in Part A, the quarry-to-quiet ratio is **2.0 or more in at least 5 of the 9** track 111 pairs, at 3.0 dB combined.
- **WEAK:** GO fails, but in Part C the channel-to-land ratio is **1.5 or more in at least 5 of the 9** pairs.
- **NO-GO:** neither holds.
- **Not tested:** Part A had no usable quarry sites. Give the Part C result on its own.

Also report, without letting it change the verdict, whether the quarry ratio holds in the low-rain pairs.

## Part D: the report

Write `pipeline/reports/channel-test.md`, `channel-test.json` and `channel_test.py`. Add one figure, `channel-test.png`: a map of the test sites on the left and bars per pair on the right (quarry vs. quiet, with rain marked).

The report opens with:

1. **The verdict** (GO / WEAK / NO-GO / not tested) in one sentence, with the numbers that decided it.
2. **What the owner must check by eye on Sunday:** the sites in the KML, and anything that looked wrong.
3. **One table per part**, then three to five plain bullets on what it means for Channel Watch.
4. **Limits:** pixel size against quarry size, mostly-unnamed channel lines, the 24-day pair, and that this is 9 pairs from one track.

Add a short "Night 4" section to `NIGHT_REPORT.md` that points to the report, lists the download size and the commits, and confirms that no NISAR product was searched or opened.

Run `pytest -q` and the contract check before the last commit. Both must pass. Push `night-1`.

## Part E (optional, only after A–D are committed and pushed)

On a new branch `brightness-leads-prep`, made from `night-1`:

1. Add a config switch to `classify.py` for the "brightness leads" rule: brightness decides whether a pixel is flagged, and coherence only raises confidence (it never adds area).
2. **The default stays exactly as today.** Every existing test passes unchanged.
3. Add tests for the new mode. Push the branch, but don't merge it, and write no threshold values anywhere.

This saves time on Monday if the owner chooses that rule. If there isn't time, skip it and say so.

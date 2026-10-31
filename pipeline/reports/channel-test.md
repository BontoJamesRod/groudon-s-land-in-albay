# Channel test: can radar see channels change?

**Verdict: GO, by the smallest possible margin.** The quarry-to-quiet ratio was 2.0 or more in exactly 5 of the 9 track 111 pairs at 3.0 dB combined (2.38, 2.31, 3.40, 2.87, 4.18), and 5 was the number needed.

The rule was fixed before the numbers, and it is applied as written. Please don't read GO as "radar sees quarrying". It says quarry polygons change more often than quiet channel stretches. It doesn't say why, and dropping either of two single quarries brings the count down to 4 of 9.

Rain could not be tested: NASA's server refused the IMERG files (Part B).

## What to check by eye on Sunday

Open `pipeline/context/channel_test_sites.kml` in Google Earth. Quarries are red and quiet stretches are blue. No quarry was dropped, so there are no orange ones.

1. **Are the 8 polygons really active quarries?** ESA WorldCover 2021 calls 67% of their area trees and only 16% bare, and none of them has a name in OpenStreetMap. Either the digging is newer than 2021, or the polygons take in a lot of ground that isn't quarry.
2. **`way/1383274132` and `way/1383274135`, the two western ones.** Across all 9 pairs they have almost no flagged pixels (under 0.1% and at most 0.7%). Are they disused, or drawn in the wrong place?
3. **`way/1323128469`, the largest (27 ha).** It's a third of the quarry area but changes little (0.1–2.1%). Is most of it inactive?
4. **`way/1323128466` and `way/1323128468`.** The GO depends on these two: without either one, the count is 4 of 9. Is there visible digging there, or could it be river-bed gravel moving by itself?
5. **Do you know the sites you care about?** No OSM quarry is near Budiao or Maninila (see Part A). If those matter, they haven't been tested.

## Part A: quarry stretches against quiet stretches

OpenStreetMap has 8 `landuse=quarry` polygons in the radar extent, all kept (77.81 ha). Quarries are © OpenStreetMap contributors, ODbL.

| OSM id | Name | Area (ha) | From summit (km) | To channel line (m) | Nearest OSM place | Flagged, across 9 pairs (%) |
| --- | --- | --- | --- | --- | --- | --- |
| way/1323128466 | none | 15.06 | 9.05 | 8 | Padang (0.5 km) | 1.4–9.9 |
| way/1323128467 | none | 8.44 | 9.57 | 14 | Padang (0.5 km) | 0.0–6.5 |
| way/1323128468 | none | 5.54 | 8.78 | 8 | Padang (0.7 km) | 1.1–14.1 |
| way/1323128469 | none | 27.04 | 9.34 | 0 | Padang (0.9 km) | 0.1–2.1 |
| way/1323128470 | none | 5.51 | 9.55 | 5 | Padang (0.7 km) | 0.0–8.2 |
| way/1323128471 | none | 6.27 | 9.89 | 46 | Padang (1.1 km) | 0.0–7.9 |
| way/1383274132 | none | 7.20 | 7.81 | 0 | Matanag (0.8 km) | under 0.1 |
| way/1383274135 | none | 2.80 | 7.21 | 99 | Bogña (1.7 km) | 0.0–0.7 |

**Dropped: none.** **Nearest Budiao:** `way/1383274135`, 3.4 km away. **Nearest Maninila:** the same quarry, 9.8 km away, so neither place really has a mapped quarry.

Quiet stretches cover 10,731 ha in total, and even the smallest quarry's match is 3,682 ha, so the target of "at least the quarries' area" is easily met.

Bold ratios reach 2.0. The last column is how many quarry pixels were flagged, out of 7,781.

| Pair (UTC) | Quarry (%) | Quiet (%) | Ratio, 3.0 dB combined | Brighter | Darker | 4.0 dB | 5.0 dB | Site rule | Flagged pixels |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 06-21 → 07-03 | 2.5 | 1.6 | 1.52 | 1.54 | 1.50 | 2.48 | 3.61 | 1.52 | 191 |
| 07-03 → 07-15 | 1.9 | 1.3 | 1.45 | 1.51 | 1.43 | 1.99 | 2.27 | 1.45 | 144 |
| 07-15 → 07-27 | 2.8 | 1.2 | **2.38** | 1.82 | 3.51 | 4.65 | 8.26 | 2.34 | 220 |
| 07-27 → 08-20 (24 days) | 3.0 | 4.2 | 0.70 | 0.60 | 1.89 | 0.93 | 1.38 | 0.70 | 233 |
| 08-20 → 09-01 | 2.2 | 0.9 | **2.31** | 1.38 | 3.96 | 3.21 | 3.95 | 2.31 | 168 |
| 09-01 → 09-13 | 1.4 | 1.1 | 1.33 | 0.89 | 4.03 | 2.12 | 2.41 | 1.01 | 110 |
| 09-13 → 09-25 | 2.0 | 0.6 | **3.40** | 3.49 | 3.27 | 6.05 | 8.93 | 2.35 | 153 |
| 09-25 → 10-07 | 2.0 | 0.7 | **2.87** | 2.85 | 2.87 | 4.08 | 4.40 | 2.42 | 153 |
| 10-07 → 10-19 | 2.2 | 0.5 | **4.18** | 4.74 | 3.61 | 4.46 | 4.27 | 1.60 | 171 |
| **Pairs at 2.0 or more** | | | **5 of 9** | 3 | 6 | 7 | 8 | 4 | |

Only the 3.0 dB combined column decides the verdict. The site rule uses coherence where a fair baseline exists, and brightness alone on 06-21 → 07-03, 07-03 → 07-15, 07-27 → 08-20 and 08-20 → 09-01.

**Track 104 cross-check** (not part of the verdict), 3.0 dB combined:

| Pair (UTC) | Quarry (%) | Quiet (%) | Ratio |
| --- | --- | --- | --- |
| 09-13 → 09-25 | 3.6 | 0.7 | 5.23 |
| 10-07 → 10-19 | 3.2 | 0.9 | 3.75 |

The other viewing direction agrees on both pairs it has, and both are above 2.0.

**How much the 5 of 9 leans on my choices.** I added these after seeing the verdict, so they can't change it.

| Check | Pairs at 2.0 or more |
| --- | --- |
| Quarries and quiet stretches each pooled, not matched quarry by quarry | 5 |
| Pixels with no radar value counted in "all pixels" (quarries have none) | 5 |
| Quiet cells within 50 m of the line only | 6 |
| Quiet cells on the same flank as the quarry (±45°) only | 5 |
| Leave out `way/1323128466` | **4** |
| Leave out `way/1323128468` | **4** |
| Leave out `way/1323128467`, `470`, `471`, `1383274132` or `1383274135` | 5 |
| Leave out `way/1323128469` | 7 |

## Part B: rain between passes

**Skipped, because access failed.** The search worked and confirmed the product: `GPM_3IMERGDL`, version 07, with 120 files for 06-22 to 10-19 (the files are V07C). Reading the first file then returned `403 Forbidden` from `data.gesdisc.earthdata.nasa.gov`. **0 bytes were downloaded** of the 1.5 GB limit.

| Asked for | Result |
| --- | --- |
| Rain per pair, wettest day, low/middle/high | Not available |
| Oct 8 → Oct 20: unusually wet or dry? | **Still unanswered** |
| Does the quarry ratio hold in low-rain pairs? | **Not tested** |

This usually means the Earthdata account hasn't approved the "NASA GESDISC DATA ARCHIVE" application. I didn't confirm that, and I didn't change anything on the account. If you want rain, approve it under Applications → Authorized Apps at urs.earthdata.nasa.gov, then run:

```powershell
python pipeline/reports/channel_test_inputs.py rain
python pipeline/reports/channel_test.py
```

The rain reader has never run on a real file, so it may need a fix. Rain is for the report only and can't change the verdict.

## Part C: channels against the land around them

Channel strips are within 200 m of a channel line. Land is more than 500 m from any line. The pair ratio weights each band by its share of the strip.

| Pair (UTC) | Strip (%) | Land (%) | Ratio | 2–4 km | 4–6 km | 6–8 km | 8–10 km | 10–14 km | Strip's share of the circle's flagged area |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 06-21 → 07-03 | 1.3 | 0.7 | 2.01 | 36.78 | 8.05 | 2.69 | 1.94 | 1.80 | 59% |
| 07-03 → 07-15 | 1.1 | 0.4 | 2.71 | 1.31 | 1.64 | 1.96 | 2.24 | 3.29 | 55% |
| 07-15 → 07-27 | 1.2 | 0.4 | 2.89 | 6.42 | 0.67 | 1.65 | 2.20 | 3.71 | 53% |
| 07-27 → 08-20 (24 days) | 3.3 | 1.0 | 3.37 | 6.90 | 0.42 | 3.42 | 2.98 | 3.73 | 61% |
| 08-20 → 09-01 | 0.7 | 0.2 | 3.88 | 6.70 | 1.34 | 2.85 | 3.50 | 4.42 | 57% |
| 09-01 → 09-13 | 0.8 | 0.3 | 2.66 | 5.79 | 18.71 | 5.80 | 1.74 | 3.14 | 58% |
| 09-13 → 09-25 | 0.6 | 0.2 | 3.09 | no land flags | 0.80 | 4.42 | 1.95 | 3.75 | 59% |
| 09-25 → 10-07 | 0.7 | 0.2 | 3.26 | 11.28 | 1.37 | 23.27 | 1.37 | 5.27 | 55% |
| 10-07 → 10-19 | 0.5 | 0.2 | 3.21 | no land flags | 7.48 | 10.77 | 2.23 | 3.20 | 62% |

All 9 pairs are at 1.5 or more. That holds for brighter, darker, 4.0 dB, 5.0 dB and the site rule too. Ratios in the 2–6 km bands rest on very few flagged pixels (0.0–0.4% of the strip), so don't lean on the large ones.

**Farmland:** 11% of the channel strip between 2 and 14 km is cropland in WorldCover 2021, against 4% of the land. Trees are 73% of the strip and 89% of the land, so "land" here is mostly forest. Part of the ratio may be fields and open ground against forest, not channels against land.

| WorldCover 2021 | Quarries | Quiet stretches | Channel strip | Land |
| --- | --- | --- | --- | --- |
| Trees | 67% | 73% | 73% | 89% |
| Cropland | 2% | 14% | 11% | 4% |
| Grass | 11% | 7% | 9% | 3% |
| Built-up | 2% | 4% | 5% | 2% |
| Bare | 16% | 2% | 1% | 1% |
| Water | 1% | 1% | 1% | 0% |

**Against the 10 km circle:** a strip mask would keep 53–62% of the circle's flagged area at 3.0 dB combined, and 53–65% under the site rule. But the strip is already 51% of the land in that circle, because channels are so dense. So the mask mostly removes area evenly, and it would not by itself clean up the map.

## What it means for Channel Watch

- **The go-ahead is real but thin.** It clears the fixed bar with nothing to spare, and two single quarries can each undo it. Treat it as "worth a closer look", not as proof.
- **The signal isn't shown to be digging.** Quarry polygons are the barest ground in the test (16% bare against 2%). Bare gravel may respond more to moisture than vegetated banks, and without rain data or known digging dates, this test can't separate the two.
- **The later pairs carry it.** The last three are the strongest (2.87–4.18), while the two pairs before mid-July, the 24-day pair and 09-01 → 09-13 aren't at 2.0. I can't say why without rain.
- **A stricter threshold separates better.** The count rises from 5 at 3.0 dB to 7 at 4.0 dB and 8 at 5.0 dB, and the site's current rule falls to 4, so a quarry layer probably shouldn't reuse that rule as it stands.
- **Coverage is the bigger gap.** Six of the 8 quarries are in one cluster near Padang, none is near Budiao or Maninila, and the owner's own sites would be a much better test than these.

## Limits

- **Pixel size against quarry size.** Pixels are 10 m, and quarries are 2.8–27 ha (278–2,702 pixels). The speckle filter averages over 50 m, so neighbouring pixels aren't independent, and quarry edges borrow from the ground around them. Each pair's 110–233 flagged pixels are fewer separate observations than the count suggests.
- **Mostly unnamed channel lines.** The lines are OSM candidates not checked by hand. All 8 quarries' nearest lines are unnamed, and some "quiet" stretches may hold unmapped digging.
- **The 24-day pair.** 07-27 → 08-20 has twice the gap of the others and it's the only pair where quiet exceeds quarry (0.70). It counts as one of the 9, as the rule says.
- **9 pairs from one track, one season.** All are from June to October, and all on track 111. Track 104 adds only two more.
- **Stops at the site bounds.** Cached crops end there, so "past 10 km" means up to the crop's edge. The 10–14 km band is partly cut off and channels further out aren't measured.
- **Quarry tags say nothing about activity.** They don't show whether a site is working, or since when, and radar can't tell who changed the ground or under what permission. This report only says "quarry mapped in OpenStreetMap" and "change".

## Rain rerun

**Blocked again, so there are no rain results yet.** The first read of the rerun also returned 403, and this time I read the server's reason: `EULA Acceptance Failure`. The Earthdata login itself works. NASA's terms for this data archive haven't been accepted on the account. Accepting them is the owner's decision, so I didn't do it, and I didn't use another rain source. **0 bytes of rain data were read** of the 1.5 GB limit, apart from the server's short refusal messages.

| Asked for | Result |
| --- | --- |
| Rain per pair, wettest day, low/middle/high | Not available |
| Heavy rain: any 3 consecutive days in a pair's window totalling 100 mm or more | Not available. The rule is now in `channel_test.py`, tested on made-up numbers only |
| Oct 8 → Oct 20: unusually wet or dry? | **Still unanswered** |
| Does the quarry ratio hold in low-rain pairs? | **Still not tested** |

The verdict above doesn't change either way, because rain is report-only.

To finish it, the owner opens NASA's approval page, signed in to Earthdata, and accepts the terms: <https://urs.earthdata.nasa.gov/approve_app?client_id=e2WVk8Pw6weeLUKZYOxvTQ> (this link is the one in the server's reply). Then:

```powershell
python pipeline/reports/channel_test_inputs.py rain
python pipeline/reports/channel_test.py
```

The results then land in `channel-test.json` under `rain_by_pair` and `low_rain_check`, and the figure gains the rain labels.

## Data used

- NISAR GCOV and GUNW: cached crops in `raw/` only, the latest dated 2026-10-19. No NISAR product was searched for, downloaded or opened beyond those.
- OpenStreetMap quarries, places and waterways: © OpenStreetMap contributors, ODbL.
- ESA WorldCover 2021, the false-alarm study's cached copy: CC BY 4.0.

To reproduce:

```powershell
python pipeline/reports/channel_test_inputs.py osm
python pipeline/reports/channel_test.py
```

Numbers are in `channel-test.json`, and the figure is `channel-test.png`.

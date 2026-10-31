# Panama check: does the pair match the mapped landslides?

Written for the project owner, to decide on T-037. Nothing was published: the pair is still only in `pipeline/out/`.

**Result: the map supports the pair at the scale of a few km, under the rule fixed before the comparison. It doesn't show that any single flagged spot is a landslide.** After the earthquake, flags rise about 17 times where the map shows the most landslides, and don't rise where it shows none. Whether to publish is your decision (see the end).

| Question | Earthquake pair (09-27 → 10-09) | Quiet pair (09-15 → 09-27) |
| --- | --- | --- |
| Do flags and mapped landslides rise and fall together, across 122 cells of 2 km? (rank correlation, 1 = perfectly) | **0.66** | −0.23 |
| The same, using only high-confidence flags | **0.81** | −0.14 |
| Flagged share of land, in the quarter of cells with the most landslides | **3.6%** | 0.21% |
| Flagged share of land, in the other cells | 1.0% | 0.73% |
| Flagged share of land, in cells with no mapped landslides | 0.85% | 0.94% |
| Rank correlation with the USGS landslide forecast | 0.43 | −0.42 |

The last-but-one row matters most: the background stays about the same, so the rise is where the map has landslides. That background is still a real false-alarm level, though: 27% of the earthquake pair's flagged area is in cells with no mapped landslides.

## What it was compared with

**Main reference: the [landslide map by the Institute of Geosciences, University of Panama](https://www.laestrella.com.pa/panama/nacional/azuero-registra-9553-deslizamientos-tras-sismo-de-magnitud-75-AF26896879)**, published on 2026-10-28 through La Estrella de Panamá. It marks 9,553 landslides, 4,822 of them in the epicentral zone, interpreted from Copernicus Sentinel-2 images (10 m). The institute calls the figures preliminary. I found no data file, only the image, so I read the black dots from the image. The image's size is 1600 × 1192 pixels, about 134 m per pixel.

**Second reference: the [USGS ground-failure model](https://earthquake.usgs.gov/earthquakes/eventpage/us6000u18k/ground-failure/landslide)** for the same event (`jessee_2018_model.tif`). This is a forecast, not an observation, so it counts for less.

**Also looked at, and not used for measuring:**

- [Copernicus EMS activation EMSR934](https://mapping.emergency.copernicus.eu/activations/EMSR934/): 9 areas and 13 products, mostly building damage. Only its ground-movement product overlaps our site, and it doesn't map landslides.
- [International Charter activation 1054](https://disasterscharter.org/es/activations/earthquake-in-panama-activation-1054-) and [UNOSAT's product list](https://unosat.org/products/): building and heritage damage, with no landslide map that I could find. I didn't open UNOSAT's live web map.
- [Eos Landslide Blog](https://eos.org/thelandslideblog/9-october-2026-panama-earthquake): names one "very dense" place, used below.

## An open question this closes

**The earthquake came before the radar pass.** [USGS](https://earthquake.usgs.gov/earthquakes/eventpage/us6000u18k) gives the time as 17:56:06 UTC on 2026-10-09, and the pass started at 23:53:35 UTC, about 6 hours later. So the pair does span it. Sources differ on the magnitude: USGS says 7.7, and the Panamanian institute says 7.5.

## How it was done

The script is `pipeline/reports/panama_check.py`, and its numbers are in `panama-check.json`. The pair uses the final rule with no tuning for this site.

1. Fit pixels to degrees from the map's axis ticks. The fit was within 0.0003°.
2. Keep the black dots and remove thinner lines and text. Cover the epicentre symbol, which hides any dots under it.
3. Put the dots on the radar grid and split the site into 2 km cells, counting land with a radar value in both pairs (433 km²).
4. Do the same for the quiet pair, as a control.

**The rule, fixed in the script before running it.** "Supports" needs a correlation of at least 0.5, at least 0.2 above the quiet pair, and at least 3 times the flags in the densest quarter of cells. "Weak support" needs 0.3, 0.1 and 1.5.

| Cell size | Verdict | Correlation, earthquake / quiet | Densest cells against the rest |
| --- | --- | --- | --- |
| **2 km (main)** | **Supports** | 0.66 / −0.23 | 3.5 times |
| 1 km | Supports | 0.60 / −0.12 | 3.3 times |
| 3 km | Weak support | 0.64 / −0.32 | 2.9 times (just under 3) |

**Checking the georeferencing.** Laying the map's sea over our own land shape, 94.6% agrees as fitted, and the best fit is 2 pixels west and 1 north (about 270 m), at 95.1%. Using that shift barely changes the result (0.66 and 3.46 times), so a small error here doesn't matter at this cell size.

## What this can't tell you

- **Dots are wider than landslides.** Each dot covers about 600 m, and together they cover 23% of the land. So nothing here measures single landslides, or what share of them the radar found. Don't read 3.6% as a detection rate.
- **The dates don't match.** The map uses images from 09-08 to 10-23, and the radar pair ends on 10-09. Landslides from aftershocks or the following two weeks of rain are on the map but can't be in the pair.
- **It could partly be terrain.** Landslides and radar changes both favour steep ground. The quiet pair argues against this as the main cause, because on the same terrain it doesn't match at all, but I didn't test slope separately.
- **Shaking can change the ground without a landslide**, and one pair is one pair.

## Things that don't fit neatly

- **The blog's "very dense" point has fewer flags than the site as a whole:** 1.4% within 3 km of 7.477, −80.865, against 1.8% elsewhere. The cause is the point, not the flags. The published map also has few dots there (13% of land), and its dense mass lies about 5 km north. Between 3 and 6 km from the point, dots rise to 34% and flags to 2.3%. So the two public sources differ on the location, and the flags follow the map.
- **Compact patches away from any dot.** These are the largest flagged patches with no mapped landslide nearby, all in the south, and they may be false alarms or real change that isn't a landslide. I can't tell which. You could check them in Google Earth along with the channels:

| Latitude, longitude | Area | High-confidence share |
| --- | --- | --- |
| 7.3882, −80.9038 | 0.15 km² | 14% |
| 7.4289, −80.8423 | 0.09 km² | 0% |
| 7.4199, −80.8492 | 0.07 km² | 0% |
| 7.4249, −80.8748 | 0.07 km² | 4% |
| 7.3831, −80.8523 | 0.06 km² | 98% |
| 7.4180, −80.8452 | 0.02 km² | 0% |

## Decisions for you

1. **Publish the pair (T-037)?** I recommend yes, as one plain change map worded as "changed after the earthquake", not "landslides". The match is real at this scale, and about a quarter of the flagged area isn't explained by the map.
2. **If you publish, what about the baseline pair?** The earthquake pair's coherence uses the quiet pair as its baseline, and F-10 says one pair. Its record would point to a pair that isn't on the site. I didn't test how the publish step and contract check treat that, because I didn't try publishing. Publishing the quiet pair too would avoid the question, and it would show visitors the "before".
3. **Can the map be used in "How we checked this"?** A link and citation are fine, but I found no license for the image, so it shouldn't be copied into the site or repository. That's why the image stays in the ignored `raw/` folder, and the overlay picture stays in `pipeline/out/`. For a data file, or to confirm the dot positions, you could ask the institute directly.

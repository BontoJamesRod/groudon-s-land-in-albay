# Threshold study, night 1 (T-016, analysis only)

**No thresholds were chosen.** The final values are the owner's decision. The site config still holds the PROVISIONAL values (3.0 dB, coherence loss 0.3). No product acquired on or after 2026-10-30 was searched for or opened.

Reproduce with `python pipeline/reports/threshold_study_night_1.py`. All numbers are in `threshold-study-night-1.json`.

## What the evidence says

1. **Over the whole site, the two signals don't separate the July event from quiet pairs at any candidate.** Total flagged area is similar in both groups, so most of what gets flagged is background change, not new material. A later check on the named gullies does show a signal (see the night 2 section).
2. **Brightness change gives a modest area signal.** At 3 and 4 dB, all three July pairs flag more land than every quiet pair (at 4 dB: 2.3–2.9 km² against 1.1–1.8 km²). The gap closes by 5–6 dB. The extra area is spread across the whole site, so it may be rain or farming rather than the current.
3. **Coherence loss shows no July signal.** The only July pair with a baseline (track 39) has one of the lowest coherence-loss tails of all pairs (99.9th percentile 0.29, quiet 0.24–0.48), and its high-confidence area is within the quiet range.
4. **There is one spatial hint.** In `threshold-study-maps.png`, both July pairs show a narrow linear streak near the middle of the map, on the volcano's slope, that the two quiet pairs mapped do not show. It could be a channel-confined deposit. This was seen by eye only, on 2 July and 2 quiet maps, and hasn't been compared with a source.

## Added on night 2: brightness change on the named gullies

Later checks changed point 2 above. Whole-site totals hide a clearer signal on the flanks where PHIVOLCS reported lava flows. This table is land flagged by brightness change alone at 3.0 dB, in a 60-degree wedge of each flank out to the reported flow length (km²):

| Track | Group | Basud (E) | Bonga (SE) | Mi-isi (S) |
| --- | --- | --- | --- | --- |
| 111 | 5 quiet pairs | 0.002–0.006 | 0.002–0.009 | 0–0.007 |
| 111 | **Spans the event** | **0.011** | **0.040** | **0.061** |
| 39 | 2 quiet pairs | 0.056–0.077 | 0.026–0.055 | 0.001–0.003 |
| 39 | **Spans the event** | **0.114** | **0.099** | **0.098** |
| 104 | 1 quiet pair | 0.007 | 0.004 | 0.002 |
| 104 | **Spans the event** | **0.027** | **0.019** | **0.068** |

On every track and flank, the July pair is above the quiet pairs. Mi-isi stands out most. Adding coherence loss raises the quiet pairs' numbers more than the July pairs', which is why a first comparison hid this.

Limits: these are small areas, the wedges are coarse and overlap, only 8 quiet pairs were used, and the rule was chosen after a first attempt gave a misleading result. It measures change on a flank, not a deposit in a gully. Only 3.0 dB was tested. See `july-gully-check.json`.

**For the owner's decision:** this suggests brightness may carry more of the signal than coherence loss on these slopes, at least for this event. It doesn't choose values.

## Pairs studied

| Pair | Group | Coherence loss? |
| --- | --- | --- |
| A111F008 08-20 → 09-01 | Quiet | Yes |
| A111F008 09-13 → 09-25 | Quiet | Yes |
| A111F008 09-25 → 10-07 | Quiet | Yes |
| A111F008 10-07 → 10-19 | Quiet | Yes |
| A039F008 09-08 → 09-20 | Quiet | Yes |
| A039F008 09-20 → 10-02 | Quiet | Yes |
| D104F082 09-13 → 09-25 | Quiet | Yes |
| A111F008 07-03 → 07-15 | Spans 07-14 | **No: previous pair has no GUNW on ASF** |
| A039F008 07-10 → 07-22 | Spans 07-14 | Yes |
| D104F082 07-03 → 07-15 | Spans 07-14 | **No: previous pair has no GUNW on ASF** |

The plan asked for the track 111 July pair. Because it has no baseline, the track 39 and track 104 July pairs were added.

## Percentiles on land

Absolute brightness change (dB):

| Pair | P50 | P90 | P95 | P99 | P99.9 |
| --- | --- | --- | --- | --- | --- |
| A111 08-20 → 09-01 | 0.54 | 1.38 | 1.70 | 2.54 | 4.70 |
| A111 09-13 → 09-25 | 0.48 | 1.24 | 1.53 | 2.39 | 4.77 |
| A111 09-25 → 10-07 | 0.48 | 1.24 | 1.54 | 2.43 | 4.74 |
| A111 10-07 → 10-19 | 0.50 | 1.29 | 1.60 | 2.45 | 4.67 |
| A039 09-08 → 09-20 | 0.55 | 1.43 | 1.78 | 2.70 | 4.60 |
| A039 09-20 → 10-02 | 0.58 | 1.50 | 1.86 | 2.84 | 5.02 |
| D104 09-13 → 09-25 | 0.49 | 1.29 | 1.61 | 2.57 | 5.14 |
| **A111 07-03 → 07-15** | 0.56 | 1.45 | 1.79 | 2.86 | 5.95 |
| **A039 07-10 → 07-22** | 0.58 | 1.52 | 1.91 | 3.23 | 6.10 |
| **D104 07-03 → 07-15** | 0.58 | 1.53 | 1.91 | 3.12 | 5.92 |

Coherence loss:

| Pair | P50 | P90 | P95 | P99 | P99.9 |
| --- | --- | --- | --- | --- | --- |
| A111 08-20 → 09-01 | −0.112 | 0.002 | 0.039 | 0.118 | 0.236 |
| A111 09-13 → 09-25 | −0.075 | 0.046 | 0.086 | 0.204 | 0.467 |
| A111 09-25 → 10-07 | −0.027 | 0.079 | 0.118 | 0.223 | 0.414 |
| A111 10-07 → 10-19 | 0.040 | 0.162 | 0.207 | 0.301 | 0.467 |
| A039 09-08 → 09-20 | −0.012 | 0.092 | 0.125 | 0.207 | 0.393 |
| A039 09-20 → 10-02 | −0.038 | 0.077 | 0.118 | 0.245 | 0.482 |
| D104 09-13 → 09-25 | −0.174 | −0.022 | 0.017 | 0.116 | 0.410 |
| **A039 07-10 → 07-22** | −0.066 | 0.045 | 0.082 | 0.165 | 0.291 |

The medians differ by pair (−0.17 to +0.04), so overall coherence shifts between dates. A fixed threshold therefore flags more on some dates than on others: at loss 0.2, A111 10-07 → 10-19 flags 35 km², of which 16 km² is inside the danger zone.

## Candidates

Three candidates for the owner to weigh. Area is km² of land flagged, as high + low. July pairs on tracks 111 and 104 can only be low confidence. For quiet pairs, all of it counts as flagged by mistake, assuming they really are quiet.

| Candidate | Quiet pairs, total | Quiet pairs, high only | A039 July, total (high) | A111 July, total | D104 July, total |
| --- | --- | --- | --- | --- | --- |
| A: 3.0 dB, 0.3 (the PROVISIONAL values) | 3.24–8.60 | 0.06–0.76 | 7.06 (0.12) | 5.20 | 6.83 |
| B: 4.0 dB, 0.4 | 1.10–2.53 | 0.02–0.24 | 2.85 (0.05) | 2.29 | 2.74 |
| C: 5.0 dB, 0.5 | 0.41–0.98 | 0.01–0.05 | 1.29 (0.02) | 1.15 | 1.22 |

Trade-offs:

- **A** catches the most but looks noisy: the reference pair, with no recorded event, shows 8.60 km² of "new material" on the map.
- **B** has about a third of A's false area. Its July totals (2.29–2.85) overlap the top of the quiet range (up to 2.53).
- **C** flags the least, but so little that a small deposit could be missed. The July pairs are only slightly above the quiet range.

Inside the danger zone, flagged area doesn't rise in July at any candidate. At candidate A, the quiet range is 0.06–2.49 km², and the July pairs have 0.20–0.49 km².

The full grid (brightness 2–6 dB by loss 0.2–0.5) is in the JSON.

## Figures

- `threshold-study-brightness-hist.png`: absolute brightness change, all pairs.
- `threshold-study-coherence-hist.png`: coherence loss, the 8 pairs with a baseline.
- `threshold-study-flagged-area.png`: land flagged by each brightness threshold, with loss at 0.5.
- `threshold-study-maps.png`: where the PROVISIONAL values flag land, 2 July and 2 quiet pairs.

## Limits of this study

- **"Quiet" only means no recorded event.** Reports describe an active lava flow in July, so activity may run through other pairs too. June to October is also the rainy season, and rain and farming both change radar brightness. Weather was not checked.
- **The location of the July deposit is unknown here.** Without it, detection can't be measured directly, only total area. A validation against named gullies would give a better test (T-035).
- **The baseline may hide the event.** Coherence loss compares with the previous pair. If the slope was already changing, its coherence was already low.
- **The event date needs checking.** The Asia News Network article appears to place the current on a Monday, and 2026-07-14 is a Tuesday. Either date falls in the same pairs.
- **One quiet baseline spans 24 days.** A111 08-20 → 09-01 uses 07-27 → 08-20 as its baseline, because no pass was found for 08-08. A longer gap lowers coherence, which may be why its median loss is so negative (−0.112). This pair's coherence numbers here are from before the pipeline stopped comparing unequal gaps (night 2), so its published record now has brightness only.
- **The July coherence result rests on one pair.** Track 39 is the only July pair with a baseline, so this evidence is thin.
- **Thresholds were tested on a 5 × 5 filtered 10 m grid.** Single pixels and small specks count fully. There is no minimum patch size, because the docs don't call for one.

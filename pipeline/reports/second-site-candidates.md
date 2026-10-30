# Second-site candidates (T-036 decision prep)

**No site is chosen.** This is the owner's decision. Passes come from ASF's product list. A small radar crop was then read for each candidate (`second_site_probe.py`, results in `second-site-probe.json`) to compare brightness change in the pair spanning the event with the pair before. It didn't use coherence, classify or masking of water, so the full new-material method is still untested at these sites.

## Radar probe results

Land flagged by brightness change alone (km²). The levels are test values only.

| Candidate, pair | Valid pixels | 3 dB: before → event | 4 dB: before → event | 5 dB: before → event |
| --- | --- | --- | --- | --- |
| Panama, track 141 frame 85, 09-27 → 10-09 | 98% | 0.51 → **2.51** | 0.13 → **1.16** | 0.04 → **0.65** |
| Fuego, track 134, 07-17 → 08-10 | 95% | 0.89 → 1.46 | 0.31 → 0.70 | 0.14 → 0.37 |
| Nyamulagira, track 14, 07-21 → 08-14 | 89% | 3.79 → 0.97 | 0.80 → 0.30 | 0.10 → 0.09 |

- **Panama** stands out clearly on track 141. **Tracks 4, 40 and 76 have almost no valid pixels over the cluster** (0%, 0.1%, 3.8%), even though their footprints contain it, so they aren't usable there.
- **Fuego** shows about twice the area, but the gap is 24 days and the pair before is 12, so part of that may come from the wait.
- **Nyamulagira** shows no sign of the flow on this pair: the pair before flags more. This box and pair may simply miss it.

The boxes are rough: 11 × 11 km around the Panama cluster, about 13 × 11 km around Fuego's west side, and 16 × 14 km on Nyamulagira.

All passes were acquired before 2026-10-30. Every pair below has PROVISIONAL GCOV, a PROVISIONAL GUNW and a previous-pair GUNW for coherence loss, unless noted. Search only shows that a product touches the area, not how much of it has usable data. Run `python pipeline/reports/second_site_search.py` to repeat the search; full granule names are in `second-site-search.json`.

## Summary

| | A: Azuero Peninsula, Panama | B: Fuego, Guatemala | C: Nyamulagira, DR Congo |
| --- | --- | --- | --- |
| Continent | North America (Central America) | North America (Central America) | Africa |
| Event | Landslides from a Mw 7.7 earthquake | Pyroclastic flows in a paroxysm | Lava flow |
| Date | 2026-10-09 | 2026-08-03 to 08-05 | Active on 2026-08-09 (start not known) |
| Best pair | 12 days (track 141) | 24 days | 24 days |
| Independent check | Good: Sentinel-2, 2,351 mapped | Medium: named ravines | Weak: one flow length |
| Radar probe | Clear change on track 141 | About twice the area | No sign of it |
| Main risk | Earthquake lowers coherence widely; partial frames | 24-day gap; steep ravines | Start date; access to reports |

## A: Azuero Peninsula landslides, Panama

- **Event:** Mw 7.7 earthquake on 2026-10-09, epicentre at 7.587, −80.769. A dense landslide cluster lies near 7.477, −80.865.
- **Evidence:** [Eos Landslide Blog](https://eos.org/thelandslideblog/9-october-2026-panama-earthquake). It compares Sentinel-2 images from 9 September and 18 October, and reports news of 2,351 landslides mapped by the University of Panama's Institute of Geosciences.
- **Usable pairs:**

| Track, frame, direction | Before → after | Note |
| --- | --- | --- |
| 141, 85, descending | 2026-09-27 → 10-09 | **98% valid.** The after pass starts at about 23:53 UTC on the day of the earthquake: confirm the earthquake came first. The strong change suggests it did |
| 76, 5, ascending | 2026-10-05 → 10-17 | Only 3.8% valid over the cluster, and its previous pair spans 24 days |
| 4, 5, ascending | 2026-09-30 → 10-12 | **Not usable here:** no valid pixels over the cluster |
| 40, 85, descending | 2026-10-02 → 10-14 | **Not usable here:** 0.1% valid over the cluster |

All of these are partial frames on ASF (`_P_` in the name, `frameCoverage: Partial`). Track 141 frame 84 and track 76 frame 6 don't reach the cluster at 7.477, −80.865, so they are left out.

- **Why it fits:** the 12-day gap matches Mayon's method. Landslides strip the surface, which should change brightness, and optical images allow a real validation.
- **Risks:** this is not a volcano, so the app's wording about new material would need to fit a landslide, and there is no summit or danger zone (05 §10 covers that case). Ground shaking and movement could lower coherence across the whole scene, so false high-confidence areas are a real risk. The landslides are described as mainly shallow.

## B: Fuego, Guatemala

- **Event:** paroxysm starting 2026-08-03 at 08:30 local time, ending after about 50 hours. Reports differ on whether it ended on 08-05 or 08-06.
- **Evidence:** [The Watchers, citing the weekly volcanic report and INSIVUMEH](https://watchers.news/2026/08/15/the-weekly-volcanic-activity-report-august-6-12-2026/) reports pyroclastic density currents and material in the Seca and Ceniza ravines. [VolcanoDB](https://volcanodb.com/fuego-volcano) says the flows reached 5–7 km down six ravines. It is a less established source, and its dates are not fully consistent.
- **Usable pairs:**

| Track, frame, direction | Before → after | Note |
| --- | --- | --- |
| 134, 9, ascending | 2026-07-17 → 08-10 | 24 days |
| 62, 9, ascending | 2026-07-24 → 08-17 | 24 days |
| 127, 81, descending | 2026-07-17 → 08-22 | 36 days |

- **Why it fits:** the closest match to Mayon: a volcano with pyroclastic deposits in named ravines.
- **Risks:** there is no 12-day pair, and a longer gap lowers coherence anyway. Fuego erupts constantly, so "before" is not a quiet surface. The Mayon result suggests this kind of deposit may be hard to separate from background change. Also the same continent as candidate A.

## C: Nyamulagira, DR Congo

- **Event:** a long-running lava eruption. A flow on the southwest flank was about 2.8 km long on 2026-08-09, and the eruption continued through July and August.
- **Evidence:** [VolcanoDiscovery's Nyamulagira page](https://www.volcanodiscovery.com/nyamuragira/news.html) and [The Watchers weekly report, 13–19 August](https://watchers.news/2026/08/22/the-weekly-volcanic-activity-report-august-13-19-2026/). I read these only as search summaries, not the full pages.
- **Usable pairs:**

| Track, frame, direction | Before → after | Note |
| --- | --- | --- |
| 14, 1, ascending | 2026-07-21 → 08-14 | 24 days |
| 50, 89, descending | 2026-07-23 → 08-16 | 24 days |
| 115, 1, ascending | 2026-07-16 → 08-21 | 36 days |

- **Why it fits:** the only candidate on a different continent from the Americas. Fresh lava over forest should be a strong change for L-band radar, and the area has little farming on the flow field.
- **Risks:** the start of this flow isn't known, so it may not have grown between these dates. There is little independent mapping to validate against, and no agreed danger zone to show. It also lies in a conflict-affected region, which makes local reports harder to get.

## Also considered

- **Kīlauea, Hawaii:** track 151, frame 11, ascending, 2026-08-11 → 08-23, has a 12-day pair spanning an overflow of more than 600 m on 08-12. New flows land on older lava inside a caldera, so the change may be subtle. It's in the Pacific, not on a continent, so I left it out of the three.
- **Krasheninnikov, Kamchatka:** a [JPL NISAR time-lapse](https://www.jpl.nasa.gov/news/us-india-satellite-captures-time-lapse-video-of-volcanic-eruption/) shows lava spreading, but Kamchatka is in Asia, the same continent as Mayon.
- **Langtang, Nepal:** the 26 August collapse is also in Asia.
- **Urgent Response products:** ASF also lists `_UR_` products, such as a GCOV over Panama from 2026-10-29. They aren't PROVISIONAL or BETA, so the pipeline leaves them out of both GCOV and GUNW searches.

## Checks before choosing

1. Boundary data for the chosen site (`docs/05` Open Question 4). None was checked for any candidate.
2. Process one full pair, with coherence, and look at the result. Each costs about 0.3 GB.
3. Does the Space Apps challenge want a volcano, or any surface change?

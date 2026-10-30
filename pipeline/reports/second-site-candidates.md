# Second-site candidates (T-036 decision prep)

**No site is chosen.** This is the owner's decision. Nothing here was processed: the passes come from ASF's product list only, so whether the new-material method actually detects each event is untested.

All passes were acquired before 2026-10-30. Every pair below has PROVISIONAL GCOV, a PROVISIONAL GUNW and a previous-pair GUNW for coherence loss, unless noted. Search only shows that a product touches the area, not how much of it has usable data. Run `python pipeline/reports/second_site_search.py` to repeat the search; full granule names are in `second-site-search.json`.

## Summary

| | A: Azuero Peninsula, Panama | B: Fuego, Guatemala | C: Nyamulagira, DR Congo |
| --- | --- | --- | --- |
| Continent | North America (Central America) | North America (Central America) | Africa |
| Event | Landslides from a Mw 7.7 earthquake | Pyroclastic flows in a paroxysm | Lava flow |
| Date | 2026-10-09 | 2026-08-03 to 08-05 | Active on 2026-08-09 (start not known) |
| Best pair | 12 days | 24 days | 24 days |
| Independent check | Good: Sentinel-2, 2,351 mapped | Medium: named ravines | Weak: one flow length |
| Main risk | Earthquake lowers coherence widely; partial frames | 24-day gap; steep ravines | Start date; access to reports |

## A: Azuero Peninsula landslides, Panama

- **Event:** Mw 7.7 earthquake on 2026-10-09, epicentre at 7.587, −80.769. A dense landslide cluster lies near 7.477, −80.865.
- **Evidence:** [Eos Landslide Blog](https://eos.org/thelandslideblog/9-october-2026-panama-earthquake). It compares Sentinel-2 images from 9 September and 18 October, and reports news of 2,351 landslides mapped by the University of Panama's Institute of Geosciences.
- **Usable pairs:**

| Track, frame, direction | Before → after | Note |
| --- | --- | --- |
| 4, 5, ascending | 2026-09-30 → 10-12 | After pass covers the cluster |
| 40, 85, descending | 2026-10-02 → 10-14 | After pass covers the cluster |
| 76, 5, ascending | 2026-10-05 → 10-17 | After pass covers the cluster |
| 141, 85, descending | 2026-09-27 → 10-09 | Same day as the earthquake: check the earthquake's time first |

These are **partial frames** on ASF (`_P_` in the name, `frameCoverage: Partial`). The after passes' footprints above contain the cluster at 7.477, −80.865; the before passes were not checked. Track 141 frame 84 and track 76 frame 6 don't cover it, so they are left out.

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
2. Process one pair and look at the result. Each costs about 0.3 GB.
3. Does the Space Apps challenge want a volcano, or any surface change?

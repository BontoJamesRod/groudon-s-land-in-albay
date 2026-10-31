# Channel names: PHIVOLCS channels matched to OpenStreetMap lines

**These are candidates, not a channel map: 1 high, 3 medium and 6 low confidence.** Nothing has been checked by eye or against a hazard map. Open `pipeline/context/channel_name_candidates.kml` in Google Earth: green is high, yellow medium, red low. The owner's verdicts on these lines are in `pipeline/reports/owner-checks.md`, and only the lines confirmed there are used.

| Channel | OSM ids | Length (km) | Start from summit (km) | Town reached | Confidence | Reason | Check by eye |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Mi-isi | 553506874, 303767871, 259704467, 86384642, 4271814 | 13.4 | 1.3 | Daraga | medium | no matching OSM name tag (parts are tagged Yawa River); passes 350 m from Mi-isi; on the 173° flank; reaches Daraga | Two Yawa River branches pass Mi-isi about equally closely (the other starts at OSM way 554777832). Which one is the gully on the south flank? |
| Bonga | 553506868, 554777830, 259704468, 780725289, 4271814 | 13.0 | 2.0 | Legazpi City | low | no matching OSM name tag (parts are tagged Pawa-Burabod River, Yawa River); passes 493 m from Bogña; on the 155° flank; reaches Legazpi City; shares its line with Mabinit | Is OSM's Bogña the Bonga PHIVOLCS means? OSM's village spelled Bonga is on the east-northeast flank and doesn't fit Legazpi. Does this line follow the southeast gully? |
| Basud | 554777833, 84641309, 553656279, 553656278 | 10.0 | 1.5 | Santo Domingo | high | OSM name tag 'Basud River'; on the 96° flank; reaches Santo Domingo | Confirm the top joins correctly. OSM also has a separate 'Basud RIver' tributary (way 555279291), left out here. The villages called Basud in OSM are on other rivers. |
| Lidong | 554777823, 245694516 | 8.9 | 1.9 | Santo Domingo | medium | no OSM name tag; passes 146 m from Lidong; on the 116° flank; reaches Santo Domingo | Is this river separate from Basud, or does PHIVOLCS treat them as one system (older lists say Basud-Lidong)? |
| Mabinit | 86384638, 554777825, 780725289, 4271814 | 11.4 | 3.6 | Legazpi City | low | no matching OSM name tag (parts are tagged Pawa-Burabod River, Yawa River); passes 657 m from Mabinit; on the 153° flank; reaches Legazpi City; shares its line with Bonga | This line and Bonga's join, so they can't both be certain. Which branch really passes Mabinit? The line is 650 m away, which is far for a village named after its channel. |
| Matanag | 554777826, 92649866, 92649870 | 5.3 | 6.1 | Legazpi City | low | no OSM name tag; passes 476 m from Matanag; on the 139° flank; reaches Legazpi City | OSM's line only starts 6 km from the summit. Is there a channel higher up that OSM hasn't drawn? |
| Buyuan | 553528103, 84641266, 84641260 | 9.7 | 1.2 | Legazpi City | low | no OSM name tag; passes 522 m from Padang; on the 129° flank; reaches Legazpi City | Weakest guess: OSM has no place called Buyuan, so Padang stands in for it. It's chosen only as the other long line near Padang. Find the real Buyuan river first. |
| Padang | 553670459, 553671688, 553672571, 92787375, 553656262, 553656261, 92787404, 259886619 | 6.3 | 4.2 | Legazpi City | medium | no OSM name tag; passes 392 m from Padang; on the 123° flank; reaches Legazpi City | Does it reach Padang's river, and might Padang and Buyuan be the wrong way round? PHIVOLCS has also written them as one channel, Buyuan-Padang. |
| Masarawag | 1385620645, 553515923, 553515921, 86384281, 86384279, 731801904, 731801903, 731801902, 86384272 | 15.6 | 1.9 | Guinobatan | low | no matching OSM name tag (parts are tagged Cabilogan River, San Francisco River); passes 968 m from Masarawag; on the 234° flank; reaches Guinobatan; shares its line with Maninila | This line passes closer to Maninila than to Masarawag. Look for the true channel beside Masarawag; OSM's lines closest to it start only about 8 km out. |
| Maninila | 1385620639, 163102997, 729189550, 729423169, 729423171, 729423168, 729189548, 729189547, 729423170, 163102615, 731801904, 731801903, 731801902, 86384272 | 17.7 | 2.1 | Guinobatan | low | no matching OSM name tag (parts are tagged Cabilogan River, San Francisco River); passes 379 m from Maninila; on the 228° flank; reaches Guinobatan; shares its line with Masarawag | Does it run through Maninila? It later joins the San Francisco River, so check that this name and that one are the same river further down. |

## How confidence is set

- **High:** an OSM name tag says so, and the line reaches the town PHIVOLCS gives.
- **Medium:** no name, but it passes within 400 m of the barangay, starts within 5 km of the summit, reaches the town, and shares no more than 100 m with another channel.
- **Low:** anything else.

## Limits

- I chose each line's top segment by hand from the lines near its barangay, so the rules grade that choice but don't make it. The choices are in `CHANNELS` in `channel_names.py`.
- Each line stops at the last point inside its town, so it can't show a channel's course beyond that.
- A village's name doesn't prove that a channel runs through it, and OSM place points are approximate.
- Where branches meet, only one route is followed, and the OSM lines themselves haven't been checked.
- Flow direction is taken from how OSM drew each line, which isn't always right.

## Sources

- Waterways and places: © OpenStreetMap contributors, ODbL. Using these lines in the app means attribution, and ODbL's share-alike terms should be read first.
- Which town each channel belongs to: search summaries of the [January 2026 PHIVOLCS advisory as reported by Rappler](https://www.rappler.com/philippines/phivolcs-mayon-kanlaon-volcano-lahar-update-advisory-january-16-2026/) and [GMA News](https://www.gmanetwork.com/news/topstories/regions/973047/phivolcs-issues-lahar-warning-for-mayon-volcano-amid-ada/story/). I didn't read the PHIVOLCS bulletin itself, and I found no newer full list.
- Town outlines: the site's `towns.geojson`.

To repeat: `python pipeline/reports/channel_names.py`

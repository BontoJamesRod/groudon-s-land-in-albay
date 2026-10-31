# Channel names, second try: one line per name

**Nothing here is confirmed or published: 1 high, 5 medium and 10 low match confidence.** Open `pipeline/context/channel_name_candidates_v2.kml` in Google Earth. The colours are match confidence, NOT hazard level.

| Name | Confidence | Own barangay, distance | Flank | Start, length (km) | Town | Stops at | Doubts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bulawan | high | None: name tag | 59° | 1.3, 11.8 | Malilipot | edge of its town | — |
| Maninila | medium | Maninila, 379 m | 227° | 2.1, 10.3 | Guinobatan | join with Quirangay, Salugan, Tumpa | — |
| Anoling | medium | Anoling, 195 m | 196° | 2.0, 5.9 | Camalig | edge of its town | — |
| Buang | medium | Buang, 342 m | 314° | 0.6, 14.7 | Tabaco City | edge of its town | — |
| Upper Nasisi | medium | Nasisi, 165 m | 283° | 1.9, 14.8 | Ligao City | edge of its town | — |
| Upper Nabonton | medium | Nabonton, 252 m | 265° | 2.8, 13.0 | Ligao City | edge of its town | — |
| Bonga | low | Bogña, 558 m | 148° | 3.6, 5.7 | Legazpi City | join with Mabinit | way 259704468 is 580 m from the barangay and starts 2.0 km out, so distance doesn't settle it |
| Mabinit | low | Mabinit, 638 m | 159° | 2.0, 7.2 | Legazpi City | join with Bonga | Bogña is closer to this line (580 m) than its own barangay; way 554777825 is 657 m from the barangay and starts 3.6 km out, so distance doesn't settle it |
| Matanag | low | Matanag, 476 m | 139° | 6.1, 5.3 | Legazpi City | edge of its town | way 553885141 is 401 m from the barangay and starts 6.1 km out, so distance doesn't settle it |
| Buyuan | low | Buyoan, 552 m | 132° | 3.2, 7.5 | Legazpi City | edge of its town | Padang is closer to this line (522 m) than its own barangay |
| Masarawag | low | Masarawag, 765 m | 234° | 1.9, 10.5 | Guinobatan | join with Maninila, Quirangay, Salugan, Tumpa | — |
| Salugan | low | Salugan, 244 m | 200° | 4.7, 5.6 | Camalig | join with Quirangay | way 553667500 is 255 m from the barangay and starts 4.7 km out, so distance doesn't settle it |
| Quirangay | low | Quirangay, 209 m | 204° | 5.7, 4.2 | Camalig | join with Salugan | — |
| Tumpa | low | Tumpa, 340 m | 215° | 5.2, 7.2 | Camalig | edge of its town | — |
| Busay | low | Busay, 888 m | 183° | 1.5, 8.7 | Daraga | join with Anoling | way 250416508 is 154 m from the barangay and starts 1.5 km out, so distance doesn't settle it |
| San Vicente | low | San Vicente, 729 m | 1° | 0.6, 11.8 | Tabaco City | edge of its town | — |

## Shared lower rivers

These are written as their own grey lines, and given to neither name.

- Unnamed river (below Quirangay, Salugan): 5.9 km.
- Cabilogan River / San Francisco River (below Maninila, Quirangay, Salugan, Tumpa): 7.4 km.
- Yawa River (below Anoling, Busay): 4.9 km.
- Pawa-Burabod River / Yawa River (below Bonga, Mabinit): 5.8 km.

## The hints, checked against OSM place names

| Hint | What OSM says |
| --- | --- |
| Matanag, Legazpi Bgy 52? | Yes: Matanag has the alternate name Barangay 52 |
| Buyuan, Bgy 49 or 51? | Bgy 51: OSM's Buyoan has the alternate names Barangay 51 and Buyuan. The first try missed it because of the spelling |
| Padang, Bgy 50 or 60? | Bgy 50: Padang has the alternate name Barangay 50 |
| Anoling and Salugan, Camalig | Both are villages in Camalig. OSM's Anoling Elementary School is about 12 km out, far from the Anoling point |
| Busay near Cagsawa, Daraga | Yes: a Busay village is in Daraga, close to the Cagsawa Ruins. OSM has other places called Busay |
| Tumpa and Quirangay, Camalig | Both are villages in Camalig |

Bonga has no Legazpi place under that spelling. OSM's Bogña has the alternate name Barangay 53, and treating it as Bonga is my reading. OSM's places spelled Bonga are in Bacacay and out to the west, which don't fit Legazpi. Mabinit has the alternate name Barangay 54.

**Not resolved:** Binaan, which reports of the 2026 advisory name in Daraga, has no place or waterway in OSM, so it has no line. It isn't in docs/05 section 8.

## How confidence is set

The rules from `channel_names.py` stay: high needs an OSM name tag on every part and the right town. Medium needs the name's own barangay within 400 m, a start within 5 km of the summit, the right town, and no shared line. Two rules are new, and either makes a match low:

- Another listed barangay is closer to the line than the name's own.
- Another branch starting within 6.5 km of the summit is closer to the barangay, or within 100 m of the same distance.

## Limits

- I chose each top segment and fork by hand; the rules grade those choices but don't make them. The choices are in `CHANNELS` in `channel_names_v2.py`.
- A village's name doesn't prove a channel runs through it, and OSM place points are approximate.
- Flow direction is as OSM drew it. I didn't bridge gaps in OSM's lines, so a line can start lower than the real gully.
- The waterway extract is the one saved in `pipeline/context`. The barangay points were read from OSM on 2026-11-01.

To repeat: `python pipeline/reports/channel_names_v2.py`

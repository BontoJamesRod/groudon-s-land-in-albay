# Channel lines from OpenStreetMap (T-010 decision prep)

**No channel file was built, and the source isn't chosen.** `channels.geojson` is still to do, once the owner decides.

- Candidate file: `pipeline/context/mayon_waterways_osm_candidate.geojson`. Data © OpenStreetMap contributors, ODbL. Using it in the app means attribution, and ODbL's share-alike terms should be read first.
- Full match results: `channel-candidates.json`. Run `python pipeline/reports/channel_candidates.py` to repeat them.

## Result

OSM has plenty of lines but very few names: **714 waterway segments, 58 with a name (8%)**, and 209 segments within 8 km of the summit. Name matching finds **only 2 of the channels** in `docs/05` §8.

| Channel (05 §8) | Expected town | Match in OSM | Quality |
| --- | --- | --- | --- |
| Bulawan | Malilipot | Bulawan River: 5 segments, 15.7 km | **Good.** Exact name, crosses Malilipot, starts 1.3 km from the summit |
| Basud | Not given | Basud River: 4 segments, 10.0 km, plus "Basud RIver": 1 segment, 2.5 km | **Good, needs joining.** Exact name, starts 1.5 km from the summit, crosses Santo Domingo. One segment has a spelling error |
| Basud-Lidong | Santo Domingo | Basud River is possibly the same | **Possible.** Same town, but needs a person to confirm |
| Mabinit | Legazpi City | None | Missing |
| Buyuan-Padang | Legazpi City | None | Missing |
| Miisi, Mi-isi | Daraga | None | Missing, and it's one of the gullies PHIVOLCS names most |
| Tumpa | Camalig | None | Missing |
| Anoling | Camalig | None | Missing |
| Quirangay | Camalig | None | Missing |
| Maninila | Guinobatan | None | Missing |
| San Vicente | Tabaco City | None | Missing |
| Buang | Tabaco City | None | Missing |
| Upper Nasisi | Ligao City | None | Missing |
| Upper Nabonton | Ligao City | None | Missing |
| Bonga | Not given | None | Missing, also named by PHIVOLCS |

Names in OSM that aren't on the list, which a person could check against local maps: Baclayon, Bagtang-Maroroy, Baranghawon, Bogñabong, Cabilogan, Guinale, Makabalo, Nawang, Pawa-Burabod, Sagumayon, San Fernando, San Francisco, Tagas, Tayhi, Tiagao, Tibu, Tobgon, Yawa.

## What this means

OSM can't supply the channels by name alone. Its unnamed lines may still follow the right gullies, so one option is to name them by hand: match each PHIVOLCS channel to an unnamed line using a hazard map or local knowledge, then record that source. Doing that for 13 or more channels is manual work, and the matches need checking. No PHIVOLCS channel map was tested tonight.

The match only compares names. Towns and summit distance are shown to help judge a match, and no line was checked against imagery.

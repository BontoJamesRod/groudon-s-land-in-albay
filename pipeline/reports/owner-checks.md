# Owner checks

Checks that only the project owner can make, with who made them and when. The pipeline reads the same verdicts from `pipeline/context/mayon_channels.json`, and a test keeps the two files the same.

## Channel lines (T-073, F-19, FR-065)

The owner checked the candidate lines in Google Earth Pro. The lines are the ones in `pipeline/context/channel_name_candidates.geojson`, and confirmed lines are used as they are.

| Channel | Verdict | Date | Imagery date | Confirmed by |
| --- | --- | --- | --- | --- |
| Basud | Confirmed | 2026-11-01 | 2026-05-16 | Project owner |
| Lidong | Confirmed | 2026-11-01 | 2026-05-16 | Project owner |
| Mi-isi | Confirmed | 2026-11-01 | 2026-05-16 | Project owner |
| Padang | Confirmed | 2026-11-01 | 2026-05-16 | Project owner |
| Bonga | Not confirmed | 2026-11-01 | 2026-05-16 | Project owner |
| Buyuan | Not confirmed | 2026-11-01 | 2026-05-16 | Project owner |
| Mabinit | Not confirmed | 2026-11-01 | 2026-05-16 | Project owner |
| Maninila | Not confirmed | 2026-11-01 | 2026-05-16 | Project owner |
| Masarawag | Not confirmed | 2026-11-01 | 2026-05-16 | Project owner |
| Matanag | Not confirmed | 2026-11-01 | — | Project owner |

**Not confirmed** means the channel must never be drawn or listed. The contract check fails if its name appears in the channel files. A check can still cite it as a place name, such as "Bonga Gully" in the July check text (owner's decision, 2026-11-01).

**Matanag:** the owner gave this verdict separately on 2026-11-01 and named no imagery date.

## Channel files license

On 2026-11-01 the owner accepted ODbL for `channels.geojson` and `channel_areas.json`.

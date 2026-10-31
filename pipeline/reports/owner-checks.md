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
| Matanag | No verdict | — | — | — |

**Not confirmed** means the channel must never be shown. The contract check fails if its name appears anywhere in the published data.

**No verdict:** Matanag is in the candidates file, but the owner's message doesn't mention it. Without a confirmation it's treated like an unconfirmed channel and stays off the site. If the owner gives a verdict, add it here and in `mayon_channels.json`.

# Night report 1 (2026-10-31)

Branch `night-1`. Nothing pushed, nothing merged into `main`.

## Status

| Task | Status | Commit | Test evidence |
| --- | --- | --- | --- |
| T-006 | Done | af1a13d | `pytest -q`: 35 passed. `python pipeline/mrw/contract_check.py`: 0 errors. CI itself has not run, because nothing was pushed |
| T-007 | Done, not run | 67f5ecc | `gitleaks/gitleaks-action@v3` confirmed in its README and as a tag on GitHub. Not executed: running the gitleaks binary locally was denied by the session's safety check, and pushing a test branch is forbidden. Owner: see morning checks |
| T-008 | Done | 710698e | `pytest -q`: 50 passed, including TC-036 |
| T-009 | Done | cad2170 | Contract check 0 errors; 12 towns; land = 84% of the box. Alignment with imagery is a manual check for the owner |
| T-011 | Done | see `git log --grep T-011` | Contract check 0 errors |
| T-012 | Done | see `git log --grep T-012` | `pytest -q`: 64 passed, including TC-025, TC-026. Real search below |

## Real ASF search (T-012)

Searched from 2026-06-01 with the request limited to before the cutoff: 29 GCOV (track 111 frame 8: 10, track 104 frame 82: 10, track 39 frame 8: 9), 24 GUNW, 26 consecutive pairs. No result had to be dropped by the cutoff filter. "Track 111 pairs match Vertex" was not compared by eye: owner check.

Track 111 dates: 06-21, 07-03, 07-15, 07-27, 08-20, 09-01, 09-13, 09-25, 10-07, 10-19. 08-08 is missing, so 07-27 → 08-20 spans 24 days, and the same gap appears on the other two tracks.

**Pairs with no GUNW on ASF:** `D104F082_20260621_20260703` and `A111F008_20260621_20260703`. So the track 111 pair spanning July 14 (07-03 → 07-15) has no previous-pair baseline and can't get coherence loss under FR-022.

## Data downloaded from ASF

Running total: 0 GB of the 20 GB budget.

## Files the plan expected that are missing

`CLAUDE.md` is not at the repo root (it is at `docs/CLAUDE (1).md`, which I read). `pipeline/notebooks/nisar_albay_starter.ipynb`, `pipeline/legacy/` and `docs/notes/` do not exist in the repo, so all pipeline logic was written from the docs and from inspecting real products. The granule names come from the examples in `docs/06-api-spec.md`.

## Assumptions

- T-006: `contract_check` rejects fields not in 05 ("exactly the column names in 05").
- T-006: `previous_pair_id` is checked for format only, not for presence in `pairs.json`. The baseline pair may be processed but not published, as with the reference pair tonight.
- T-006: a pair without coherence may omit the `coherence_loss` layer, because there is nothing to draw. 06 says a real pair has 5 layers but doesn't cover this case.
- T-006: `ci.yml` skips pushes to `main` because `deploy.yml` calls the same checks for those. Every push is still checked once.

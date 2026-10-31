# Runbook: the first passes after the eruption

Follow this **only after the owner has locked the thresholds**. Until then, no product acquired on or after 2026-10-30 (UTC) may be searched for or opened.

Run every command in PowerShell from the project folder. Steps 1–3 are the owner's decisions and edits. An agent shouldn't do them without the owner saying so.

## What this produces

| Track | Pair | Coherence baseline |
| --- | --- | --- |
| 104 descending | `mayon_D104F082_20261019_20261031` | 10-07 → 10-19 |
| 111 ascending | `mayon_A111F008_20261019_20261031` | 10-07 → 10-19 |

Both baselines are already available. The pass times should be about 10:16 UTC on track 104 and 21:13 UTC on track 111, based on earlier passes. ASF may take days to list a pass, and its GUNW can come later than its GCOV.

## 1. Lock the thresholds

Edit `pipeline/sites/mayon.json`:

- In `thresholds`, set `status` to `"FINAL"` and enter the final `brightness_threshold_db` and `coherence_loss_threshold`.
- In `provisional_fields`, remove `"thresholds"`.

Don't write threshold values into `docs/`.

**If you choose "brightness leads, coherence confirms":** the site doesn't work that way yet. Today `pipeline/mrw/classify.py` gives low confidence to coherence loss alone. Change that first, with its tests in `pipeline/tests/test_classify.py`, and check the wording on the site that describes "one signal". Do this before step 4.

## 2. Update the wording on the site

The site says the thresholds are provisional in `site/js/strings.js`, in `drawerShow` and in the disclaimer line. The products themselves are still provisional, so keep that part. Then:

```powershell
.venv\Scripts\Activate.ps1
python pipeline/mrw/stamp_assets.py
pytest
```

## 3. Lift the cutoff

In `pipeline/mrw/search.py`, change this line:

```python
BLIND_CUTOFF = datetime(2026, 10, 30, tzinfo=timezone.utc)
```

to this:

```python
BLIND_CUTOFF = datetime(2026, 11, 1, tzinfo=timezone.utc)
```

This opens the Oct 31 passes and nothing later. Then update the rule in `CLAUDE.md` that forbids opening these products, because it would otherwise still apply. Commit steps 1–3 together **before opening any eruption data**, so the history shows the thresholds came first:

```powershell
pytest
git add pipeline/sites/mayon.json pipeline/mrw pipeline/tests site CLAUDE.md
git commit -m "T-0NN: lock the final thresholds and lift the blind cutoff"
```

## 4. Redo the published pairs with the final values

This keeps the whole timeline on one set of thresholds. It reads cached crops and shouldn't download much.

```powershell
python pipeline/mrw/eruption_run.py republish
python pipeline/mrw/contract_check.py site/data
```

## 5. Check for the Oct 31 passes

This reads product names only.

```powershell
python pipeline/mrw/eruption_run.py check
```

- **"no new pass on ASF yet":** stop and try again later.
- **"NO COHERENCE YET":** wait for the GUNW. Processing now would give a brightness-only result.

## 6. Process

```powershell
python pipeline/mrw/eruption_run.py process
python pipeline/mrw/contract_check.py pipeline/out --unpublished
```

The download budget in `download.py` counts every byte ever logged in `raw/`, up to 20 GB. Each pair should need under 0.2 GB.

**Before publishing, check the printed areas.** Look at the median coherence of both pairs if the total is far above about 8 km². D104 09-25 → 10-07 showed 102 km² only because its baseline had unusually high coherence, which made the whole scene look changed. The current baseline's median is about 0.29 on track 104. See "A coherence baseline problem" in `pipeline/reports/threshold-study-night-1.md`.

## 7. Publish

Publish only the pairs from step 6 that were processed and look right:

```powershell
python pipeline/mrw/publish.py mayon mayon_D104F082_20261019_20261031
python pipeline/mrw/publish.py mayon mayon_A111F008_20261019_20261031
python pipeline/mrw/contract_check.py site/data
```

Each publish undoes itself if the contract check fails.

The newest pair becomes the one the site opens on. `LATEST_PAIR` in `pipeline/tests/e2e/test_mvp.py` names the current one, so update it to the newest pair you published. The newest is the track 111 pair if both are published.

```powershell
pytest
```

## 8. Push and merge

Only with the owner's go-ahead for this occasion. Never force-push. Check first that no radar files are staged.

```powershell
git add site/data pipeline/tests NIGHT_REPORT.md
git status --short
git commit -m "T-0NN: publish the first passes after the eruption"
git push origin night-1
```

Wait for CI on `night-1` to pass at https://github.com/BontoJamesRod/groudon-s-land-in-albay/actions, then:

```powershell
git switch main
git pull --ff-only origin main
git merge --no-ff night-1 -m "Merge night-1: first passes after the eruption"
git push origin main
git switch night-1
```

## 9. Check the live site

Wait for "Deploy site" to pass, then open https://bontojamesrod.github.io/groudon-s-land-in-albay/ with a hard reload (Ctrl+Shift+R), on a computer and a phone:

- [ ] It opens on the newest pair, with the right dates and track.
- [ ] The legend no longer says PROVISIONAL about the thresholds.
- [ ] The dotted 10 km ring and the danger zone show, and the 10 km limit is stated.
- [ ] Compare opens without the map moving, and town labels stay still while dragging.
- [ ] Older pairs still open.
- [ ] The browser console shows no errors.

## If something goes wrong

- **A bad pair went live:** remove its folder from `site/data/sites/mayon/pairs/`, rebuild the list, and push a new commit. Don't rewrite history. To rebuild the list:

  ```powershell
  python -c "import sys; sys.path.insert(0, 'pipeline'); from pathlib import Path; from mrw.config import utc_now_text; from mrw.publish import rebuild_pairs_list; rebuild_pairs_list(Path('site/data/sites/mayon'), utc_now_text())"
  ```

- **The script says "Stopped":** step 1 or step 3 isn't done. It stops before contacting ASF.
- **Earthdata login fails:** don't open or print `~/.netrc` or `~/_netrc`. Stop, and have the owner log in again with `python pipeline/mrw/check_access.py`.

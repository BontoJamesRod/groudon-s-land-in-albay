# Runbook: the first passes after the eruption

Run every command in PowerShell from the project folder, after `.venv\Scripts\Activate.ps1`.

**Where things stand:** the owner locked the final thresholds on 2026-11-01. `BLIND_CUTOFF` in `pipeline/mrw/search.py` is 2026-11-01, which opens the Oct 31 passes and nothing later. Don't move it unless the owner says so. The 11 published pairs already use the final thresholds, so there's nothing to redo first.

## What this produces

| Track | Pair | Coherence baseline |
| --- | --- | --- |
| 104 descending | `mayon_D104F082_20261019_20261031` | 10-07 → 10-19 |
| 111 ascending | `mayon_A111F008_20261019_20261031` | 10-07 → 10-19 |

Both baselines are already available. The pass times should be about 10:16 UTC on track 104 and 21:13 UTC on track 111. ASF may take days to list a pass, and its GUNW can come later than its GCOV.

## 1. Check for the Oct 31 passes

This reads product names only.

```powershell
python pipeline/mrw/eruption_run.py check
```

- **"no new pass on ASF yet":** stop and try again later.
- **"NO COHERENCE YET":** wait for the GUNW. Processing now would give a brightness-only result.

## 2. Process

```powershell
python pipeline/mrw/eruption_run.py process
python pipeline/mrw/contract_check.py pipeline/out --unpublished
```

The contract check here reads only the pair folders, so other files under `pipeline/out/` can't block it. The download budget in `download.py` counts every byte logged in `raw/`, up to 20 GB. Each pair should need under 0.2 GB.

## 3. Review the numbers

Name the pairs from step 2, one or both. This reads names from ASF and the cached crops, and downloads nothing.

```powershell
python pipeline/mrw/eruption_run.py review mayon_D104F082_20261019_20261031 mayon_A111F008_20261019_20261031
```

It prints each pair's far-field coherence change, flagged area beyond 8 km, no-data share and where its change is, next to the published pairs. It says HOLD or LOOK CLOSER where the rule below applies, and exits with code 1 only on a hold. With two pairs, it also says how much the tracks agree.

## 4. Preview

This copies the site to `pipeline/out/preview/`, publishes the pairs into the copy, and serves it on this computer only. Nothing changes in `site/`.

```powershell
python pipeline/mrw/eruption_run.py preview mayon_D104F082_20261019_20261031 mayon_A111F008_20261019_20261031
```

Open <http://127.0.0.1:8001/>, and press Ctrl+C when finished. Look for reasons (d) and (e) below, on both pairs.

## 5. Apply the rule, and ask the owner

The owner set this rule on 2026-11-03, before any post-eruption product was opened.

**Hold a pair (don't publish it) automatically if any of these is true:**

- **(a)** a product isn't PROVISIONAL or better;
- **(d)** large no-data gaps cover the volcano. `review` calls more than 5% of the land within the danger zone large, and a person also looks at the map;
- **(e)** the map shows stripe or edge patterns. Only a person can check this.

**Look closer if either far-field check is out of range. Neither holds a pair by itself:**

- **(b)** the median coherence change of land more than 8 km from the summit, where an eruption shouldn't reach, falls outside the range of the same measure on the published pairs that used coherence;
- **(c)** the flagged area beyond 8 km from the summit is above the highest of the published 12-day pairs. The 24-day pair is left out.

**To look closer:** `review` prints this pair's flagged share inside 6 km, beyond 8 km and in the channels' strips, next to the published pairs and to what change spread evenly would give. If the change is concentrated near the volcano and its channels compared with the quiet pairs, publish. If it's spread evenly across the whole scene, hold.

**A large area alone is NOT a reason to hold.**

**Two tracks or one:** when both tracks have a pair, `review` reports how much they agree, next to the quiet pairs' 17–21% within about 200 m. This supports a decision and never blocks one. If only one track is ready, publish it with the single-track note in step 6.

The reference numbers are saved in `pipeline/reports/hold-check-baseline.json`. Don't rebuild that file after opening a post-eruption product.

Report the numbers and the preview to the owner. **Publish only with the owner's approval.** A held pair stays in `pipeline/out/`.

## 6. Publish

```powershell
python pipeline/mrw/publish.py mayon mayon_D104F082_20261019_20261031
python pipeline/mrw/publish.py mayon mayon_A111F008_20261019_20261031
python pipeline/mrw/contract_check.py site/data
pytest
```

With only one track ready, add `--single-track` to its publish command. When the other track arrives, publish the first pair again without the option, so that its note goes away.

Each publish undoes itself if the contract check fails. The newest pair becomes the one the site opens on. The tests read the latest pair from the data, so they need no edits.

## 7. Push and merge

Only with the owner's go-ahead for this occasion. Never force-push. Check first that no radar files are staged.

```powershell
git add site/data NIGHT_REPORT.md
git status --short
git commit -m "T-038: publish the first passes after the eruption"
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

## 8. Check the live site

Wait for "Deploy site" to pass, then open https://bontojamesrod.github.io/groudon-s-land-in-albay/ with a hard reload (Ctrl+Shift+R), on a computer and a phone:

- [ ] It opens on the newest pair, with the right dates and track, and the label on the map agrees.
- [ ] The dotted 10 km ring and the danger zone show, and the 10 km limit is stated.
- [ ] Compare opens without the map moving, and town labels stay still while dragging.
- [ ] Older pairs still open.
- [ ] The browser console shows no errors.

## Practise with a drill

A drill runs steps 2 to 4 on an older pair, from cached data only, in `pipeline/out/drill/`. It refuses any pair from the eruption onward, and it publishes nothing.

```powershell
python pipeline/mrw/eruption_run.py process --drill mayon_A111F008_20261007_20261019
python pipeline/mrw/contract_check.py pipeline/out/drill --unpublished
python pipeline/mrw/eruption_run.py review --drill mayon_A111F008_20261007_20261019
python pipeline/mrw/eruption_run.py preview --drill mayon_A111F008_20261007_20261019
```

## If something goes wrong

- **A bad pair went live:** remove its folder from `site/data/sites/mayon/pairs/`, rebuild the list, and push a new commit. Don't rewrite history. To rebuild the list:

  ```powershell
  python -c "import sys; sys.path.insert(0, 'pipeline'); from pathlib import Path; from mrw.config import utc_now_text; from mrw.publish import rebuild_pairs_list; rebuild_pairs_list(Path('site/data/sites/mayon'), utc_now_text())"
  ```

- **The script says "Stopped":** the thresholds aren't FINAL or the cutoff has been moved back. It stops before contacting ASF. Ask the owner.
- **"This crop isn't in raw/":** `review` and a drill never download. Run step 2 first, or pick a pair that has been processed.
- **Earthdata login fails:** don't open or print `~/.netrc` or `~/_netrc`. Stop, and have the owner log in again with `python pipeline/mrw/check_access.py`.

# Night plan 1 (2026-10-31)

You are working alone overnight on Mayon Radar Watch while the owner sleeps. Nobody can answer questions until morning. Work through the tasks below in order, verify each one, and leave a clear report.

## Read first

- `CLAUDE.md` (project rules)
- `docs/04-technical-design.md`, `docs/05-database-design.md`, `docs/06-api-spec.md`: the design, the data files and the exact field names
- `docs/07-roadmap.md` (task IDs) and `docs/08-test-plan.md` (test cases)
- `docs/01-prd.md` §6: the exact error and display messages (FR-IDs)
- Reference code that already worked: `pipeline/notebooks/nisar_albay_starter.ipynb`, `pipeline/legacy/` (old `common.py`, `make_data.py`, `build_app.py`, `template.html`) and the progress notes in `docs/notes/`. Reuse their logic instead of reinventing it. If any of these files are missing, carry on without them and say so in the report.

## Hard rules

1. **Branch:** create branch `night-1` from `main` before changing anything. Commit after each task with the message `T-0NN: <what was done>`. Never push, never merge into `main`, never force-push, never rewrite history.
2. **Secrets:** never open, print or copy `~/.netrc` or `~/_netrc`. Log in with `earthaccess.login()`, which reads the saved credentials. If login fails, mark every data task blocked and continue with the others.
3. **Data in Git:** never commit `raw/`, `*.h5` or `pipeline/out/`. Respect `.gitignore`.
4. **Docs are locked:** don't edit anything in `docs/` except new files in `docs/notes/`. If a document looks wrong or incomplete, write it in the report.
5. **Stay blind to the eruption:** do not search for, download, open or process any NISAR product acquired on or after 2026-10-30 (UTC). Thresholds must be chosen before anyone sees eruption data.
6. **Thresholds are the owner's decision:** read them from the site config. Use provisional values (brightness 3.0 dB, coherence loss 0.3) and mark them `PROVISIONAL` in code, config, output and the report. Never write threshold values into `docs/`.
7. **Download budget:** at most 20 GB from ASF in total tonight. Prefer streaming only the cropped part of each product (fsspec + h5py ranged reads, as in the notebook) over full downloads. Cache in `raw/`. Keep a running total in the report.
8. **Follow the docs exactly:** folder layout (04 §10), module names (04 §3), file formats and field names (05, 06), messages (01 §6). When something is unclear, choose the option marked `Suggestion:` in the docs, record the assumption in the report and keep going. Don't add features that aren't in the docs.
9. **Verify:** run `pytest` after every task; it must pass before you commit. Put the evidence (command and result) in the report.
10. **Beginner-readable code:** short functions, plain-English docstrings, comments that explain each radar step. The owner is learning from this code.
11. **Don't get stuck:** after 3 failed approaches on one task, mark it blocked with the reason and move to the next task that doesn't depend on it.
12. **Windows:** PowerShell commands, `pathlib` for paths, Python 3.12 in `.venv`.

## Known facts (from the progress notes)

- Mayon bounds (W, S, E, N): 123.56, 13.14, 123.81, 13.38. Summit 13.2572° N, 123.6856° E. Danger zone 6 km. Time zone `Asia/Manila`.
- Passes: track 111 ascending frame 8, track 104 descending frame 82, track 39 ascending frame 8. Only compare passes from the same track, frame and direction.
- GCOV backscatter: `/science/LSAR/GCOV/grids/frequencyA/HHHH`, with `xCoordinates`, `yCoordinates` and `projection` in the same group. Values are linear power (gamma-0).
- GUNW coherence: `/science/LSAR/GUNW/grids/frequencyA/unwrappedInterferogram/HH/coherenceMagnitude`, about 80 m pixels.
- Reference pair: track 111, 2026-10-07 → 2026-10-19 (granule names in the progress notes). Sanity check: median brightness change on land ≈ +0.14 dB.
- Boundaries: `faeldon/philippines-json-maps`, file `geojson/provdists/hires/municities-provdist-500500000.0.1.json` from the `geojson-hires.zip` release (Albay = 500500000). License: CC BY-IGO.

## Tasks, in order

1. **T-006:** `pipeline/mrw/contract_check.py` validates every JSON and GeoJSON file under `site/data/` against 05: envelope, `schema_version`, required fields, types, enums, constraints, and image and grid sizes. Add a CI workflow that runs `pytest` and the contract check on every push and pull request, and make the deploy job run only if they pass. Write tests for it.
2. **T-007:** add a secret-scanning step to CI. Check the tool's current official docs for the right action name and version. If you can't verify one, write a small Python pattern-check script instead and run it in CI.
3. **T-008:** `pipeline/sites/mayon.json` and `pipeline/mrw/config.py` (load, validate, build the `sites` row). Zoom levels 12 / 10 / 16, marked PROVISIONAL (05 Open Question 1). Reversed bounds must give the FR-044 message. Tests for TC-036.
4. **T-009:** build `towns.geojson`, `land.geojson` and `sources.json` for Mayon from the boundary file: clip to the bounds, put label points inside each polygon, make land the union of the towns. They must pass the contract check.
5. **T-011:** `events.json` with 2 events: 2026-10-30 eruption (source https://mb.com.ph/2026/10/30/mayon-volcano-alert-status-raised-to-level-3) and 2026-07-14 pyroclastic density current (source https://asianews.network/?p=287449).
6. **T-012:** `search.py` and `pairs.py`: list passes, build consecutive same-track pairs, give the FR-027 and FR-028 messages. Unit tests use fake search results (TC-025, TC-026). Do one real search and record the result in the report.
7. **T-013:** `download.py`: stream or download, crop to the site bounds, cache in `raw/`, log bytes.
8. **T-014:** `gcov.py`: HH to dB, 5 × 5 speckle filter, brightness change, sea, coverage and product masks with no-data reasons. Unit tests (TC-027). Run it on the reference pair and compare with the +0.14 dB sanity check.
9. **T-015:** `coherence.py`: coherence loss = previous pair's coherence − this pair's coherence, resampled to the GCOV grid; brightness-only fallback when GUNW is missing. Unit tests.
10. **T-017:** `classify.py`: none, low and high classes, areas in km², grid codes from 05. Thresholds from the config (PROVISIONAL). Tests for TC-022 and TC-023.
11. **T-018:** `export.py`: write the 5 layer images, `new_material.bin` and `pair.json` to `pipeline/out/`, exactly as in 05 and 06. The contract check must pass on the output.
12. **T-019:** `publish.py`. Publish the reference pair into `site/data/` on this branch, so the web app has real data to show.
13. **T-016, analysis only:** study at least 3 quiet pairs (June–October, all before 2026-10-30) plus the track 111 pair whose dates span 2026-07-14. Show histograms and percentiles of absolute brightness change and coherence loss on land; for the July 14 pair, how much area each candidate threshold flags; for quiet pairs, how much area each candidate flags by mistake. Propose 2–3 candidate threshold pairs with that evidence. Save it as `pipeline/reports/threshold-study-night-1.md` with figures next to it. Don't pick the final values.
14. **T-022 to T-025 (web):** `site/js/data.js`, `map.js`, `timeline.js`, `layers.js`, following 03, 04 and 06: real sites, towns, land, danger-zone ring, background-imagery fallback, timeline with the latest pair, new-material layer, legend, area summary, disclaimer line. Check it by serving `site/` locally. Take screenshots if you can; otherwise list the manual checks for the owner.

## Report

Keep `NIGHT_REPORT.md` at the repo root up to date as you go. Commit it with each task. It must contain:

- Each task: done, partly done or blocked, the commit, test evidence, assumptions made
- Total data downloaded
- The threshold study summary and candidate values
- What the owner should check first in the morning, and questions only the owner can answer
- Anything in `docs/` that looked wrong or incomplete

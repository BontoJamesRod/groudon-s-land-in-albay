# Mayon Radar Watch

- Windows and PowerShell. Activate the environment first: `.venv\Scripts\Activate.ps1` (Python 3.12).
- Tests: `pytest` from the repo root. Local site: `python -m http.server 8000 --directory site`.
- The planning docs in `docs/` are the spec: 04 design, 05 data files, 06 file contract, 07 tasks, 08 tests. Don't edit them unless the owner asks.
- Never commit `raw/`, `*.h5`, `pipeline/out/` or credentials. Never print Earthdata credentials.
- Never push or merge to `main` unless the owner asks.
- The owner is a Python beginner: keep code simple and explain radar steps in plain comments.
- The owner set the final thresholds on 2026-11-01, and lifted the blind cutoff to open the Oct 31 passes only. Never open NISAR products acquired on or after 2026-11-01 (UTC) unless the owner moves `BLIND_CUTOFF` again.

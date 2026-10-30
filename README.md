# Mayon Radar Watch

A web app that shows, after every NISAR radar satellite pass, where Mayon Volcano put new material and which river channels and towns are near it. Built for the NASA Space Apps Challenge 2026, "Dancing with the SARs".

This is not an official warning service. Follow PHIVOLCS and your LGU.

## Folders

| Folder | What's in it |
| --- | --- |
| `docs/` | Planning documents: brief, PRD, design, roadmap, tests |
| `pipeline/` | Python code that downloads and processes NISAR data |
| `site/` | The public website, deployed to GitHub Pages |
| `raw/` | Downloaded NISAR files (not committed) |

## Setup on Windows

1. Create a virtual environment: `py -3.12 -m venv .venv`
2. Activate it: `.venv\Scripts\Activate.ps1`
3. Install packages: `pip install -r pipeline/requirements.txt`
4. Run the tests: `pytest`
5. Check NISAR access: `python pipeline/mrw/check_access.py`
6. Run the site locally: `python -m http.server 8000 --directory site`, then open http://localhost:8000

## Data

NISAR data: NASA–ISRO, distributed by the Alaska Satellite Facility (ASF DAAC). Products are labeled provisional.

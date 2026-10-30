# Mayon Radar Watch

A web app that shows, after every NISAR radar satellite pass, where Mayon Volcano put new material and which river channels and towns are near it. Built for the NASA Space Apps Challenge 2026, "Dancing with the SARs".

**This is not an official warning service. Follow PHIVOLCS and your LGU.**

## How it works

A Python pipeline compares two NISAR passes from the same track, 12 days or more apart. It looks at two signals:

- **Brightness change:** how much the ground's radar reflection changed, in dB (from GCOV products).
- **Coherence loss:** how much less alike the two passes are than the previous two (from GUNW products).

Where both signals pass their thresholds, the app shows high confidence. Where only one does, it shows low confidence. The pipeline writes small files into `site/data/`, and the website reads them in the visitor's browser. There is no server.

The detection thresholds are PROVISIONAL until they are reviewed, and channel lines aren't in the app yet.

## Folders

| Folder | What's in it |
| --- | --- |
| `docs/` | Planning documents: brief, PRD, design, roadmap, tests |
| `pipeline/mrw/` | Python code that downloads and processes NISAR data |
| `pipeline/sites/` | One settings file per site |
| `pipeline/context/` | Source files for boundaries, events and validation sheets |
| `pipeline/reports/` | Analysis reports |
| `pipeline/out/` | Processed pairs before publishing (not committed) |
| `site/` | The public website, deployed to GitHub Pages |
| `raw/` | Cropped NISAR data and the download log (not committed) |

## Setup on Windows

1. Create a virtual environment: `py -3.12 -m venv .venv`
2. Activate it: `.venv\Scripts\Activate.ps1`
3. Install packages: `pip install -r pipeline/requirements.txt`
4. Run the tests: `pytest`
5. Check NISAR access: `python pipeline/mrw/check_access.py`

Step 5 asks for your NASA Earthdata login the first time and saves it in your home folder, never in this project.

## Run the site

```powershell
python -m http.server 8000 --directory site
```

Then open <http://localhost:8000>.

## Run the pipeline

```powershell
# Rebuild towns, land, events and sources for a site
python pipeline/mrw/context.py mayon

# Process one pair into pipeline/out/, using the names of its two GCOV products
python pipeline/mrw/export.py mayon <before GCOV granule> <after GCOV granule>

# Copy a checked pair into site/data/
python pipeline/mrw/publish.py mayon <pair id>

# Write a validation sheet to pipeline/out/validation_drafts/, or publish it once reviewed
python pipeline/mrw/validation.py mayon <pair id>
python pipeline/mrw/validation.py mayon <pair id> --publish

# Check everything in site/data/ against the data contract
python pipeline/mrw/contract_check.py
```

Publishing only changes files on your computer. A pair reaches the public site when `main` is pushed and CI passes.

Until the final thresholds are set, the pipeline refuses every product acquired on or after 2026-10-30 (`BLIND_CUTOFF` in `pipeline/mrw/search.py`), so the thresholds can't be influenced by the eruption data.

## Data sources

- **Radar:** NISAR data, NASA–ISRO, distributed by the Alaska Satellite Facility (ASF DAAC). Products are labeled provisional.
- **Town borders and land:** NAMRIA and PSA via OCHA COD-AB, packaged by [faeldon/philippines-json-maps](https://github.com/faeldon/philippines-json-maps), CC BY-IGO.
- **Background map:** Esri World Imagery.
- **Map library:** [Leaflet](https://leafletjs.com/) 1.9.4, copied into `site/vendor/`.
- **Events:** PHIVOLCS, through the news reports linked in `pipeline/context/mayon_events.json`.

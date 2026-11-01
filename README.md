# Mayon Radar Watch

A web app that watches how Mayon Volcano's river channels change between NISAR radar satellite passes. It compares radar images from the same track, usually 12 days apart, and maps where fresh ash, rock and lava may have landed. A channel timeline ranks the channels that the owner has confirmed by how much changed since the last pass. The Oct 30, 2026 eruption is one chapter of that story, and two pairs in Panama show the same engine on another continent. Built for the NASA Space Apps Challenge 2026, "Dancing with the SARs".

**This is not an official warning service. Follow PHIVOLCS and your LGU.**

## How it works

A Python pipeline compares two NISAR passes from the same track, 12 days or more apart. It uses two signals:

- **Brightness change:** how much the ground's radar reflection changed, in dB (from GCOV products).
- **Coherence loss:** how much less alike the two passes are than the previous two (from GUNW products).

Brightness change alone flags a spot. Coherence loss only raises a flagged spot to high confidence, and it never adds area. The pipeline writes small files into `site/data/`, and the website reads them in the visitor's browser. There is no server.

The detection thresholds are final, set on 2026-11-01 before the post-eruption passes were opened. The NISAR products are still PROVISIONAL.

Channel lines come from OpenStreetMap, © OpenStreetMap contributors. The project owner checked them by eye, and only those lines are used (`pipeline/reports/owner-checks.md`). `channels.geojson` and `channel_areas.json` under `site/data/sites/mayon/` are available under the [ODbL](https://opendatacommons.org/licenses/odbl/).

## Folders

| Folder | What's in it |
| --- | --- |
| `docs/` | Planning documents: brief, PRD, design, roadmap, tests |
| `plans/` | The owner's run plans, kept as written |
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

## License and credits

The code and documentation are under the [Apache-2.0 license](LICENSE), with the copyright notice in [NOTICE](NOTICE). The published radar layers in `site/data/sites/*/pairs/` are under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), credited to Mayon Radar Watch and NASA–ISRO NISAR data via ASF. Data files under their own licenses, such as ODbL and CC BY-SA 4.0, aren't covered by either. [CREDITS.md](CREDITS.md) lists every data source, library and tool with its license, and says which files fall under which terms.

## Data sources

- **Radar:** NISAR data, NASA–ISRO, distributed by the Alaska Satellite Facility (ASF DAAC). Products are labeled provisional.
- **Town borders and land:** Mayon: NAMRIA and PSA via OCHA COD-AB, packaged by [faeldon/philippines-json-maps](https://github.com/faeldon/philippines-json-maps), CC BY-IGO. Panama: [geoBoundaries](https://www.geoboundaries.org/), CC BY-SA 4.0.
- **Background map:** Esri World Imagery.
- **Map library:** [Leaflet](https://leafletjs.com/) 1.9.4, copied into `site/vendor/`.
- **Events:** PHIVOLCS, through the news reports linked in `pipeline/context/mayon_events.json`.

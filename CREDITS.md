# Credits and licenses

**The code and documentation in this repository are under the [Apache-2.0 license](LICENSE), with the copyright notice in [NOTICE](NOTICE). The data isn't.** The published radar layers are under CC BY 4.0 for Mayon and CC BY-SA 4.0 for Panama, and each other data source keeps its own terms, listed here. Apache-2.0 doesn't cover data files under ODbL, CC BY-SA 4.0, CC BY-IGO or any other license below, and it gives you no rights to them. If you reuse those files, follow their terms.

This list is a project record, not legal advice.

## Which license covers which files

| Files | Terms |
| --- | --- |
| Code and documentation we wrote: `site/js`, `site/css`, `site/*.html`, `pipeline/mrw`, `pipeline/reports/*.py`, `pipeline/tests`, `docs`, `.github` | Apache-2.0 |
| `site/data/sites/mayon/channels.geojson`, `channel_areas.json` | ODbL 1.0, © OpenStreetMap contributors. Share-alike applies |
| `pipeline/context/`: `channel_name_candidates*`, `channel_test_sites*`, `mayon_waterways_osm_candidate.geojson`, `osm_*.geojson` | ODbL 1.0, © OpenStreetMap contributors. Share-alike applies |
| `site/data/sites/panama/towns.geojson`, `land.geojson`, and `pipeline/context/panama_boundaries.json` | CC BY-SA 4.0, geoBoundaries. Share-alike applies |
| `site/data/sites/mayon/towns.geojson`, `land.geojson`, and `pipeline/context/mayon_boundaries.json` | CC BY-IGO, NAMRIA and PSA via OCHA COD-AB |
| Radar layers (images and value grids) and pair records in `site/data/sites/mayon/pairs/` | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Credit: Mayon Radar Watch and NASA–ISRO NISAR data via ASF |
| Radar layers (images and value grids) and pair records in `site/data/sites/panama/pairs/` | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Credit: Mayon Radar Watch and NASA–ISRO NISAR data via ASF; geoBoundaries. Share-alike applies |
| `channel_histogram.json` in those folders | ODbL 1.0, © OpenStreetMap contributors, because it's counted inside strips built on OpenStreetMap lines. Share-alike applies |
| `validation.json` in those folders | Not under CC BY 4.0: it cites other people's sources, by name and link, under their own terms |
| `site/vendor/leaflet-1.9.4/` | BSD-2-Clause, with its own `LICENSE` file |
| `pipeline/tests/e2e/vendor/axe-core-4.14.0/` | MPL-2.0, with its own `LICENSE` files |

## Reusing the radar layers

The radar layers are made from NISAR data, which is free and open. The results are provisional and aren't an official warning. Credit them as:

- **Mayon:** "Mayon Radar Watch and NASA–ISRO NISAR data via ASF, CC BY 4.0."
- **Panama:** "Mayon Radar Watch and NASA–ISRO NISAR data via ASF; geoBoundaries, CC BY-SA 4.0."

The layers mark sea as no data, using each site's land shape. Panama's shape is CC BY-SA 4.0 geoBoundaries data, which is why its layers carry share-alike. Mayon's is CC BY-IGO (NAMRIA and PSA via OCHA COD-AB), which has no share-alike.

## Data sources

The ids are the rows in [`site/data/sources.json`](site/data/sources.json).

| Source | Provider | License or terms | Used for | Id |
| --- | --- | --- | --- | --- |
| [NISAR GCOV and GUNW](https://nisar-docs.asf.alaska.edu/nisar-intro/) | NASA and ISRO, distributed by the Alaska Satellite Facility (ASF DAAC) | Free and open NASA Earth science data; no separate license named | The radar layers | `nisar_asf` |
| [GPM IMERG Late Run daily](https://gpm.nasa.gov/data/policy), `GPM_3IMERGDL` version 07 | NASA Goddard, through NASA GES DISC | Free, no license named; the GPM data policy asks for acknowledgement | The channel test only. Not published | `gpm_imerg` |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) channel lines | OpenStreetMap contributors | ODbL 1.0 | The published channels | `channel_lines` |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) waterways, places and quarries | OpenStreetMap contributors | ODbL 1.0 | Candidates and the channel test. Not published | `osm_analysis` |
| [geoBoundaries gbOpen](https://www.geoboundaries.org/), Panama ADM2 | geoBoundaries | CC BY-SA 4.0 | Panama's borders and land | `pa_admin_boundaries` |
| [Philippine boundaries](https://github.com/faeldon/philippines-json-maps) | NAMRIA and PSA via OCHA COD-AB, packaged by faeldon/philippines-json-maps | CC BY-IGO | Mayon's towns | `ph_admin_boundaries` |
| [Philippine coastline](https://github.com/faeldon/philippines-json-maps), from the same boundaries | NAMRIA and PSA via OCHA COD-AB, packaged by faeldon/philippines-json-maps | CC BY-IGO | Mayon's coastline | `ph_coastline` |
| [ESA WorldCover 2021](https://esa-worldcover.org/) | European Space Agency | CC BY 4.0 | The false-alarm study only. Not published | `esa_worldcover_2021` |
| [Copernicus DEM GLO-30](https://registry.opendata.aws/copernicus-dem/) | European Space Agency, Copernicus programme (produced using Copernicus WorldDEM-30, DLR and Airbus) | Copernicus DEM GLO-30 licence, free with attribution | The false-alarm study only. Not published | `copernicus_dem_glo30` |
| [Esri World Imagery](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer) | Esri | Esri terms of use, with attribution | The background map, loaded from Esri and not stored here | `esri_world_imagery` |
| [PHIVOLCS advisory of 16 January 2026, by GMA News](https://www.gmanetwork.com/news/topstories/regions/973047/phivolcs-issues-lahar-warning-for-mayon-volcano-amid-ada/story/) | PHIVOLCS | Names only, cited from the source | Channel names | `channel_names` |
| [PHIVOLCS lahar advisory of 16 January 2026, by DZRH News](https://dzrh.com.ph/post/phivolcs-issues-lahar-warning-at-mayon-volcano-as-tropical-storm-ada-brings-heavy-rains) | PHIVOLCS | Names only, cited from the source | Channel names | `channel_names_dzrh` |
| [PHIVOLCS Mayon Volcano Bulletin of 24 March 2000](https://wovodat.phivolcs.dost.gov.ph/cm_image/bulletin/MVBU_20000324070000.pdf) | PHIVOLCS | Names only, cited from the source | Channel names | `channel_names_bulletin` |

Events and validation sources are cited with links, row by row, in each site's `events.json` and in the validation records. Their text and images aren't copied here.

**Citation:** For the mission, ASF's guide points to the [NISAR Mission Science Users' Handbook](https://doi.org/10.48577/jpl.UD4HV3). Rain data is credited to NASA Goddard and NASA GES DISC, as the GPM data policy asks.

## Libraries in this repository

| Library | Version | License | Used for |
| --- | --- | --- | --- |
| [Leaflet](https://leafletjs.com/) | 1.9.4 | BSD-2-Clause | The map, on the public site |
| [axe-core](https://github.com/dequelabs/axe-core) | 4.14.0 | MPL-2.0 | Accessibility tests only |

## Python packages

These are installed by `pip` and aren't copied into this repository. Python itself is under the PSF license. The licenses are as each package declares them in its metadata, at the versions installed on 2026-11-01. Some packages bundle other libraries in their binary wheels, such as GDAL in rasterio and HDF5 in h5py, under those libraries' own terms.

Listed in `pipeline/requirements.txt`:

| Package | Version | License |
| --- | --- | --- |
| aiohttp | 3.14.5 | Apache-2.0 AND MIT |
| asf_search | 14.1.0 | BSD |
| earthaccess | 0.19.0 | MIT |
| fsspec | 2026.9.0 | BSD-3-Clause |
| h5netcdf | 1.8.2 | BSD-3-Clause |
| h5py | 3.16.0 | BSD-3-Clause |
| ipykernel | 7.4.0 | BSD-3-Clause |
| matplotlib | 3.11.2 | Matplotlib license (based on PSF) |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| pillow | 13.0.0 | MIT-CMU |
| pyproj | 3.8.0 | MIT |
| pytest | 9.2.0 | MIT |
| pytest-playwright | 0.10.0 | Apache-2.0 |
| rasterio | 1.5.2 | BSD-3-Clause |
| scipy | 1.18.1 | BSD-3-Clause |
| shapely | 2.2.0 | BSD-3-Clause |
| tzdata | 2026.6 | Apache-2.0 |
| xarray | 2026.9.0 | Apache-2.0 |

Installed because those packages need them:

| Package | Version | License |
| --- | --- | --- |
| affine | 3.0.1 | BSD-3-Clause |
| aiobotocore | 3.10.0 | Apache-2.0 |
| aiohappyeyeballs | 2.7.1 | PSF-2.0 |
| aioitertools | 0.13.0 | MIT |
| aiosignal | 1.4.0 | Apache-2.0 |
| asttokens | 3.0.2 | Apache-2.0 |
| attrs | 26.1.0 | MIT |
| botocore | 1.43.117 | Apache-2.0 |
| bounded-pool-executor | 0.0.3 | MIT |
| certifi | 2026.10.23 | MPL-2.0 |
| charset-normalizer | 3.5.2 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| colorama | 0.4.6 | BSD |
| comm | 0.2.3 | BSD-3-Clause |
| contourpy | 1.4.0 | BSD-3-Clause |
| cycler | 0.12.1 | BSD-3-Clause |
| dateparser | 1.4.3 | BSD-3-Clause |
| debugpy | 1.8.22 | MIT |
| executing | 2.3.0 | MIT |
| fonttools | 4.68.0 | MIT |
| frozenlist | 1.8.0 | Apache-2.0 |
| greenlet | 3.5.6 | MIT AND PSF-2.0 |
| idna | 3.20 | BSD-3-Clause |
| importlib_resources | 7.1.0 | Apache-2.0 |
| iniconfig | 2.3.1 | MIT |
| ipython | 9.18.0 | BSD-3-Clause |
| ipython_pygments_lexers | 1.1.1 | BSD |
| jedi | 0.20.1 | MIT |
| jmespath | 1.1.0 | MIT |
| jupyter_client | 8.10.0 | BSD-3-Clause |
| jupyter_core | 5.9.1 | BSD-3-Clause |
| kiwisolver | 1.5.1 | BSD-3-Clause |
| matplotlib-inline | 0.2.2 | BSD-3-Clause |
| multidict | 7.2.1 | Apache-2.0 |
| multimethod | 2.1 | Apache-2.0 |
| nest-asyncio2 | 1.7.4 | BSD |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pandas | 3.1.0 | BSD-3-Clause |
| parso | 0.8.7 | MIT |
| pip | 26.2.2 | MIT |
| platformdirs | 4.14.0 | MIT |
| playwright | 1.64.1 | Apache-2.0 |
| pluggy | 1.7.0 | MIT |
| pqdm | 0.2.0 | MIT |
| prompt_toolkit | 3.0.53 | BSD |
| propcache | 0.5.4 | Apache-2.0 |
| psutil | 7.2.2 | BSD-3-Clause |
| pure_eval | 0.2.4 | MIT |
| pyee | 14.0.0 | MIT |
| Pygments | 2.21.0 | BSD-2-Clause |
| pyparsing | 3.3.3 | MIT |
| python-cmr | 0.13.0 | MIT |
| python-dateutil | 2.9.0.post0 | Apache-2.0 or BSD-3-Clause |
| python-slugify | 9.1.3 | MIT |
| pytz | 2026.6 | MIT |
| pyzmq | 27.2.0 | BSD-3-Clause |
| regex | 2026.9.29 | Apache-2.0 AND CNRI-Python |
| requests | 2.34.2 | Apache-2.0 |
| s3fs | 2026.9.0 | BSD |
| six | 1.17.0 | MIT |
| stack-data | 0.6.3 | MIT |
| tenacity | 9.2.1 | Apache-2.0 |
| text-unidecode | 1.3 | Artistic-1.0 or GPL-2.0-or-later (recipient's choice) |
| tinynetrc | 1.3.1 | MIT |
| tornado | 6.6 | Apache-2.0 |
| tqdm | 4.70.1 | MPL-2.0 AND MIT |
| traitlets | 5.16.1 | BSD-3-Clause |
| typing_extensions | 4.16.0 | PSF-2.0 |
| tzlocal | 5.4.5 | MIT |
| urllib3 | 2.8.0 | MIT |
| wcwidth | 0.9.4 | MIT |
| wrapt | 2.5.2 | BSD-2-Clause |
| yarl | 1.25.1 | Apache-2.0 |

## Tools

| Tool | License or terms | Used for |
| --- | --- | --- |
| [Playwright](https://playwright.dev/) with Chromium | Apache-2.0; Chromium is BSD-3-Clause | Browser tests |
| [Gitleaks](https://github.com/gitleaks/gitleaks) and its GitHub Action | MIT for the tool; see the action's own terms | Scanning for secrets |
| GitHub Actions and GitHub Pages, with the `actions/*` workflow steps | GitHub's terms; the steps are MIT | Tests and hosting |
| [Earthdata Login and NASA Earthdata search](https://www.earthdata.nasa.gov/) | NASA's terms | Finding and downloading data |
| [Overpass API](https://overpass-api.de/) | Its own usage policy; the data is ODbL | Reading OpenStreetMap |
| [Google Earth Pro](https://www.google.com/earth/versions/) | Google's terms | The owner's check of channel lines. Nothing from it is copied here |
| [Claude Code](https://claude.com/claude-code) | Anthropic's terms | Writing code and documents, with the owner reviewing |

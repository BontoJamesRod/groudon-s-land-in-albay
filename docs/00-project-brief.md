# Project Brief: Mayon Radar Watch

| Version | Status | Last updated | Based on |
| --- | --- | --- | --- |
| 0.3 | Draft | 2026-10-31 | Project idea, chat discussion, progress notes (`mayon_radar_watch_progress.md`), challenge checklist (`dancing-with-the-sars-checklist.md`) |

## 1. Summary

Mayon Radar Watch is a web app that answers one question after every NISAR satellite pass: where did Mayon put new material, and which river channels and towns is it near? It compares NASA–ISRO NISAR radar images taken 12 days apart, maps fresh ash, rock and lava deposits, and lines them up with the channels that drain the volcano and the towns along them. It is built first as an entry for the NASA Space Apps Challenge 2026 "Dancing with the SARs" challenge (Nov 14–15, 2026), with the Oct 30, 2026 eruption as its showcase, and the same engine runs on a second site on another continent. Radar sees through clouds, ash and darkness, so the map stays current in typhoon season, when normal satellite photos are blocked.

## 2. Problem Statement

| Item | Description |
| --- | --- |
| Who | Communities along the river channels that drain Mayon, and the barangay and LGU officials who brief them |
| Problem | After an eruption, fresh ash, rock and lava sit on Mayon's slopes and in its gullies. Heavy rain can carry that material down the channels as lahars; PHIVOLCS warned of lahars after the Oct 30, 2026 eruption ([Manila Bulletin](https://mb.com.ph/2026/10/30/mayon-volcano-alert-status-raised-to-level-3)). People can't see where new material landed or which channels it sits in: clouds and ash block normal satellite photos, and NISAR radar data comes as multi-gigabyte files that need expert tools. |
| Current workaround | [TBD] Not answered yet (Open Question 1) |
| Cost of the problem | [TBD] for today's workaround (Open Question 2). Context: Typhoon Reming in 2006 left about 1,200 people dead or missing in Albay ([Inquirer](https://newsinfo.inquirer.net/?p=850250)). |

## 3. Target Users

| User type | Description | Main pain points |
| --- | --- | --- |
| Residents along Mayon's channels | People in towns whose river channels drain the volcano: Legazpi, Daraga, Camalig, Guinobatan, Ligao, Santo Domingo, Malilipot and Tabaco ([PHIVOLCS channel list via ReliefWeb](https://reliefweb.int/report/philippines/philippines-mayon-volcano-update-23-mar-2000)) | Can't see where new material landed or whether their channel holds it |
| Barangay and LGU disaster officials | Officials who brief residents and plan evacuations | Need a simple, honest picture they can explain to others |
| Space Apps judges (secondary) | Judges scoring Impact, Creativity, Validity, Relevance and Presentation | Need to see every challenge requirement (R1–R8 in the checklist) met in the app and demo |

## 4. Goals and Success Metrics

| G-ID | Goal | Metric | Target | Timeframe |
| --- | --- | --- | --- | --- |
| G-01 | Suggestion: Submit a complete, eligible entry to Dancing with the SARs | Challenge requirements R1–R8 visibly met in the app and demo | 8 of 8 | Before the local deadline, Nov 15, 2026 |
| G-02 | Suggestion: Show the Oct 30, 2026 eruption in real NISAR data | Post-eruption pairs (track 104 or 111) processed and live in the app | At least 1 pair | By Nov 7, 2026 |
| G-03 | Suggestion: Make radar readable for non-experts | Albay residents or LGU staff who can correctly say where new material is and which channel it's in, after 2 minutes with the app | At least 7 of 10 people tested | By Nov 30, 2026 |

## 5. Core Features

Requirement IDs (R1–R8) refer to Section 1 of the challenge checklist. Feature IDs are permanent; removed features stay in the table, marked Removed.

| F-ID | Feature | One-line description | Priority (Must / Should / Could) |
| --- | --- | --- | --- |
| F-01 | Interactive map | Pan and zoom a map of the Mayon area with town borders and the 6 km Permanent Danger Zone (R1) | Must |
| F-02 | Place readout | Search a town or tap the map to see distance to the crater, danger-zone status, new material nearby and how confident the result is (R1, R8) | Must |
| F-03 | Pass timeline | Step through every same-track 12-day pair since June 2026, including the July 14 pyroclastic flow and the Oct 30 eruption (R4) | Must |
| F-04 | Before/after view | Swipe between the radar images of two dates (R4, R5) | Must |
| F-05 | New-material layer | Areas where NISAR GCOV brightness change and coherence loss agree between two passes, with legend, units and confidence (R2, R3, R5, R6) | Must |
| F-06 | Ground-movement layer | Line-of-sight movement in cm from NISAR GUNW, labeled "within the noise" when no clear signal shows | Could |
| F-07 | Flood layer | Open water in the Albay lowlands after typhoons, using the same change engine | Could |
| F-08 | "What am I looking at?" panel | How radar sees, what the colors mean, confidence levels, limitations, and that official warnings come from PHIVOLCS and LGUs (R8) | Must |
| F-09 | Data sources panel | Product name, granule ID, acquisition dates, provisional status and link for every layer (R2, R3) | Must |
| F-10 | Second showcase site | The same new-material engine run on one site on another continent (R7) | Must |
| F-11 | Public app and code | A public link and a public code repository that judges can open | Must |
| F-12 | Validation check | At least one result compared with an independent source, such as the gullies named in PHIVOLCS bulletins for the same dates | Should |
| F-13 | Mobile-friendly, color-blind-safe design | Readable on a phone, with a color-blind-safe palette | Should |
| F-14 | Point time series | Chart of change at a tapped point across every pass since June 2026 | Could |
| F-15 | Past-years water comparison | Removed in v0.2: moved to Out of Scope | Removed |
| F-16 | Filipino and Bikol language option | Switch the app's text to Filipino or Bikol | Could |
| F-17 | Automatic updates | A scheduled pipeline that finds and processes new NISAR passes | Could |
| F-18 | More change types and places | Farming shifts, wetland loss and earthquakes at other sites | Could |
| F-19 | Channels and towns | Draw the PHIVOLCS-named channels that drain Mayon and the towns along each; tapping a changed area shows which channel it's in (R8) | Must |

## 6. Out of Scope

From the challenge checklist:

- Using Sentinel-1 or optical imagery as the main data. The challenge requires NISAR; other data is context or validation only.

Suggestion (not yet confirmed, see Open Question 3):

- Predicting lahars, eruptions or floods. The app shows where new material is, never where or when a lahar will flow.
- Official warnings or evacuation advice. PHIVOLCS and LGUs own those.
- Computing flow paths from elevation data. Channels are drawn from the PHIVOLCS-named list instead.
- Live or real-time data. The app updates after each 12-day pass, about 2–3 days later.
- Recording ground shaking. That is PHIVOLCS's seismic network.
- Measuring how fast water flows, or water in narrow rivers in the dry season.
- Comparisons with years before calibrated NISAR data (before June 17, 2026).
- User accounts and collecting personal data.
- A native mobile app. The project is web only.

## 7. Constraints

| Type | Constraint |
| --- | --- |
| Timeline | Hackathon Nov 14–15, 2026 (fixed), submitted before the local-time deadline. First post-eruption NISAR products expected around Nov 3–4, 2026. Backup showcase: the July 14, 2026 pyroclastic flow pair. |
| Budget | [TBD] Not stated (Open Question 6) |
| Team | Builder: the project owner, a beginner in Python and radar data, working on Windows with Google Colab and VS Code. Presenter: a teammate who presents and records the demo but does not build. |
| Platform | Web app that works on phones. Runs on localhost during development, then as a public site for judges and users. |
| Language and locale | English (required for the submission). Filipino and Bikol later. Time zone Asia/Manila. |
| Compliance | Space Apps submission rules: video demo of 30 seconds or less, or a deck of 7 slides or fewer; English; public links; all members registered on a local event. Every dataset cited by name, link and date. NISAR products labeled provisional. The app states it is not an official warning. Earthdata login details are never put in code or files. |

## 8. Tech Preferences

- Python in Google Colab and Jupyter notebooks for processing (`asf_search`, `earthaccess`, `h5py`, `rasterio`)
- NISAR L2 products from ASF DAAC: `NISAR_L2_GCOV_PROVISIONAL_V1` and `NISAR_L2_GUNW_PROVISIONAL_V1`
- Leaflet 1.9.4 for the web map
- A static website on GitHub Pages, Netlify or Vercel
- GitHub Actions for scheduled data updates (later), with Earthdata credentials stored as repository secrets
- VS Code on Windows for development

## 9. Glossary

| Term | Meaning |
| --- | --- |
| NISAR | NASA–ISRO Synthetic Aperture Radar satellite. Its L-band radar (24 cm wavelength) images the same place every 12 days. |
| SAR | Synthetic aperture radar: a satellite sends microwave pulses and measures what bounces back. Works through clouds, ash and darkness. |
| GCOV | NISAR brightness product: how strongly each patch of ground reflects the radar |
| GUNW | NISAR interferogram product: the phase difference between two passes. Also carries the coherence layer. |
| New material | Fresh ash, rock, lava or pyroclastic deposits that the app detects as change between two passes |
| Coherence | How similar two radar images are, from 0 to 1. Fresh deposits make it drop sharply. |
| dB (decibel) | Log scale for radar brightness. Change in dB = 10 × log10(after / before). |
| Line-of-sight (LOS) | Movement toward or away from the satellite, not straight up or down |
| Track / frame | The satellite's path and the section of it. Only images from the same track, frame and orbit direction are compared. |
| Pass / pair | One satellite visit / two passes compared with each other |
| Channel / gully | A river valley that drains the volcano, such as Mi-isi, Bonga or Basud |
| Permanent Danger Zone (PDZ) | The 6 km radius around Mayon's summit that people may not enter |
| Lahar | A flow of volcanic debris and water down river channels, often triggered by heavy rain |
| Uson | Local word for pyroclastic density currents: fast clouds of hot gas, ash and rock |
| PROVISIONAL | NISAR products that are calibrated but not fully validated yet |
| ASF DAAC | Alaska Satellite Facility, the NASA archive that distributes NISAR data |

## 10. Assumptions

- Fresh deposits on Mayon show up as both brightness change and coherence loss at NISAR's 10–20 m pixels. This is tested first, on the July 14 and Oct 30 events.
- NISAR keeps passing every 12 days on tracks 104, 111 and 39, and products appear 36–72 hours after each pass.
- Channel lines can be traced from open map data and matched to the channel names in PHIVOLCS bulletins.
- All processing happens in Python before publishing, so the website itself is static.
- The app collects no personal data.
- The presenter registers for the same local event and is listed on the team.

## 11. Open Questions

| # | Question | Affects |
| --- | --- | --- |
| 1 | How do people near Mayon find out today what changed in their area and channel? | Section 2 |
| 2 | What goes wrong with that today? | Section 2 |
| 3 | Do you agree with the suggested out-of-scope list? | Section 6 |
| 4 | Which second site, on another continent? It should have a clear surface change in 2026 NISAR data (an eruption, landslide or flood), so the same engine applies. | F-10 |
| 5 | Do the Space Apps and Legazpi local event rules allow code written before Nov 14? This decides how much existing work can be used, so check it first. | Section 7 |
| 6 | What is the monthly budget? Suggestion: ₱0, using free tiers (Colab, GitHub Pages, NASA Earthdata). | Section 7 |
| 7 | What brightness change and coherence drop count as "new material"? Decide before the eruption data arrives (around Nov 3). | F-05 |
| 8 | What do the official Objectives, Potential Considerations and Resources sections add? (Checklist Section 11) | Section 5 |
| 9 | What are the team name and the presenter's name? | Section 7 |
| 10 | Who will help test the app with residents or LGU staff? | G-03 |

## 12. Conflicts with Earlier Documents

None. This is the only document so far. The earlier progress notes described a personal project free of hackathon rules; this brief follows the Space Apps requirements, as decided on Oct 31, 2026.

## 13. Revision History

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-31 | First draft |
| 0.2 | 2026-10-31 | Refocused on one question: where new material landed, and which channels and towns are near it. Added F-19 Channels and towns. F-05 now requires brightness change and coherence loss to agree. F-06 and F-07 lowered to Could. Removed F-15. Dropped the water-shortage user group. Added a backup showcase pair and Open Questions 7 and 10. |
| 0.3 | 2026-10-31 | Put F-15 back in the feature table marked Removed, as the kit's ID rules require. |

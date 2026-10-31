// Every piece of interface text in one place, for review against FR-038 (docs/04 section 3).
// The wording test in pipeline/tests/test_wording.py reads this file.

export const STRINGS = {
  // Main screen (SCR-01)
  appName: "Mayon Radar Watch",
  searchButton: "Search",
  helpButton: "What am I looking at?",
  compareButton: "Compare",
  previous: "Previous",
  next: "Next",
  radarPassList: "Radar pass",
  mapLabel: "Map of the selected site",
  panelLabel: "Radar pass and legend",
  drawerShow: "Show legend and details (PROVISIONAL results)",
  drawerHide: "Hide legend and details",
  disclaimer: "This is not an official warning. Follow PHIVOLCS and your LGU.",
  loadingRadar: "Loading radar data…",
  backgroundUnavailable: "Background map unavailable",
  noPairs: "No radar passes processed yet for this site",
  latestPass: "This is the latest pass",
  passLoadError: "Couldn't load this pass. Try again.",
  siteLoadError: (name) => `Couldn't load ${name}. Try again.`,
  siteListError: "Couldn't load the site list. Try again.",
  pairRange: (before, after) => `${before} to ${after}`,
  pairLabel: (range, timeZone, track, frame, direction) =>
    `${range} (${timeZone}), track ${track}, frame ${frame}, ${direction}`,
  optionWithEvents: (range, names) => `${range}: ${names}`,
  eventInPeriod: (names) => `Event in this period: ${names}`,
  layerUnits: (units) => `Units: ${units}`,
  totalArea: (km2) => `Total detected area: ${km2.toFixed(2)} km²`,
  nothingDetected: (before, after) => `No new material detected between ${before} and ${after}`,
  boundaryAttribution: "Boundaries: NAMRIA and PSA via OCHA COD-AB (CC BY-IGO)",
  tileAttribution: "Tiles &copy; Esri",

  // Readout card (SCR-02)
  readoutLoading: "Reading radar values…",
  readoutGridError: "Couldn't load radar values. Try again.",
  noRadarData: "No radar data here",
  noDataReasons: {
    253: "a slope the radar can't see",
    254: "sea",
    255: "outside radar coverage",
  },
  insideDangerZone: "Inside the Permanent Danger Zone. Entry is not allowed.",
  outsideDangerZone: "Outside the danger zone",
  outsideTowns: "Outside the mapped towns",
  distanceToSummit: (km) => `Distance to summit: ${km.toFixed(1)} km`,
  noNewMaterial: "No new material detected. Confidence: none",
  beyondReach: (km) => `Not checked: this map only looks within ${km} km of the summit`,
  classWithConfidence: (label, confidence) => `${label}. Confidence: ${confidence}`,
  pairDates: (before, after) => `Radar passes: ${before} to ${after}`,
  close: "Close",
  retry: "Retry",

  // Town search (SCR-03)
  searchTitle: "Find a town",
  searchField: "Town name",
  searchSubmit: "Search",
  searchHint: "Type a town name",
  searchNoMatch: "No town found. Try another name or tap the map.",

  // Compare view (SCR-04)
  compareLoading: "Loading radar images…",
  compareMissing: "Before/after images not available for this pair",
  compareBefore: (date) => `Before: ${date}`,
  compareAfter: (date) => `After: ${date}`,
  compareDivider: "Move the divider between the before and after images",

  // "What am I looking at?" (SCR-05)
  helpHowRadarTitle: "How radar sees",
  helpHowRadar: [
    "The NISAR satellite sends radio waves to the ground and measures what comes back. It works through clouds and at night.",
    "Comparing two passes from the same angle shows where the ground changed. Fresh rock and ash change how brightly the ground reflects, and they make the two passes look less alike.",
  ],
  helpColorsTitle: "What each color means",
  helpNoColor: "No color: no new material detected, or no radar data.",
  helpClasses: [
    "Orange: possible new material (one signal). Confidence: low",
    "Dark orange: new material (both signals). Confidence: high",
  ],
  helpConfidenceTitle: "Confidence levels",
  helpConfidence: [
    "None: neither radar signal changed enough.",
    "Low: one signal changed, or there was no coherence data to check the second signal. Rain, wind or farming can also cause this.",
    "High: both signals changed in the same place: the brightness, and how alike the passes are.",
  ],
  helpLimitsTitle: "Limitations",
  helpLimits: [
    "A pass usually comes every 12 days, and sometimes the gap is longer. The map can be days old and shows nothing about what happens next. Longer gaps can show more change.",
    "Some colored spots are not new material. Crops, rain and building work can look the same to the radar.",
    "At Mayon, this map only looks within 10 km of the summit, shown by the white dotted ring. It can't show anything beyond that, including in towns further away.",
    "Steep slopes facing away from the radar can't be seen, and small deposits can be missed.",
    "The radar products are provisional, and the detection thresholds are provisional until they are reviewed.",
  ],
  helpOfficialTitle: "Official warnings",
  helpOfficial: "For warnings and advice, follow PHIVOLCS and your LGU.",
  helpOfficialLink: "PHIVOLCS website",
  helpOfficialUrl: "https://www.phivolcs.dost.gov.ph/",

  // Data sources (SCR-06)
  sourcesButton: "Data sources",
  sourcesTitle: "Data sources",
  sourcesRadarTitle: "Radar data",
  sourcesContextTitle: "Context data",
  sourcesEmpty: "Pick a radar pass to see its sources",
  sourcesLoading: "Loading sources…",
  sourcesError: "Couldn't load sources. Try again.",
  sourcesProduct: (type, maturity) => `${type}, ${maturity}`,
  sourcesDates: (dates) => `Acquired: ${dates}`,
  sourcesContextLine: (name, provider, license) => `${name}. Source: ${provider}. License: ${license}.`,
  sourcesContextLink: "Open source",

  // "How we checked this" (SCR-07)
  checkButton: "How we checked this",
  checkTitle: "How we checked this",
  checkEmpty: "Not yet checked against an independent source",
  checkLoading: "Loading check…",
  checkError: "Couldn't load this check. Try again.",
  checkSource: (name, date) => `Source: ${name}, ${date}`,
  checkSourceLink: "Open source",
  checkColumns: ["Place", "Reported by the source", "Detected by the app", "Note"],
  checkYes: "Yes",
  checkNo: "No",
  checkDetected: { yes: "Yes", no: "No", not_visible: "Not visible to radar" },

  // Site picker (SCR-08)
  pickerTitle: "Choose a site",
  pickerEmpty: "No sites available yet",
  pickerOption: (name, country) => `${name}, ${country}`,
};

// Put the text into the page's fixed elements: `data-text` sets what it shows,
// and `data-label` sets what a screen reader says.
export function applyPageStrings(root = document) {
  root.querySelectorAll("[data-text]").forEach((element) => {
    element.textContent = STRINGS[element.dataset.text];
  });
  root.querySelectorAll("[data-label]").forEach((element) => {
    element.setAttribute("aria-label", STRINGS[element.dataset.label]);
  });
}

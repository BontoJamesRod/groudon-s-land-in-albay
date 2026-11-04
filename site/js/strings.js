// Every piece of interface text in one place, for review against FR-038 (docs/04 section 3).
// The wording test in pipeline/tests/test_wording.py reads this file.

const COURT_M2 = 28 * 15; // one basketball court, as the owner set it (FR-079)

// A channel's area as basketball courts, to picture its size.
function courtsText(km2) {
  if (km2 === 0) return "0 basketball courts";
  const courts = Math.round((km2 * 1000000) / COURT_M2);
  if (courts === 0) return "less than 1 basketball court";
  return `about ${courts.toLocaleString("en-US")} basketball court${courts === 1 ? "" : "s"}`;
}

// A share of the ground as words. A tiny share never reads as 0%.
function shareText(share) {
  if (share > 0 && share < 0.001) return "under 0.1%";
  return `${(share * 100).toFixed(1)}%`;
}

export const STRINGS = {
  // Main screen (SCR-01)
  appName: "Mayon Radar Watch",
  searchButton: "Search",
  // The search box in the top bar (FR-093). Search only finds towns, so it says so.
  searchBox: "Find a town",
  helpButton: "What am I looking at?",
  compareButton: "Compare",
  previous: "Previous",
  next: "Next",
  radarPassList: "Radar pass",
  mapLabel: "Map of the selected site",
  panelLabel: "Radar pass and legend",
  drawerShow: "Show legend and details (PROVISIONAL radar products, within 10 km of the summit)",
  drawerHide: "Hide legend and details",
  disclaimer: "This is not an official warning. Follow PHIVOLCS and your LGU.",
  disclaimerShort: "Not an official warning · Follow PHIVOLCS",
  // Info popovers (FR-088): the button says "More about" and what it explains.
  infoLabel: (what) => `More about ${what}`,
  infoWhat: {
    disclaimer: "this warning", pass: "this radar pass", legend: "the colors", area: "the area",
    chart: "the chart", card: "this spot", credits: "the map credits",
    channelLayer: "the channel lines", channels: "the channel list", bars: "the bars", gap: "this pass's gap",
  },
  // The side column's cards (F-24, FR-094).
  passTitle: "This pass",
  layersTitle: "Layers",
  histogramSection: "Brightness change",
  passSub: (track, partOfDay, time) => `Track ${track} · ${partOfDay} pass, ${time}`,
  partOfDay: { morning: "morning", afternoon: "afternoon", evening: "evening" },
  areaNumber: (km2) => km2.toFixed(2),
  areaUnit: "km²",
  areaCaption: (reach) => (reach ? `new material within ${reach} km of the summit` : "new material"),
  areaCourtsLine: (km2) => { const text = courtsText(km2); return text[0].toUpperCase() + text.slice(1); },
  confidenceArea: (word, km2) => `${word} ${km2.toFixed(2)} km²`,
  channelsChecked: (count) => `${count} checked by eye`,
  zoneAlways: "Always shown",
  // The phone sheet (FR-095).
  showAll: (count) => `Show all ${count} channels and layers`,
  showMore: "Show the layers and the chart",
  creditsButton: "Credits",
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
  pairShort: (before, after, names) => `${before} – ${after}${names ? ` · ${names}` : ""}`,
  optionWithEvents: (range, names) => `${range}: ${names}`,
  optionWithGap: (text, note) => `${text} (${note})`,
  gapNote: (days) => `${days}-day gap, not comparable`,
  eventInPeriod: (names) => `Event in this period: ${names}`,
  legendColors: "What each color means:",
  legendShort: { high: "Likely", low: "Possible" },
  areaUnits: "Areas are in km². Channel areas also show basketball courts.",
  productsWithCoherence: "GCOV + GUNW",
  productsWithoutCoherence: "GCOV",
  productLabel: (products, before, after) => `NISAR ${products} · before ${before} · after ${after}`,
  totalArea: (km2) => `Total detected area: ${km2.toFixed(2)} km²`,
  nothingDetected: (before, after) => `No new material detected between ${before} and ${after}`,
  satelliteCredit: 'Imagery: <a href="https://cloudless.eox.at">EOxCloudless</a> by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2024), <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>',
  satelliteUnavailable: "Satellite map unavailable. Showing the relief map.",
  satelliteLoading: (waiting) => `Loading satellite imagery: ${waiting} ${waiting === 1 ? "tile" : "tiles"} to go`,
  basemapLabel: "Background map",
  basemapRelief: "Relief",
  basemapSatellite: "Satellite",
  reliefCredit: 'Relief: <a href="https://registry.opendata.aws/copernicus-dem/">Copernicus DEM GLO-30</a>, produced using Copernicus WorldDEM-30 &copy; DLR e.V. 2010-2014 and &copy; Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved',
  // FR-091: the folded credit line. Everything is still listed in its popover.
  creditsShortOsm: 'Map data <a href="https://www.openstreetmap.org/copyright">&copy; OpenStreetMap contributors</a> and others',
  creditsShort: "Map credits",
  marksNote: "Small spots are drawn larger than life so they can be seen. The areas don't change.",

  // Readout card (SCR-02)
  readoutLoading: "Reading radar values…",
  readoutGridError: "Couldn't load radar values. Try again.",
  noRadarData: "No radar data here",
  noDataReasons: {
    253: "the radar product marked this spot as invalid",
    254: "sea",
    255: "outside radar coverage",
  },
  insideDangerZone: "Inside the Permanent Danger Zone. Entry is not allowed.",
  outsideDangerZone: "Outside the danger zone",
  outsideTowns: "Outside the mapped towns",
  distanceToSummit: (km) => `Distance to summit: ${km.toFixed(1)} km`,
  inOrNearChannel: (names) => `New material detected in or near ${names}`,
  notInChannel: "Not in a named channel on this map",
  channelTowns: (names) => `Towns along this channel: ${names}`,
  noNewMaterial: "No new material detected. Confidence: none",
  beyondReach: (km) => `Not checked: this map only looks within ${km} km of the summit`,
  classWithConfidence: (label, confidence) => `${label}. Confidence: ${confidence}`,
  pairDates: (before, after) => `Radar passes: ${before} to ${after}`,
  cardHeadline: (place, result) => (result ? `${place}: ${result}` : place),
  resultShort: { none: "no new material", low: "possible new material", high: "likely new material" },
  noDataShort: (reason) => `no radar data (${reason})`,
  notCheckedShort: "not checked",
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
    "Orange: possible new material (brightness only). Confidence: low",
    "Dark orange: likely new material (brightness and coherence agree). Confidence: high",
  ],
  helpConfidenceTitle: "Confidence levels",
  helpConfidence: [
    "None: the brightness didn't change enough. A change only in how alike the passes are isn't enough to mark a spot.",
    "Low: the brightness changed, but the passes didn't become much less alike, or there was no coherence data to check that. Rain, wind or farming can also cause this.",
    "High: the brightness changed, and the passes also became less alike in the same place.",
  ],
  helpLimitsTitle: "Limitations",
  // In the list below and in the Panama list: why the chart's flag line can't be moved (FR-074).
  helpLimits: [
    "A pass usually comes every 12 days, and sometimes the gap is longer. The map can be days old and shows nothing about what happens next. Longer gaps can show more change.",
    "Some colored spots are not new material. Crops, rain and building work can look the same to the radar.",
    "At Mayon, this map only looks within 10 km of the summit, shown by the white dotted ring. It can't show anything beyond that, including in towns further away.",
    "Steep slopes facing away from the radar can't be seen, and small deposits can be missed.",
    "The radar products are provisional. The detection thresholds are set, but they haven't been checked against field reports.",
    "Only channels the project owner has checked are drawn. Other channels also drain Mayon, and they aren't on this map.",
    "The flag line can't be moved here. It was fixed before the eruption data was opened, and letting it move would undo that.",
  ],
  helpOfficialTitle: "Official warnings",
  helpOfficial: "For warnings and advice, follow PHIVOLCS and your LGU.",
  helpOfficialLink: "PHIVOLCS website",
  helpOfficialUrl: "https://www.phivolcs.dost.gov.ph/",
  helpMoreTitle: "More",

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

  // Channel layer (SCR-01)
  channelLayerLabel: "Channels",
  channelsUnavailable: "Channels unavailable",
  channelLineNote: "Solid line: checked. Dashed white line: past the reach of this map, so not checked.",
  channelSources: "Names: PHIVOLCS. Lines: OpenStreetMap contributors (ODbL), confirmed by the project owner.",
  channelsTitle: "Channels since the last pass",
  channelsLoading: "Loading channel changes…",
  channelsError: "Couldn't load channel changes. Try again.",
  channelsEmpty: "No confirmed channels yet for this site",
  channelsLatest: (range, track) => `Most changed first, since the last pass: ${range}, track ${track}`,
  histogramTitle: "How much the ground's brightness changed",
  histogramAlt: (threshold, share) => `Chart of brightness change. Most of the ground sits near no change. Flag lines at plus and minus ${threshold} decibels. ${shareText(share)} of the checked land is past them.`,
  histogramBin: (low, high, share) => `${low} to ${high} dB: ${shareText(share)} of the ground`,
  histogramDarker: "Darker",
  histogramNoChange: "No change",
  histogramBrighter: "Brighter",
  histogramSentence: (share) => `Most of the ground barely changed. The shaded edges changed by more than the line, so they're flagged: ${shareText(share)} of the checked land.`,
  histogramNothingFlagged: "All of the checked land stayed inside the lines, so none of it is flagged.",
  histogramShare: (share) => `${shareText(share)} flagged`,
  histogramShareNone: "None flagged",
  histogramScaleNote: (site) => `${site.detection_reach_km ? `Land within ${site.detection_reach_km} km of the summit.` : "Land in this site."} Bar heights use a square-root scale, so the small edges can be seen.`,
  histogramChannelNote: (name) => `Thin line: the ${name} strip, scaled to its own ground. Bars: all the checked land.`,
  histogramMissing: "Brightness chart not available for this pair",
  channelArea: (km2) => `${km2.toFixed(3)} km²`,
  channelCourts: courtsText,
  channelCourtSize: `1 basketball court = 28 × 15 m = ${COURT_M2} m².`,
  channelNoData: "No radar data",
  channelsHow: (halfWidth, reach) => `This is the area flagged as possible or likely new material in a strip ${halfWidth} m on each side of the line${reach ? `, within ${reach} km of the summit` : ""}.`,
  channelsOnlyConfirmed: "Only channels the project owner has checked are listed. Other channels also drain Mayon.",
  channelBack: "All channels",
  channelBarsLead: "Area flagged in each radar pass. Tap one to show that pass on the map.",
  channelBarLabel: (range, track) => `${range}, track ${track}`,
  channelBarsScale: "All channels use the same scale, so their bars can be compared.",
  // A channel's page (F-24, FR-096).
  channelPassTitle: (title, track) => `${title} · Track ${track}`,
  channelAreaNumber: (km2) => km2.toFixed(3),
  everyPassSince: (month) => `Every pass since ${month}`,
  newestFirst: "Newest first",
  channelChartNote: "All channels use the same scale. Pick a pass in the list below to show it on the map.",
  channelTracks: (main, others) => `Darker bars: track ${main}. Lighter bars: track ${others}.`,
  channelGapBars: "A dashed, hollow bar is a pass with a longer gap, so it can't be compared with the others.",
  channelRowTrack: (track) => `Track ${track}`,
  channelSourceName: "Name:",
  channelSourceLine: "Line:",
  channelOsm: "© OpenStreetMap contributors",
  channelOsmLicense: "(ODbL)",
  channelNotChecked: "Not checked",
  channelNotCheckedNote: (reach) => `The dashed white part of this channel is more than ${reach} km from the summit. It's not checked and not counted, which doesn't mean that nothing changed there.`,
  channelCredit: 'Channel lines: <a href="https://www.openstreetmap.org/copyright">&copy; OpenStreetMap contributors</a> (ODbL)',

  // Site picker (SCR-08)
  pickerTitle: "Choose a site",
  pickerEmpty: "No sites available yet",
  pickerOption: (name, country) => `${name}, ${country}`,
};

// A site whose map shows change in general, not volcanic material. Its `wording_set` in
// sites.json is "plain_change". Anything not listed here is the same for every site.
const PLAIN_CHANGE = {
  drawerShow: "Show legend and details (PROVISIONAL radar products)",
  disclaimer: "This is not an official warning. Follow SINAPROC and your local authorities.",
  disclaimerShort: "Not an official warning · Follow SINAPROC",
  areaUnits: "Areas are in km².",
  areaCaption: () => "changed",
  areaCourtsLine: null,
  resultShort: { none: "no change", low: "possible change", high: "likely change" },
  nothingDetected: (before, after) => `No change detected between ${before} and ${after}`,
  noNewMaterial: "No change detected. Confidence: none",
  helpHowRadar: [
    STRINGS.helpHowRadar[0],
    "Comparing two passes from the same angle shows where the ground changed. Changed ground reflects the radar differently, and it can make the two passes look less alike.",
  ],
  helpNoColor: "No color: no change detected, or no radar data.",
  helpClasses: [
    "Orange: possible change (brightness only). Confidence: low",
    "Dark orange: likely change (brightness and coherence agree). Confidence: high",
  ],
  helpLimits: [
    STRINGS.helpLimits[0],
    "This map shows where the ground changed, not why. Crops, rain and building work can look the same to the radar.",
    "Steep slopes facing away from the radar can't be seen, and small changes can be missed.",
    STRINGS.helpLimits[4],
    "The flag line can't be moved here. It was fixed before this site was processed, with no tuning for this site, and letting it move would undo that.",
  ],
  helpOfficial: "For warnings and advice, follow SINAPROC and your local authorities.",
  helpOfficialLink: "SINAPROC website",
  helpOfficialUrl: "https://www.sinaproc.gob.pa/",
};

// The text for one site: the shared text, with that site's wording on top.
export function textFor(site) {
  return site && site.wording_set === "plain_change" ? { ...STRINGS, ...PLAIN_CHANGE } : STRINGS;
}

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

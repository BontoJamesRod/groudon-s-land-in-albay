// Starts the app and connects its parts: load the site list, then the first site,
// then its latest pair. Switching sites loads the new site before removing the old
// one, so the previous site stays on screen if loading fails (FR-042).

import { createCompare } from "./compare.js";
import { loadPair, loadSiteData, loadSites } from "./data.js";
import { createNewMaterialLayer } from "./layers.js";
import { createMap, RADAR_PANE } from "./map.js";
import { createPanel, fillCheck, fillHelp, fillPicker, fillSources } from "./panels.js";
import { createReadout } from "./readout.js";
import { createSearch } from "./search.js";
import { applyPageStrings, STRINGS } from "./strings.js";
import { createTimeline } from "./timeline.js";

const byId = (id) => document.getElementById(id);

// What is on screen now.
const app = { sites: [], site: null, map: null, pair: null, compare: null };

function showError(text, retry) {
  byId("app-message").textContent = text;
  byId("app-retry").hidden = false;
  byId("app-retry").onclick = retry;
  byId("loading").hidden = true;
}

function clearMessage() {
  byId("app-message").textContent = "";
  byId("app-retry").hidden = true;
}

function setUpCompare(map, site) {
  return createCompare(map, {
    view: byId("compare-view"),
    divider: byId("compare-divider"),
    beforeLabel: byId("compare-before"),
    afterLabel: byId("compare-after"),
    close: byId("compare-close"),
    message: byId("compare-message"),
  }, site, (hidden) => {
    map.getPane(RADAR_PANE).style.display = hidden ? "none" : "";
  });
}

function setUpSearch(map, site, siteData, readout) {
  const search = createSearch({
    panel: byId("search-panel"),
    form: byId("search-form"),
    input: byId("search-input"),
    suggestions: byId("search-suggestions"),
    message: byId("search-message"),
    close: byId("search-close"),
  }, siteData.towns, (town) => {
    const { label_lat: lat, label_lon: lon, name } = town.properties;
    map.setView([lat, lon], Math.max(map.getZoom(), site.default_zoom), { animate: false });
    readout.open(lat, lon, name);
  });
  byId("search-button").onclick = search.open;
}

// Connect the pair list, map layer, readout and compare view for the site on screen.
function setUpPairs(map, site, siteData, readout) {
  if (siteData.pairs.length === 0) {
    byId("app-message").textContent = STRINGS.noPairs;
    byId("panel").hidden = true;
    return Promise.resolve();
  }
  byId("panel").hidden = false;
  const showPair = createNewMaterialLayer(map, {
    toggle: byId("layer-toggle"),
    title: byId("legend-title"),
    rows: byId("legend-rows"),
    area: byId("legend-area"),
    summary: byId("summary"),
  }, site);
  byId("compare-button").onclick = () => app.compare.open(app.pair);
  return createTimeline({
    list: byId("pair-list"),
    label: byId("pair-label"),
    events: byId("pair-events"),
    previous: byId("previous"),
    next: byId("next"),
    message: byId("timeline-message"),
    retry: byId("timeline-retry"),
  }, site, siteData.pairs, siteData.events, async (summary) => {
    const pair = await loadPair(site.id, summary.id);
    await showPair(pair);
    app.compare.close();
    app.compare.clearMessage();
    app.pair = pair;
    readout.setPair(pair);
  });
}

// Replace what is on screen with an already loaded site.
async function showSite(site, siteData) {
  clearMessage();
  byId("readout-card").hidden = true;
  byId("search-panel").hidden = true;
  if (app.compare) app.compare.close();
  if (app.map) app.map.remove();
  app.map = null;
  app.pair = null;
  app.site = site;
  byId("site-name").textContent = site.name;
  const map = createMap(site, siteData, byId("background-notice"));
  app.map = map;
  app.compare = setUpCompare(map, site);
  const readout = createReadout({
    card: byId("readout-card"),
    body: byId("readout-body"),
    close: byId("readout-close"),
    retry: byId("readout-retry"),
  }, site, siteData.towns);
  map.on("click", (event) => readout.open(event.latlng.lat, event.latlng.lng));
  setUpSearch(map, site, siteData, readout);
  await setUpPairs(map, site, siteData, readout);
  byId("loading").hidden = true;
}

// Load a site first, and only then touch the screen.
async function openSite(site) {
  clearMessage();
  byId("loading").hidden = false;
  let siteData;
  try {
    siteData = await loadSiteData(site.id);
  } catch (problem) {
    console.error(problem.message);
    showError(STRINGS.siteLoadError(site.name), () => openSite(site));
    return;
  }
  try {
    await showSite(site, siteData);
  } catch (problem) {
    // Bad data can break the map itself, and the visitor still needs a way to try again.
    console.error(problem);
    showError(STRINGS.siteLoadError(site.name), () => openSite(site));
  }
}

function setUpPanels() {
  const help = createPanel(byId("help-panel"), (body) => fillHelp(body, () => app.pair));
  const sources = createPanel(byId("sources-panel"), (body) => fillSources(body, () => app.pair, app.site.time_zone));
  const picker = createPanel(byId("picker-panel"), (body) => fillPicker(body, app.sites, (site) => {
    byId("picker-panel").close();
    if (site.id !== app.site.id) openSite(site);
  }));
  const check = createPanel(byId("check-panel"), (body) => fillCheck(body, () => app.pair));
  byId("help-button").onclick = help;
  byId("check-button").onclick = () => app.site && check();
  byId("sources-button").onclick = () => app.site && sources();
  byId("site-name").onclick = () => app.site && picker();
}

async function start() {
  clearMessage();
  byId("loading").hidden = false;
  try {
    app.sites = await loadSites();
    if (app.sites.length === 0) throw new Error("The site list is empty");
  } catch (problem) {
    console.error(problem.message);
    showError(STRINGS.siteListError, start);
    return;
  }
  await openSite(app.sites[0]);
}

applyPageStrings();
setUpPanels();
start();

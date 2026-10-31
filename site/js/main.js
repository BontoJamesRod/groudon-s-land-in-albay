// Starts the app and connects its parts: load the site list, then the first site,
// then its latest pair. Switching sites loads the new site before removing the old
// one, so the previous site stays on screen if loading fails (FR-042).

import { createChannels } from "./channels.js";
import { createCompare } from "./compare.js";
import { loadPair, loadSiteData, loadSites } from "./data.js";
import { createDrawer } from "./drawer.js";
import { createChannelLayer, createNewMaterialLayer, showChannelLegend } from "./layers.js";
import { createMap, RADAR_PANE, showStartView } from "./map.js";
import { createPanel, fillCheck, fillHelp, fillPicker, fillSources } from "./panels.js";
import { createReadout } from "./readout.js";
import { createSearch } from "./search.js";
import { applyPageStrings, STRINGS, textFor } from "./strings.js";
import { createTimeline } from "./timeline.js";

const byId = (id) => document.getElementById(id);

// What is on screen now.
const app = { sites: [], site: null, map: null, pair: null, compare: null, channels: null, drawer: null, openRequest: 0 };

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

// Draw the site's channels, or say why there are none. A tap on a line opens the card for that spot.
function setUpChannelLayer(map, siteData, readout) {
  const elements = {
    legend: byId("channel-legend"),
    layer: byId("channel-layer"),
    toggle: byId("channel-toggle"),
    note: byId("channel-note"),
    unavailable: byId("channels-unavailable"),
  };
  if (siteData.channels && siteData.channels.features.length) {
    createChannelLayer(map, elements, siteData.channels, (channel, latlng) => {
      readout.open(latlng.lat, latlng.lng, undefined, channel);
    });
  } else {
    showChannelLegend(elements, siteData.channelsFailed ? "unavailable" : "none");
  }
}

// The Channels button shows only for a site with channel data (US-024/AC-2).
function setUpChannels(map, site, siteData) {
  const button = byId("channels-button");
  button.hidden = site.channel_strip_half_width_m == null;
  app.channels = button.hidden ? null : createChannels(map, {
    panel: byId("channel-panel"),
    title: byId("channel-title"),
    back: byId("channel-back"),
    close: byId("channel-close"),
    status: byId("channel-status"),
    retry: byId("channel-retry"),
    body: byId("channel-body"),
    opener: button,
  }, site, siteData, () => map.invalidateSize({ animate: false }), (pairId) => {
    const list = byId("pair-list");
    list.value = pairId;
    list.dispatchEvent(new Event("change"));
  });
  button.onclick = () => app.channels.open();
}

// Connect the pair list, map layer, readout and compare view for the site on screen.
function setUpPairs(map, site, siteData, readout) {
  if (siteData.pairs.length === 0) {
    byId("app-message").textContent = STRINGS.noPairs;
    byId("panel").hidden = true;
    return Promise.resolve();
  }
  byId("panel").hidden = false;
  // Showing the panel made the map shorter, and Leaflet only notices that when told.
  map.invalidateSize({ pan: false });
  showStartView(map, site);
  const showPair = createNewMaterialLayer(map, {
    toggle: byId("layer-toggle"),
    title: byId("legend-title"),
    rows: byId("legend-rows"),
    area: byId("legend-area"),
    summary: byId("summary"),
  }, site);
  // There is nothing to compare until the first pair has loaded.
  byId("compare-button").disabled = true;
  byId("compare-button").onclick = async () => {
    await app.compare.open(app.pair);
    // On a phone the images need the room. An error stays readable in the open drawer.
    if (!byId("compare-view").hidden) app.drawer.close();
  };
  const siteIsShown = () => app.site === site;
  return createTimeline({
    list: byId("pair-list"),
    label: byId("pair-label"),
    events: byId("pair-events"),
    gap: byId("pair-gap"),
    previous: byId("previous"),
    next: byId("next"),
    message: byId("timeline-message"),
    retry: byId("timeline-retry"),
  }, site, siteData.pairs, siteData.events, siteIsShown, async (summary, isCurrent) => {
    try {
      const pair = await loadPair(site.id, summary.id);
      if (!isCurrent()) return;
      await showPair(pair, isCurrent);
      if (!isCurrent()) return;
      app.pair = pair;
      app.compare.pairChanged(pair);
      if (app.channels) app.channels.pairChanged(pair);
      byId("compare-button").disabled = false;
      readout.setPair(pair);
      // The legend has just filled in, so the panel may have grown and the map shrunk. Leaflet
      // only notices when told, and otherwise the map jumps at some later moment.
      map.invalidateSize({ animate: false });
    } catch (problem) {
      if (app.channels && isCurrent()) app.channels.pairFailed();
      throw problem;
    }
  });
}

// Replace what is on screen with an already loaded site.
async function showSite(site, siteData) {
  clearMessage();
  byId("readout-card").hidden = true;
  byId("search-panel").hidden = true;
  if (app.compare) app.compare.close();
  if (app.channels) app.channels.close();
  if (app.map) app.map.remove();
  app.map = null;
  app.pair = null;
  app.site = site;
  byId("site-name").textContent = site.name;
  document.querySelector(".disclaimer").textContent = textFor(site).disclaimer;
  app.drawer.siteChanged();
  const map = createMap(site, siteData, byId("background-notice"));
  app.map = map;
  app.compare = setUpCompare(map, site);
  const readout = createReadout({
    card: byId("readout-card"),
    body: byId("readout-body"),
    close: byId("readout-close"),
    retry: byId("readout-retry"),
  }, site, siteData.towns, siteData.channels);
  map.on("click", (event) => readout.open(event.latlng.lat, event.latlng.lng));
  setUpChannelLayer(map, siteData, readout);
  setUpChannels(map, site, siteData);
  setUpSearch(map, site, siteData, readout);
  await setUpPairs(map, site, siteData, readout);
  byId("loading").hidden = true;
}

// Load a site first, and only then touch the screen.
async function openSite(site) {
  clearMessage();
  byId("loading").hidden = false;
  app.openRequest += 1;
  const thisRequest = app.openRequest; // only the site picked last may open
  let siteData;
  try {
    siteData = await loadSiteData(site);
    if (thisRequest !== app.openRequest) return;
  } catch (problem) {
    if (thisRequest !== app.openRequest) return;
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
  app.drawer = createDrawer(byId("panel"), byId("drawer-toggle"), () => {
    if (app.map) app.map.invalidateSize({ animate: false });
  }, () => app.site);
  const help = createPanel(byId("help-panel"), (body) => fillHelp(body, () => app.pair, app.site));
  const sources = createPanel(byId("sources-panel"), (body) => fillSources(body, () => app.pair, app.site));
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

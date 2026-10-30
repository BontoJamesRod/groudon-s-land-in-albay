// Starts the app: load the site list, then the first site, then its latest pair.

import { loadPair, loadSiteData, loadSites } from "./data.js";
import { createNewMaterialLayer } from "./layers.js";
import { createMap } from "./map.js";
import { createTimeline } from "./timeline.js";

const NO_PAIRS_MESSAGE = "No radar passes processed yet for this site";

const byId = (id) => document.getElementById(id);

function showError(text, retry) {
  byId("app-message").textContent = text;
  byId("app-retry").hidden = false;
  byId("app-retry").onclick = retry;
  byId("loading").hidden = true;
}

function clearError() {
  byId("app-message").textContent = "";
  byId("app-retry").hidden = true;
}

function setUpPairs(map, site, siteData) {
  if (siteData.pairs.length === 0) {
    byId("app-message").textContent = NO_PAIRS_MESSAGE;
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
  const timelineElements = {
    list: byId("pair-list"),
    label: byId("pair-label"),
    events: byId("pair-events"),
    previous: byId("previous"),
    next: byId("next"),
    message: byId("timeline-message"),
    retry: byId("timeline-retry"),
  };
  return createTimeline(timelineElements, site, siteData.pairs, siteData.events, async (pair) => {
    await showPair(await loadPair(site.id, pair.id));
  });
}

async function openSite(site) {
  byId("site-name").textContent = site.name;
  let siteData;
  try {
    siteData = await loadSiteData(site.id);
  } catch (problem) {
    console.error(problem.message);
    showError(`Couldn't load ${site.name}. Try again.`, () => openSite(site));
    return;
  }
  clearError();
  const map = createMap(site, siteData, byId("background-notice"));
  await setUpPairs(map, site, siteData);
  byId("loading").hidden = true;
}

async function start() {
  clearError();
  byId("loading").hidden = false;
  let sites;
  try {
    sites = await loadSites();
  } catch (problem) {
    console.error(problem.message);
    showError("Couldn't load the site list. Try again.", start);
    return;
  }
  if (sites.length === 0) {
    showError("Couldn't load the site list. Try again.", start);
    return;
  }
  await openSite(sites[0]);
}

start();

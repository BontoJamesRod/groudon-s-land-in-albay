// Tasks T-075 and T-076: the channel list, one channel's bars, and its strip on the map.
// The browser only shows these areas: the pipeline works them out (FR-064).

import { loadChannelAreas, loadChannels } from "./data.js";
import { channelLines } from "./layers.js";
import { STRIP_PANE } from "./map.js";
import { element } from "./panels.js";
import { STRINGS } from "./strings.js";
import { pairDates } from "./timeline.js";

const STRIP_STYLE = { color: "#22d3ee", weight: 1.5, opacity: 0.9, fillColor: "#22d3ee", fillOpacity: 0.22, interactive: false };
const FIT_PADDING_PX = 24;

// Largest first, ties by name, and channels with no radar data for that pair last (FR-061).
export function sortChannels(channels, areaOf) {
  return [...channels].sort((a, b) => {
    const [areaA, areaB] = [areaOf(a), areaOf(b)];
    if ((areaA === null) !== (areaB === null)) return areaA === null ? 1 : -1;
    return (areaB ?? 0) - (areaA ?? 0) || a.properties.name.localeCompare(b.properties.name);
  });
}

// `elements`: panel, title, back, close, status, retry, body, opener. `onResize` runs after the map
// changes size, and `onPickPair(id)` shows a pair on the map.
export function createChannels(map, elements, site, siteData, onResize, onPickPair) {
  const { pairs, towns } = siteData;
  let channels = siteData.channels; // null if the file failed when the site opened: it's tried again here
  let rows = null;
  let request = 0; // closing, or opening again, cancels a load that is still running
  let stripLayer = null; // what the open channel has on the map
  let selectedPairId = null;

  function areaRow(channel, pair) {
    return rows.find((row) => row.channel_id === channel.properties.id && row.pair_id === pair.id) || null;
  }

  // No row counts the same as no radar value: the area isn't known, so it must not read as 0.
  function flaggedArea(channel, pair) {
    const row = areaRow(channel, pair);
    return row && row.flagged_area_km2 !== null ? row.flagged_area_km2 : null;
  }

  // A message about the list or the view replaces it, unless `keepBody` says it's only a passing note.
  function showStatus(text, canRetry, keepBody = false) {
    elements.status.textContent = text;
    elements.retry.hidden = !canRetry;
    if (text && !keepBody) elements.body.replaceChildren();
  }

  function listRow(channel, latest) {
    const button = element("button", undefined, "channel-row");
    button.type = "button";
    const area = flaggedArea(channel, latest);
    button.onclick = () => showChannel(channel);
    button.append(element("span", channel.properties.name, "channel-row-name"),
      element("span", area === null ? STRINGS.channelNoData : STRINGS.channelArea(area)));
    const row = element("li");
    row.append(button);
    return row;
  }

  function removeStrip() {
    if (stripLayer) stripLayer.remove();
    stripLayer = null;
  }

  // The strip goes under the radar image, so that its color doesn't change the flagged cells.
  function drawStrip(channel) {
    removeStrip();
    const strip = L.geoJSON(channel.properties.strip_geometry, { style: STRIP_STYLE, pane: STRIP_PANE });
    stripLayer = L.layerGroup([strip, channelLines(channel)]).addTo(map);
    map.fitBounds(strip.getBounds(), { padding: [FIT_PADDING_PX, FIT_PADDING_PX], animate: false });
  }

  function markSelectedBar() {
    elements.body.querySelectorAll(".channel-bar").forEach((bar) => {
      if (bar.dataset.pair === selectedPairId) bar.setAttribute("aria-current", "true");
      else bar.removeAttribute("aria-current");
    });
  }

  // One pair's bar. All bars share one scale, so that a channel's bars can be compared with another's.
  function barRow(channel, pair, largest) {
    const area = flaggedArea(channel, pair);
    const button = element("button", undefined, "channel-bar");
    button.type = "button";
    button.dataset.pair = pair.id;
    const top = element("span", undefined, "channel-bar-top");
    top.append(element("span", STRINGS.channelBarLabel(pairDates(pair, site.time_zone), pair.track)),
      element("span", area === null ? STRINGS.channelNoData : STRINGS.channelArea(area), "channel-bar-value"));
    button.append(top);
    if (area !== null) {
      const fill = element("span", undefined, "channel-bar-fill");
      fill.style.width = `${largest ? (area / largest) * 100 : 0}%`;
      const track = element("span", undefined, "channel-bar-track");
      track.append(fill);
      button.append(track);
    }
    button.onclick = () => onPickPair(pair.id);
    const row = element("li");
    row.append(button);
    return row;
  }

  function townNames(channel) {
    return channel.properties.town_ids.map((id) => {
      const town = towns.features.find((item) => item.properties.id === id);
      return town ? town.properties.name : id;
    });
  }

  // SCR-14: one bar per published pair, in order of after date, with the strip on the map.
  function showChannel(channel) {
    elements.title.textContent = channel.properties.name;
    elements.back.hidden = false;
    showStatus("", false);
    const largest = Math.max(0, ...rows.map((row) => row.flagged_area_km2 ?? 0));
    const bars = element("ol", undefined, "channel-bars");
    bars.append(...pairs.map((pair) => barRow(channel, pair, largest)));
    elements.body.replaceChildren(
      element("p", STRINGS.channelTowns(townNames(channel).join(", ")), "channel-lead"),
      element("p", STRINGS.channelBarsLead, "channel-note"),
      bars,
      element("p", STRINGS.channelsHow(site.channel_strip_half_width_m, site.detection_reach_km), "channel-note"),
      element("p", STRINGS.channelBarsScale, "channel-note"),
    );
    markSelectedBar();
    elements.panel.scrollTop = 0;
    drawStrip(channel);
    elements.title.focus();
  }

  // SCR-13: the channels, most changed first, for the latest pair.
  function showList() {
    elements.title.textContent = STRINGS.channelsTitle;
    elements.back.hidden = true;
    removeStrip();
    if (channels.features.length === 0) {
      showStatus(STRINGS.channelsEmpty, false);
      return;
    }
    if (pairs.length === 0) {
      showStatus(STRINGS.noPairs, false);
      return;
    }
    showStatus("", false);
    const latest = pairs[pairs.length - 1];
    const sorted = sortChannels(channels.features, (channel) => flaggedArea(channel, latest));
    const list = element("ul", undefined, "channel-rows");
    list.append(...sorted.map((channel) => listRow(channel, latest)));
    elements.body.replaceChildren(
      element("p", STRINGS.channelsLatest(pairDates(latest, site.time_zone), latest.track), "channel-lead"),
      list,
      element("p", STRINGS.channelsHow(site.channel_strip_half_width_m, site.detection_reach_km), "channel-note"),
      element("p", STRINGS.channelsOnlyConfirmed, "channel-note"),
    );
  }

  // A failed load leaves the map as it was, and the panel offers another try (US-024/AC-3).
  async function load() {
    request += 1;
    const thisRequest = request;
    showStatus(STRINGS.channelsLoading, false);
    try {
      const loaded = channels || await loadChannels(site.id);
      const loadedRows = loaded.features.length ? await loadChannelAreas(site.id, loaded, pairs) : [];
      if (thisRequest !== request) return;
      channels = loaded;
      rows = loadedRows;
      showList();
    } catch (problem) {
      if (thisRequest !== request) return;
      console.error(problem.message);
      showStatus(STRINGS.channelsError, true);
    }
  }

  function setOpen(open) {
    elements.panel.hidden = !open;
    document.body.classList.toggle("channels-open", open);
    onResize();
  }

  function open() {
    setOpen(true);
    elements.title.focus();
    if (rows) showList();
    else load();
  }

  function close() {
    request += 1;
    removeStrip();
    setOpen(false);
  }

  elements.close.onclick = () => {
    close();
    elements.opener.focus();
  };
  elements.back.onclick = () => {
    showList();
    elements.title.focus();
  };
  elements.retry.onclick = load;

  // The map's pair changed, for example after tapping a bar.
  function pairChanged(pair) {
    selectedPairId = pair.id;
    markSelectedBar();
    if (rows) showStatus("", false, true);
  }

  // On a phone the pass controls are hidden behind this panel, so it has to say so itself.
  function pairFailed() {
    showStatus(STRINGS.passLoadError, false, true);
  }

  return { open, close, pairChanged, pairFailed };
}

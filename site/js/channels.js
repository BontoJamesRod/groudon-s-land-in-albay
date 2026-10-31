// Task T-075: the channel list. The browser only shows these areas: the pipeline works them out (FR-064).

import { loadChannelAreas, loadChannels } from "./data.js";
import { element } from "./panels.js";
import { STRINGS } from "./strings.js";
import { pairDates } from "./timeline.js";

// Largest first, ties by name, and channels with no radar data for that pair last (FR-061).
export function sortChannels(channels, areaOf) {
  return [...channels].sort((a, b) => {
    const [areaA, areaB] = [areaOf(a), areaOf(b)];
    if ((areaA === null) !== (areaB === null)) return areaA === null ? 1 : -1;
    return (areaB ?? 0) - (areaA ?? 0) || a.properties.name.localeCompare(b.properties.name);
  });
}

// `elements`: panel, title, back, close, status, retry, body. `onResize` runs after the map changes size.
export function createChannels(elements, site, siteData, onResize) {
  const { pairs } = siteData;
  let channels = siteData.channels; // null if the file failed when the site opened: it's tried again here
  let rows = null;
  let request = 0; // closing, or opening again, cancels a load that is still running

  function areaRow(channel, pair) {
    return rows.find((row) => row.channel_id === channel.properties.id && row.pair_id === pair.id) || null;
  }

  // No row counts the same as no radar value: the area isn't known, so it must not read as 0.
  function flaggedArea(channel, pair) {
    const row = areaRow(channel, pair);
    return row && row.flagged_area_km2 !== null ? row.flagged_area_km2 : null;
  }

  function showStatus(text, canRetry) {
    elements.status.textContent = text;
    elements.retry.hidden = !canRetry;
    if (text) elements.body.replaceChildren();
  }

  function listRow(channel, latest) {
    const button = element("button", undefined, "channel-row");
    button.type = "button";
    const area = flaggedArea(channel, latest);
    button.append(element("span", channel.properties.name, "channel-row-name"),
      element("span", area === null ? STRINGS.channelNoData : STRINGS.channelArea(area)));
    const row = element("li");
    row.append(button);
    return row;
  }

  // SCR-13: the channels, most changed first, for the latest pair.
  function showList() {
    elements.title.textContent = STRINGS.channelsTitle;
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
    setOpen(false);
  }

  elements.close.onclick = () => {
    close();
    elements.opener.focus();
  };
  elements.retry.onclick = load;

  return { open, close };
}

// Tasks T-075, T-076, T-077 and T-091: the channel list, one channel's bars, and its strip on the map.
// The browser only shows these areas: the pipeline works them out (FR-064).

import { loadChannelAreas, loadChannels } from "./data.js";
import { channelLines } from "./layers.js";
import { STRIP_PANE } from "./map.js";
import { element } from "./panels.js";
import { STRINGS } from "./strings.js";
import { gapNote, pairDates } from "./timeline.js";

const STRIP_STYLE = { color: "#22d3ee", weight: 1.5, opacity: 0.9, fillColor: "#22d3ee", fillOpacity: 0.22, interactive: false };
const FIT_PADDING_PX = 24;
// A shorter phone opens on the map: with the list open, too little of the map would show.
const SHORT_PHONE = "(max-width: 700px) and (max-height: 699px)";

// A label for what lies past the reach, at the middle of its longest stretch (FR-071).
function notCheckedLabel({ type, coordinates }) {
  const stretches = type === "LineString" ? [coordinates] : coordinates;
  const longest = stretches.reduce((best, stretch) => (stretch.length > best.length ? stretch : best));
  const [lon, lat] = longest[Math.floor(longest.length / 2)];
  return L.tooltip({ permanent: true, direction: "center", className: "channel-label not-checked-label", interactive: false })
    .setLatLng([lat, lon])
    .setContent(STRINGS.channelNotChecked);
}

// Largest first, ties by name, and channels with no radar data for that pair last (FR-061).
function sortChannels(channels, areaOf) {
  return [...channels].sort((a, b) => {
    const [areaA, areaB] = [areaOf(a), areaOf(b)];
    if ((areaA === null) !== (areaB === null)) return areaA === null ? 1 : -1;
    return (areaB ?? 0) - (areaA ?? 0) || a.properties.name.localeCompare(b.properties.name);
  });
}

// `elements`: panel, title, back, close, status, retry, body, opener. `onResize` runs after the map
// changes size, and `onPickPair(id)` shows a pair on the map.
export function createChannels(map, elements, site, siteData, onResize, onPickPair, onChannelChange) {
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
    const value = element("span", undefined, "channel-row-value");
    value.append(element("span", area === null ? STRINGS.channelNoData : STRINGS.channelArea(area), "channel-row-area"));
    if (area !== null) value.append(element("span", STRINGS.channelCourts(area), "channel-row-courts"));
    button.append(element("span", channel.properties.name, "channel-row-name"), value);
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
    const { strip_geometry: stripShape, not_checked_geometry: notChecked } = channel.properties;
    const strip = L.geoJSON(stripShape, { style: STRIP_STYLE, pane: STRIP_PANE });
    const parts = [strip, channelLines(channel)];
    const bounds = strip.getBounds();
    if (notChecked) {
      parts.push(notCheckedLabel(notChecked));
      bounds.extend(L.geoJSON(notChecked).getBounds());
    }
    stripLayer = L.layerGroup(parts).addTo(map);
    map.fitBounds(bounds, { padding: [FIT_PADDING_PX, FIT_PADDING_PX], animate: false });
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
      button.append(element("span", STRINGS.channelCourts(area), "channel-bar-courts"));
      const fill = element("span", undefined, "channel-bar-fill");
      fill.style.width = `${largest ? (area / largest) * 100 : 0}%`;
      const track = element("span", undefined, "channel-bar-track");
      track.append(fill);
      button.append(track);
    }
    const note = gapNote(pair);
    if (note) {
      button.classList.add("channel-bar-dim");
      button.append(element("span", note, "channel-bar-note"));
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
    onChannelChange(channel);
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
      element("p", STRINGS.channelCourtSize, "channel-note"),
    );
    if (channel.properties.not_checked_geometry) {
      elements.body.append(element("p", STRINGS.channelNotCheckedNote(site.detection_reach_km), "channel-note"));
    }
    markSelectedBar();
    elements.panel.scrollTop = 0;
    elements.panel.parentElement.scrollTop = 0; // on a desktop, the column around the panel scrolls
    drawStrip(channel);
    elements.title.focus();
  }

  function showListTitle() {
    elements.title.textContent = STRINGS.channelsTitle;
    elements.back.hidden = true;
    removeStrip();
  }

  // SCR-13: the channels, most changed first, for the latest pair.
  function showList() {
    onChannelChange(null);
    showListTitle();
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
    const lead = STRINGS.channelsLatest(pairDates(latest, site.time_zone), latest.track);
    const note = gapNote(latest);
    elements.body.replaceChildren(
      element("p", note ? STRINGS.optionWithGap(lead, note) : lead, "channel-lead"),
      list,
      element("p", STRINGS.channelsHow(site.channel_strip_half_width_m, site.detection_reach_km), "channel-note"),
      element("p", STRINGS.channelsOnlyConfirmed, "channel-note"),
      element("p", STRINGS.channelCourtSize, "channel-note"),
    );
  }

  // A failed load leaves the map as it was, and the panel offers another try (US-024/AC-3).
  async function load() {
    request += 1;
    const thisRequest = request;
    showListTitle();
    showStatus(STRINGS.channelsLoading, false);
    try {
      const loaded = channels || await loadChannels(site.id);
      // With no channels or no pairs there's nothing to look up, and the list says so.
      const loadedRows = loaded.features.length && pairs.length ? await loadChannelAreas(site.id, loaded, pairs) : [];
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

  // For when the site opens: the list appears, and the keyboard focus stays put (US-028/AC-3).
  function showAtStart() {
    if (!window.matchMedia(SHORT_PHONE).matches) show();
  }

  function show() {
    setOpen(true);
    if (rows) showList();
    else load();
  }

  function open() {
    show();
    elements.title.focus();
  }

  function close() {
    onChannelChange(null);
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
    if (elements.status.textContent === STRINGS.passLoadError) showStatus("", false, true);
  }

  // On a phone the pass controls are hidden behind this panel, so it has to say so itself.
  function pairFailed() {
    showStatus(STRINGS.passLoadError, false, true);
  }

  return { showAtStart, open, close, pairChanged, pairFailed };
}

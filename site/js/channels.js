// Tasks T-075, T-076, T-077 and T-091: the channel list, one channel's bars, and its strip on the map.
// The browser only shows these areas: the pipeline works them out (FR-064).

import { loadChannelAreas, loadChannels } from "./data.js";
import { channelLines } from "./layers.js";
import { STRIP_PANE } from "./map.js";
import { element } from "./panels.js";
import { newInfo } from "./popover.js";
import { STRINGS } from "./strings.js";
import { gapNote, pairDates, passTitle, shortMonth, startMonth } from "./timeline.js";

const STRIP_STYLE = { color: "#22d3ee", weight: 1.5, opacity: 0.9, fillColor: "#22d3ee", fillOpacity: 0.22, interactive: false };
const FIT_PADDING_PX = 24;

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

// `elements`: host (the side column), panel, title, back, info, lead, how, headMore (the towns and the
// pass card go there, under the name), status, retry, body, and the
// pass buttons under the map (previous, next), which a channel's page also drives.
// `onResize` runs after the map changes size, and `onPickPair(id)` shows a pair on the map.
export function createChannels(map, elements, site, siteData, onResize, onPickPair, onChannelChange) {
  const { pairs, towns } = siteData;
  let channels = siteData.channels; // null if the file failed when the site opened: it's tried again here
  let rows = null;
  let request = 0; // closing, or opening again, cancels a load that is still running
  let stripLayer = null; // what the open channel has on the map
  let selectedPairId = null;
  let openChannel = null; // the channel whose page is open
  let passCard = null; // the parts of that page's pass card that change with the pass

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

  // The largest area of any channel in any pair: every bar uses it, so all bars share one scale.
  function largestArea() {
    return Math.max(0, ...rows.map((row) => row.flagged_area_km2 ?? 0));
  }

  // A small bar on the shared scale. It only pictures the number beside it, so a screen reader skips it.
  function miniBar(area, largest, className) {
    const track = element("span", undefined, className);
    track.setAttribute("aria-hidden", "true");
    const fill = element("span", undefined, "channel-mini-fill");
    fill.style.width = `${largest && area ? (area / largest) * 100 : 0}%`;
    track.append(fill);
    return track;
  }

  // One row: the name and its towns, the area and courts, a small bar, and an arrow to its page.
  function listRow(channel, latest, largest) {
    const button = element("button", undefined, "channel-row");
    button.type = "button";
    const area = flaggedArea(channel, latest);
    button.onclick = () => showChannel(channel);
    const words = element("span", undefined, "channel-row-words");
    words.append(element("span", channel.properties.name, "channel-row-name"), element("span", townNames(channel).join(" · "), "channel-row-towns"));
    const value = element("span", undefined, "channel-row-value");
    value.append(element("span", area === null ? STRINGS.channelNoData : STRINGS.channelArea(area), "channel-row-area"));
    if (area !== null) value.append(element("span", STRINGS.channelCourts(area), "channel-row-courts"), miniBar(area, largest, "channel-mini"));
    const arrow = element("span", undefined, "chevron chevron-next");
    arrow.setAttribute("aria-hidden", "true");
    button.append(words, value, arrow);
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

  // The highlighted row and bar are always the pass on the map, and the row is brought into view (FR-080).
  function markSelectedBar() {
    elements.body.querySelectorAll(".channel-bar").forEach((bar) => {
      if (bar.dataset.pair === selectedPairId) {
        bar.setAttribute("aria-current", "true");
        bar.scrollIntoView({ block: "nearest" });
      } else {
        bar.removeAttribute("aria-current");
      }
    });
    elements.body.querySelectorAll(".channel-col").forEach((column) => {
      column.classList.toggle("channel-col-selected", column.dataset.pair === selectedPairId);
    });
  }

  // A pass's area in the channel, as the text a row or a bar's name uses.
  function areaText(area) {
    return area === null ? STRINGS.channelNoData : STRINGS.channelArea(area);
  }

  // The pass card: ‹ the selected pass ›, its area in this channel, its courts and how the strip is counted.
  // ‹ and › work like the pass buttons under the map, which the page hides.
  function buildPassCard() {
    const card = element("div", undefined, "card channel-pass");
    const head = element("div", undefined, "channel-pass-head");
    const title = element("p", undefined, "channel-pass-title");
    const step = (id, label, arrow, target) => {
      const button = element("button", undefined, "icon-button");
      button.type = "button";
      button.id = id;
      button.setAttribute("aria-label", label);
      const mark = element("span", undefined, `chevron ${arrow}`);
      mark.setAttribute("aria-hidden", "true");
      button.append(mark);
      button.onclick = () => target.click();
      return button;
    };
    head.append(step("channel-previous", STRINGS.previous, "chevron-back", elements.previous), title,
      step("channel-next", STRINGS.next, "chevron-next", elements.next));
    const number = element("p", undefined, "channel-pass-number");
    const courts = element("p", undefined, "channel-pass-courts");
    card.append(head, number, courts,
      element("p", STRINGS.channelsHow(site.channel_strip_half_width_m, site.detection_reach_km), "channel-note"));
    passCard = { card, title, number, courts };
    return card;
  }

  function showPassCard() {
    if (!passCard || !openChannel) return;
    const pair = pairs.find((item) => item.id === selectedPairId) || pairs[pairs.length - 1];
    const area = flaggedArea(openChannel, pair);
    passCard.title.textContent = STRINGS.channelPassTitle(passTitle(pair, site.time_zone), pair.track);
    if (area === null) {
      passCard.number.textContent = STRINGS.channelNoData;
    } else {
      passCard.number.replaceChildren(element("span", STRINGS.channelAreaNumber(area), "area-value"), " ",
        element("span", STRINGS.areaUnit, "area-unit"));
    }
    passCard.courts.textContent = area === null ? "" : STRINGS.areaCourtsLine(area);
  }

  // "Every pass since June": one bar per published pair, oldest on the left, on the shared scale.
  // It's a picture of the list below it, which holds the same numbers and the buttons, so a screen
  // reader skips it. Bars narrower than a finger can't be the buttons (FR-049).
  function passChart(channel, largest) {
    const mainTrack = pairs[pairs.length - 1].track;
    const columns = element("div", undefined, "channel-cols");
    const months = element("div", undefined, "channel-months");
    let lastMonth = null;
    for (const pair of pairs) {
      const area = flaggedArea(channel, pair);
      const column = element("span", undefined, "channel-col");
      column.dataset.pair = pair.id;
      column.classList.toggle("channel-col-other", pair.track !== mainTrack);
      column.classList.toggle("channel-col-gap", gapNote(pair) !== null);
      column.classList.toggle("channel-col-none", area === null);
      const fill = element("span", undefined, "channel-col-fill");
      fill.style.height = `${largest && area ? (area / largest) * 100 : 0}%`;
      column.append(fill);
      columns.append(column);
      const month = shortMonth(pair, site.time_zone);
      months.append(element("span", month === lastMonth ? "" : month));
      lastMonth = month;
    }
    const picture = element("div", undefined, "card channel-chart");
    const drawing = element("div", undefined, "channel-drawing");
    drawing.setAttribute("aria-hidden", "true");
    drawing.append(columns, months);
    picture.append(drawing, element("p", STRINGS.channelChartNote, "channel-note"));
    return picture;
  }

  // What the bars' shades mean, built from the pairs themselves.
  function chartInfo() {
    const mainTrack = pairs[pairs.length - 1].track;
    const others = [...new Set(pairs.map((pair) => pair.track).filter((track) => track !== mainTrack))];
    const lines = [element("p", STRINGS.channelBarsScale)];
    if (others.length) lines.push(element("p", STRINGS.channelTracks(mainTrack, others.join(", "))));
    if (pairs.some((pair) => gapNote(pair))) lines.push(element("p", STRINGS.channelGapBars));
    return newInfo(STRINGS.infoWhat.bars, ...lines);
  }

  // One pass in the newest-first list: dates and track on the left, km² and courts on the right.
  // A pass with an unequal gap is dimmed, and its note is in the info button beside it.
  function barRow(channel, pair) {
    const area = flaggedArea(channel, pair);
    const button = element("button", undefined, "channel-bar");
    button.type = "button";
    button.dataset.pair = pair.id;
    const left = element("span", undefined, "channel-bar-words");
    left.append(element("span", passTitle(pair, site.time_zone, false), "channel-bar-dates"),
      element("span", STRINGS.channelRowTrack(pair.track), "channel-bar-track-name"));
    const right = element("span", undefined, "channel-bar-numbers");
    right.append(element("span", areaText(area), "channel-bar-value"));
    if (area !== null) right.append(element("span", STRINGS.channelCourts(area), "channel-bar-courts"));
    button.append(left, right);
    button.onclick = () => onPickPair(pair.id);
    const row = element("li", undefined, "channel-bar-row");
    row.append(button);
    const note = gapNote(pair);
    if (note) {
      button.classList.add("channel-bar-dim");
      row.append(newInfo(STRINGS.infoWhat.gap, element("p", note, "channel-bar-note")));
    }
    return row;
  }

  // Where the channel's name and line come from.
  function sourceLine(channel) {
    const line = element("p", undefined, "channel-source");
    const { name_source: nameSource, name_source_url: nameUrl } = channel.properties;
    const name = nameUrl ? element("a", nameSource) : document.createTextNode(nameSource);
    if (nameUrl) name.href = nameUrl;
    const osm = element("a", STRINGS.channelOsm);
    osm.href = "https://www.openstreetmap.org/copyright";
    line.append(`${STRINGS.channelSourceName} `, name, `. ${STRINGS.channelSourceLine} `, osm, ` ${STRINGS.channelOsmLicense}`);
    return line;
  }

  function townNames(channel) {
    return channel.properties.town_ids.map((id) => {
      const town = towns.features.find((item) => item.properties.id === id);
      return town ? town.properties.name : id;
    });
  }

  // SCR-14: a channel's page, with its strip on the map (FR-096).
  function showChannel(channel) {
    onChannelChange(channel);
    setPage(true);
    openChannel = channel;
    elements.title.textContent = channel.properties.name;
    showStatus("", false);
    const largest = largestArea();
    const chartTitle = element("div", undefined, "channel-section-title");
    chartTitle.append(element("h3", STRINGS.everyPassSince(startMonth(pairs[0], site.time_zone))), chartInfo());
    const rows = element("ol", undefined, "channel-bars");
    rows.append(...[...pairs].reverse().map((pair) => barRow(channel, pair)));
    elements.headMore.replaceChildren(element("p", townNames(channel).join(" · "), "channel-towns"), buildPassCard());
    elements.body.replaceChildren(
      chartTitle,
      passChart(channel, largest),
      element("h3", STRINGS.newestFirst, "channel-section-title"),
      rows,
    );
    if (channel.properties.not_checked_geometry) {
      const card = element("div", undefined, "card channel-not-checked");
      const mark = element("span", undefined, "not-checked-mark");
      mark.setAttribute("aria-hidden", "true");
      card.append(mark, element("p", STRINGS.channelNotCheckedNote(site.detection_reach_km)));
      elements.body.append(card);
    }
    elements.body.append(sourceLine(channel));
    showPassCard();
    elements.host.scrollTop = 0;
    drawStrip(channel);
    elements.title.focus();
    markSelectedBar();
  }

  // A channel's page takes the column (or the sheet) over from the other cards, with a way back.
  function setPage(open) {
    elements.host.classList.toggle("channel-page-open", open);
    elements.back.hidden = !open;
    elements.info.hidden = open;
  }

  function showListTitle() {
    setPage(false);
    openChannel = null;
    passCard = null;
    elements.headMore.replaceChildren();
    elements.title.textContent = STRINGS.channelsTitle;
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
    const largest = largestArea();
    list.append(...sorted.map((channel) => listRow(channel, latest, largest)));
    // Which pass the list is for, and how its areas are counted, are in the title's info button.
    const lead = STRINGS.channelsLatest(pairDates(latest, site.time_zone), latest.track);
    const note = gapNote(latest);
    elements.lead.textContent = note ? STRINGS.optionWithGap(lead, note) : lead;
    elements.how.textContent = STRINGS.channelsHow(site.channel_strip_half_width_m, site.detection_reach_km);
    // An unequal gap matters enough to stay on screen.
    elements.body.replaceChildren(...(note ? [element("p", note, "soft-note")] : []), list);
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
    onResize();
  }

  // For when the site opens: the list is always there, and the keyboard focus stays put (FR-094).
  function showAtStart() {
    setOpen(true);
    if (rows) showList();
    else load();
  }

  // For when the site changes: the list and any channel's strip go away.
  function close() {
    onChannelChange(null);
    openChannel = null;
    passCard = null;
    elements.headMore.replaceChildren();
    request += 1;
    removeStrip();
    setPage(false);
    setOpen(false);
  }

  elements.back.onclick = () => {
    showList();
    elements.title.focus();
  };
  elements.retry.onclick = load;

  // The map's pair changed, for example after tapping a bar.
  function pairChanged(pair) {
    selectedPairId = pair.id;
    showPassCard();
    markSelectedBar();
    if (elements.status.textContent === STRINGS.passLoadError) showStatus("", false, true);
  }

  // On a phone the pass controls are hidden behind this panel, so it has to say so itself.
  function pairFailed() {
    showStatus(STRINGS.passLoadError, false, true);
  }

  return { showAtStart, close, pairChanged, pairFailed };
}

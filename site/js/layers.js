// Tasks T-025 and T-028: the new-material layer, its legend and the area summary,
// and the channel layer with its names and sources.

import { RADAR_PANE } from "./map.js";
import { createMarks } from "./marks.js";
import { STRINGS, textFor } from "./strings.js";
import { localDate } from "./timeline.js";

// A dark edge keeps a channel line readable on bright imagery, and a dash marks what isn't checked.
const CHANNEL_EDGE_STYLE = { color: "#0f172a", weight: 5, opacity: 0.55, interactive: false, className: "line-channel-edge" };
const CHANNEL_STYLE = { color: "#22d3ee", weight: 3, opacity: 1, interactive: false, className: "line-channel" };
const NOT_CHECKED_STYLE = { color: "#ffffff", weight: 2.5, opacity: 1, dashArray: "6 7", interactive: false, className: "line-not-checked" };
// An invisible, wider line makes a channel easier to tap. Tapping it must not also tap the map.
const CHANNEL_TAP_STYLE = { opacity: 0, weight: 18, bubblingMouseEvents: false };

function layerBounds(layer) {
  return [[layer.bounds_south, layer.bounds_west], [layer.bounds_north, layer.bounds_east]];
}

// Wait for the image to load, so a failed image counts as a failed pair
// and the previous pair stays on screen.
function loadImage(url) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error(`Image failed to load: ${url}`));
    image.src = url;
  });
}

// One legend row: a swatch and its text. On screen the text is one word, and in the popover it's in full.
function legendRow(item, text) {
  const row = document.createElement("li");
  const swatch = document.createElement("span");
  swatch.className = "swatch";
  swatch.style.backgroundColor = item.color;
  const words = document.createElement("span");
  words.textContent = text;
  row.append(swatch, words);
  return row;
}

function paragraph(text) {
  const item = document.createElement("p");
  item.textContent = text;
  return item;
}

function showLegend(elements, layer, pair, site) {
  const text = textFor(site);
  const km2 = pair.new_material_area_km2;
  elements.title.textContent = layer.title;
  elements.rows.replaceChildren(...layer.legend.map((item) => legendRow(item, STRINGS.legendShort[item.confidence])));
  elements.full.replaceChildren(...layer.legend.map((item) => legendRow(item, STRINGS.classWithConfidence(item.label, item.confidence))));
  elements.noColor.textContent = text.helpNoColor;
  elements.area.textContent = text.areaHeadline(km2);
  const more = [paragraph(text.areaUnits), paragraph(STRINGS.totalArea(km2))];
  // Basketball courts only where channel areas show them too.
  if (text.areaCourts) more.push(paragraph(text.areaCourts(km2)), paragraph(STRINGS.channelCourtSize));
  elements.areaMore.replaceChildren(...more);
}

// The label on the map saying which radar products made this pair, and from which dates (FR-084).
// Without coherence data, only the brightness product (GCOV) went into the map.
function productText(pair, site) {
  const products = pair.coherence_used ? STRINGS.productsWithCoherence : STRINGS.productsWithoutCoherence;
  return STRINGS.productLabel(products, localDate(pair.before_acquired_start, site.time_zone),
    localDate(pair.after_acquired_start, site.time_zone));
}

function createProductLabel(map) {
  const label = L.DomUtil.create("p", "product-label");
  const Label = L.Control.extend({ onAdd: () => label });
  new Label({ position: "bottomright" }).addTo(map);
  return label;
}

function summaryText(pair, site) {
  const timeZone = site.time_zone;
  if (pair.new_material_area_km2 !== 0) return "";
  const before = localDate(pair.before_acquired_start, timeZone);
  const after = localDate(pair.after_acquired_start, timeZone);
  return textFor(site).nothingDetected(before, after);
}

// Set up the layer's toggle. Returns the function that shows a pair on the map.
export function createNewMaterialLayer(map, elements, site) {
  let overlay = null;
  const productLabel = createProductLabel(map);

  elements.toggle.onchange = () => {
    if (!overlay) return;
    if (elements.toggle.checked) overlay.addTo(map);
    else overlay.remove();
  };

  return async function showPair(pair, isCurrent) {
    const layer = pair.layers.find((item) => item.kind === "new_material");
    const url = `${pair.folder}/${layer.image_path}`;
    const image = await loadImage(url);
    if (!isCurrent()) return;
    if (overlay) overlay.remove();
    const bounds = layerBounds(layer);
    overlay = L.layerGroup([
      L.imageOverlay(url, bounds, { pane: RADAR_PANE, alt: layer.title, className: "radar-image" }),
      createMarks(image, bounds, RADAR_PANE),
    ]);
    if (elements.toggle.checked) overlay.addTo(map);
    showLegend(elements, layer, pair, site);
    productLabel.textContent = productText(pair, site);
    elements.summary.textContent = summaryText(pair, site);
  };
}

// One channel's lines: solid where the map checks it, and dashed past the reach (FR-071).
export function channelLines(channel) {
  const { checked_geometry: checked, not_checked_geometry: notChecked } = channel.properties;
  const lines = [L.geoJSON(checked, { style: CHANNEL_EDGE_STYLE }), L.geoJSON(checked, { style: CHANNEL_STYLE })];
  if (notChecked) {
    lines.push(L.geoJSON(notChecked, { style: CHANNEL_EDGE_STYLE }), L.geoJSON(notChecked, { style: NOT_CHECKED_STYLE }));
  }
  return L.layerGroup(lines);
}

function channelLabel(channel) {
  const { label_lat: lat, label_lon: lon, name } = channel.properties;
  const label = document.createElement("span");
  label.textContent = name; // text from a data file is never read as HTML
  return L.tooltip({ permanent: true, direction: "center", className: "channel-label", interactive: false })
    .setLatLng([lat, lon])
    .setContent(label);
}

// Show one of the channel legend's two states, or neither for a site with no channel data.
export function showChannelLegend(elements, state) {
  elements.legend.hidden = state === "none";
  elements.layer.hidden = state !== "layer";
  elements.unavailable.hidden = state !== "unavailable";
}

// Draw a site's channels. `onTap(channel, latlng)` runs when the visitor taps a line.
export function createChannelLayer(map, elements, channels, onTap) {
  const group = L.layerGroup();
  for (const channel of channels.features) {
    group.addLayer(channelLines(channel));
    group.addLayer(channelLabel(channel));
    const tapLine = L.geoJSON(channel.geometry, { style: CHANNEL_TAP_STYLE });
    tapLine.on("click", (event) => onTap(channel, event.latlng));
    group.addLayer(tapLine);
  }
  showChannelLegend(elements, "layer");
  elements.note.hidden = !channels.features.some((channel) => channel.properties.not_checked_geometry);
  // OpenStreetMap's license asks for this credit wherever its data is shown.
  map.attributionControl.addAttribution(STRINGS.channelCredit);
  elements.toggle.onchange = () => {
    if (elements.toggle.checked) group.addTo(map);
    else group.remove();
  };
  elements.toggle.checked = true;
  group.addTo(map);
}

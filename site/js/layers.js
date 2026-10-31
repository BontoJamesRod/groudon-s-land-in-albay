// Tasks T-025 and T-028: the new-material layer, its legend and the area summary,
// and the channel layer with its names and sources.

import { RADAR_PANE } from "./map.js";
import { STRINGS, textFor } from "./strings.js";
import { localDate } from "./timeline.js";

// A dark edge keeps a channel line readable on bright imagery, and a dash marks what isn't checked.
const CHANNEL_EDGE_STYLE = { color: "#0f172a", weight: 5, opacity: 0.55, interactive: false };
const CHANNEL_STYLE = { color: "#22d3ee", weight: 3, opacity: 1, interactive: false };
const NOT_CHECKED_STYLE = { color: "#ffffff", weight: 2.5, opacity: 1, dashArray: "6 7", interactive: false };
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
    image.onload = () => resolve();
    image.onerror = () => reject(new Error(`Image failed to load: ${url}`));
    image.src = url;
  });
}

function legendRow(item) {
  const row = document.createElement("li");
  const swatch = document.createElement("span");
  swatch.className = "swatch";
  swatch.style.backgroundColor = item.color;
  const text = document.createElement("span");
  text.textContent = STRINGS.classWithConfidence(item.label, item.confidence);
  row.append(swatch, text);
  return row;
}

function showLegend(elements, layer, pair) {
  elements.title.textContent = layer.title;
  elements.rows.replaceChildren(...layer.legend.map(legendRow));
  elements.area.textContent = `${STRINGS.layerUnits(layer.units)}. ${STRINGS.totalArea(pair.new_material_area_km2)}`;
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

  elements.toggle.onchange = () => {
    if (!overlay) return;
    if (elements.toggle.checked) overlay.addTo(map);
    else overlay.remove();
  };

  return async function showPair(pair, isCurrent) {
    const layer = pair.layers.find((item) => item.kind === "new_material");
    const url = `${pair.folder}/${layer.image_path}`;
    await loadImage(url);
    if (!isCurrent()) return;
    if (overlay) overlay.remove();
    overlay = L.imageOverlay(url, layerBounds(layer), { pane: RADAR_PANE, alt: layer.title, className: "radar-image" });
    if (elements.toggle.checked) overlay.addTo(map);
    showLegend(elements, layer, pair);
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

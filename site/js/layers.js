// Task T-025: the new-material layer, its legend and the area summary.

import { RADAR_PANE } from "./map.js";
import { localDate } from "./timeline.js";

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
  text.textContent = `${item.label}. Confidence: ${item.confidence}`;
  row.append(swatch, text);
  return row;
}

function showLegend(elements, layer, pair) {
  elements.title.textContent = layer.title;
  elements.rows.replaceChildren(...layer.legend.map(legendRow));
  elements.area.textContent = `Total detected area: ${pair.new_material_area_km2.toFixed(2)} km²`;
}

function summaryText(pair, timeZone) {
  if (pair.new_material_area_km2 !== 0) return "";
  const before = localDate(pair.before_acquired_start, timeZone);
  const after = localDate(pair.after_acquired_start, timeZone);
  return `No new material detected between ${before} and ${after}`;
}

// Set up the layer's toggle. Returns the function that shows a pair on the map.
export function createNewMaterialLayer(map, elements, site) {
  let overlay = null;

  elements.toggle.addEventListener("change", () => {
    if (!overlay) return;
    if (elements.toggle.checked) overlay.addTo(map);
    else overlay.remove();
  });

  return async function showPair(pair) {
    const layer = pair.layers.find((item) => item.kind === "new_material");
    const url = `${pair.folder}/${layer.image_path}`;
    await loadImage(url);
    if (overlay) overlay.remove();
    overlay = L.imageOverlay(url, layerBounds(layer), { pane: RADAR_PANE, alt: layer.title, className: "radar-image" });
    if (elements.toggle.checked) overlay.addTo(map);
    showLegend(elements, layer, pair);
    elements.summary.textContent = summaryText(pair, site.time_zone);
  };
}

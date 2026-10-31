// Task T-023: the map, its zoom limits, the background imagery with its fallback,
// and the layers the app draws from its own data: town borders and names, the
// coastline and the danger-zone ring. These stay visible if the imagery fails (FR-005).

import { STRINGS } from "./strings.js";

const TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
const TILE_FAILURES_FOR_NOTICE = 4;
const TOWN_STYLE = { color: "#ffffff", weight: 1, opacity: 0.8, fill: false };
const COAST_STYLE = { color: "#7dd3fc", weight: 2, fill: false };
const RING_STYLE = { color: "#fb923c", weight: 2, fill: false, dashArray: "6 6" };
const REACH_STYLE = { color: "#ffffff", weight: 2, opacity: 0.9, fill: false, dashArray: "2 6" };

// Radar images go in their own layer, under the borders so that towns stay readable.
export const RADAR_PANE = "radar";
export const COMPARE_PANE = "compare";
export const COMPARE_LINE_PANE = "compareLine";

function addBackground(map, notice) {
  const tiles = L.tileLayer(TILE_URL, { attribution: STRINGS.tileAttribution, maxZoom: map.getMaxZoom() });
  let failuresInARow = 0;
  tiles.on("tileload", () => {
    failuresInARow = 0;
    notice.hidden = true;
  });
  // One failed tile among good ones isn't an outage, so the message waits for a run of failures.
  tiles.on("tileerror", () => {
    failuresInARow += 1;
    if (failuresInARow >= TILE_FAILURES_FOR_NOTICE) notice.hidden = false;
  });
  tiles.addTo(map);
}

function addTowns(map, towns) {
  L.geoJSON(towns, { style: TOWN_STYLE, interactive: false }).addTo(map);
  return towns.features.map((town) => {
    const { label_lat: lat, label_lon: lon, name } = town.properties;
    return L.tooltip({ permanent: true, direction: "center", className: "town-label", interactive: false })
      .setLatLng([lat, lon])
      .setContent(escapeText(name))
      .addTo(map);
  });
}

// Leaflet tooltips take HTML, so a name from a data file is turned into plain text first.
function escapeText(text) {
  const holder = document.createElement("span");
  holder.textContent = text;
  return holder.innerHTML;
}

function addDangerZone(map, site) {
  if (site.danger_zone_radius_km == null || site.summit_lat == null) return null;
  const center = [site.summit_lat, site.summit_lon];
  if (site.detection_reach_km) {
    L.circle(center, { ...REACH_STYLE, radius: site.detection_reach_km * 1000, interactive: false }).addTo(map);
  }
  const ring = L.circle(center, { ...RING_STYLE, radius: site.danger_zone_radius_km * 1000, interactive: false }).addTo(map);
  // The label sits just outside the ring's southern edge. At Mayon the northern edge
  // puts it on top of Tabaco City.
  return L.tooltip({ permanent: true, direction: "bottom", className: "zone-label", interactive: false })
    .setLatLng([ring.getBounds().getSouth(), site.summit_lon])
    .setContent(escapeText(site.danger_zone_label))
    .addTo(map);
}

// Zoomed out, labels crowd together. The danger zone matters most, so a town's name
// makes way for it until the visitor zooms back in.
function keepZoneLabelClear(map, zoneLabel, townLabels) {
  function update() {
    const zone = zoneLabel.getElement().getBoundingClientRect();
    for (const town of townLabels) {
      const box = town.getElement().getBoundingClientRect();
      const touches = box.left < zone.right && box.right > zone.left && box.top < zone.bottom && box.bottom > zone.top;
      town.getElement().style.visibility = touches ? "hidden" : "";
    }
  }
  map.on("zoomend moveend resize", update);
  update();
}

// Build the map for a site. `notice` is the "Background map unavailable" element.
export function createMap(site, siteData, notice) {
  const map = L.map("map", { minZoom: site.min_zoom, maxZoom: site.max_zoom })
    .setView([site.center_lat, site.center_lon], site.default_zoom);
  map.attributionControl.addAttribution(STRINGS.boundaryAttribution);
  map.createPane(RADAR_PANE).style.zIndex = 350;
  map.createPane(COMPARE_PANE).style.zIndex = 340;
  // Above town borders and below the labels (Leaflet's label layer is 650).
  map.createPane(COMPARE_LINE_PANE).style.zIndex = 630;
  addBackground(map, notice);
  L.geoJSON(siteData.land, { style: COAST_STYLE, interactive: false }).addTo(map);
  const townLabels = addTowns(map, siteData.towns);
  const zoneLabel = addDangerZone(map, site);
  if (zoneLabel) keepZoneLabelClear(map, zoneLabel, townLabels);
  return map;
}

// Task T-023: the map, its zoom limits, the background imagery with its fallback,
// and the layers the app draws from its own data: town borders and names, the
// coastline and the danger-zone ring. These stay visible if the imagery fails (FR-005).

import { STRINGS } from "./strings.js";

const TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
const TOWN_STYLE = { color: "#ffffff", weight: 1, opacity: 0.8, fill: false };
const COAST_STYLE = { color: "#7dd3fc", weight: 2, fill: false };
const RING_STYLE = { color: "#fb923c", weight: 2, fill: false, dashArray: "6 6" };

// Radar images go in their own layer, under the borders so that towns stay readable.
export const RADAR_PANE = "radar";

function addBackground(map, notice) {
  const tiles = L.tileLayer(TILE_URL, { attribution: STRINGS.tileAttribution, maxZoom: map.getMaxZoom() });
  let anyTileLoaded = false;
  tiles.on("tileload", () => {
    anyTileLoaded = true;
    notice.hidden = true;
  });
  // One failed tile among good ones isn't an outage, so the message waits for none having loaded.
  tiles.on("tileerror", () => {
    if (!anyTileLoaded) notice.hidden = false;
  });
  tiles.addTo(map);
}

function addTowns(map, towns) {
  L.geoJSON(towns, { style: TOWN_STYLE, interactive: false }).addTo(map);
  for (const town of towns.features) {
    const { label_lat: lat, label_lon: lon, name } = town.properties;
    L.tooltip({ permanent: true, direction: "center", className: "town-label", interactive: false })
      .setLatLng([lat, lon])
      .setContent(escapeText(name))
      .addTo(map);
  }
}

// Leaflet tooltips take HTML, so a name from a data file is turned into plain text first.
function escapeText(text) {
  const holder = document.createElement("span");
  holder.textContent = text;
  return holder.innerHTML;
}

function addDangerZone(map, site) {
  if (site.danger_zone_radius_km === null || site.summit_lat === null) return;
  const center = [site.summit_lat, site.summit_lon];
  const ring = L.circle(center, { ...RING_STYLE, radius: site.danger_zone_radius_km * 1000, interactive: false }).addTo(map);
  // The label sits on the ring's northern edge, where it doesn't cover the summit.
  L.tooltip({ permanent: true, direction: "top", className: "zone-label", interactive: false })
    .setLatLng([ring.getBounds().getNorth(), site.summit_lon])
    .setContent(escapeText(site.danger_zone_label))
    .addTo(map);
}

// Build the map for a site. `notice` is the "Background map unavailable" element.
export function createMap(site, siteData, notice) {
  const map = L.map("map", { minZoom: site.min_zoom, maxZoom: site.max_zoom })
    .setView([site.center_lat, site.center_lon], site.default_zoom);
  map.attributionControl.addAttribution(STRINGS.boundaryAttribution);
  map.createPane(RADAR_PANE).style.zIndex = 350;
  addBackground(map, notice);
  L.geoJSON(siteData.land, { style: COAST_STYLE, interactive: false }).addTo(map);
  addTowns(map, siteData.towns);
  addDangerZone(map, site);
  return map;
}

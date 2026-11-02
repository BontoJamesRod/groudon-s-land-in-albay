// Task T-023: the map, its zoom limits, the background imagery with its fallback,
// and the layers the app draws from its own data: town borders and names, the
// coastline and the danger-zone ring. These stay visible if the imagery fails (FR-005).

import { STRINGS } from "./strings.js";

const SATELLITE_URL = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/g/{z}/{y}/{x}.jpg";
const SATELLITE_NATIVE_ZOOM = 14; // past this, the imagery is enlarged
const SATELLITE_PREVIEW_ZOOM = 10; // a few tiles, enlarged, cover the view while the sharp ones come
const SHARP_TILES_WAIT_MS = 10000; // the sharp tiles start then, even if the preview isn't finished
const BASEMAP_KEY = "mayon-radar-basemap";
const TILE_FAILURES_FOR_NOTICE = 4;
const PHONE_LAYOUT = "(max-width: 700px)"; // the same width as in app.css
const PHONE_LABEL_DROP_PX = 22; // far enough inside the ring to clear the town names beside its top edge
const RING_ROOM_PX = 26; // the room the ring needs above the map credits to show clearly
// These colours are for Satellite. On the light relief, app.css recolours each line by its class.
const TOWN_STYLE = { color: "#ffffff", weight: 1, opacity: 0.8, fill: false, className: "line-town" };
const COAST_STYLE = { color: "#7dd3fc", weight: 2, fill: false, className: "line-coast" };
const RING_STYLE = { color: "#fb923c", weight: 2, fill: false, dashArray: "6 6", className: "line-ring" };
const REACH_STYLE = { color: "#ffffff", weight: 2, opacity: 0.9, fill: false, dashArray: "2 6", className: "line-reach" };

// Radar images go in their own layer, under the borders so that towns stay readable.
export const RADAR_PANE = "radar";
export const COMPARE_PANE = "compare";
export const COMPARE_LINE_PANE = "compareLine";
export const STRIP_PANE = "channelStrip";

function reliefBounds(site) {
  return [[site.relief_bounds_south, site.relief_bounds_west], [site.relief_bounds_north, site.relief_bounds_east]];
}

// The relief stops at its bounds, so the map does too. A very wide screen can see more than the
// whole relief at the lowest zoom, so there the lowest zoom rises (FR-076).
function keepInsideRelief(map, site) {
  const bounds = reliefBounds(site);
  map.options.maxBoundsViscosity = 1;
  map.setMaxBounds(bounds);
  function update() {
    map.options.minZoom = site.min_zoom; // otherwise the answer below can never come back down
    map.setMinZoom(map.getBoundsZoom(bounds, true));
  }
  map.on("resize", update);
  update();
}

// The visitor's choice, kept in this browser. The storage can be blocked, and then Relief opens.
function savedBasemap() {
  try {
    return localStorage.getItem(BASEMAP_KEY) === "satellite" ? "satellite" : "relief";
  } catch {
    return "relief";
  }
}

function saveBasemap(choice) {
  try {
    localStorage.setItem(BASEMAP_KEY, choice);
  } catch {
    // The choice still applies until the page closes.
  }
}

function reliefTiles(map, site) {
  return L.tileLayer(`data/sites/${site.id}/relief/{z}/{x}/{y}.webp`, {
    attribution: STRINGS.reliefCredit,
    maxZoom: map.getMaxZoom(),
    maxNativeZoom: site.relief_max_native_zoom,
    bounds: reliefBounds(site),
  });
}

function satelliteTiles(map) {
  return L.tileLayer(SATELLITE_URL, {
    maxZoom: map.getMaxZoom(),
    maxNativeZoom: SATELLITE_NATIVE_ZOOM,
    zIndex: 3, // above the preview and the relief
  });
}

// EOX's tiles can take over a minute for a whole screen, so a few low-detail ones go first.
function satellitePreview(map) {
  return L.tileLayer(SATELLITE_URL, {
    attribution: STRINGS.satelliteCredit,
    maxZoom: map.getMaxZoom(),
    maxNativeZoom: SATELLITE_PREVIEW_ZOOM,
    zIndex: 2,
  });
}

// Say how many tiles are still on their way, so that slow imagery doesn't look like nothing happened.
// It counts what's on the map right now, because moving the map drops tiles that never finish.
function showLoadingCount(layers, notice) {
  function update() {
    if (notice.textContent === STRINGS.satelliteUnavailable) return;
    const waiting = layers.reduce((sum, layer) => sum
      + (layer.getContainer() ? layer.getContainer().querySelectorAll("img:not(.leaflet-tile-loaded)").length : 0), 0);
    notice.textContent = STRINGS.satelliteLoading(waiting);
    notice.hidden = waiting === 0;
  }
  // One frame later, because Leaflet adds a batch of new tiles to the page just after announcing them.
  for (const layer of layers) layer.on("tileloadstart tileload tileerror tileabort tileunload load", () => L.Util.requestAnimFrame(update));
}

// Show imagery, low detail first. A browser only fetches 6 tiles at a time from one server, so the
// sharp tiles wait their turn. Otherwise they'd hold up the few tiles that cover the whole view.
function addSatellite(map, preview, sharp) {
  let timer = null;
  function addSharp() {
    clearTimeout(timer);
    preview.off("load", addSharp);
    sharp.addTo(map);
  }
  preview.on("load", addSharp);
  timer = setTimeout(addSharp, SHARP_TILES_WAIT_MS);
  preview.addTo(map);
  return () => {
    clearTimeout(timer);
    preview.off("load", addSharp);
    preview.remove();
    sharp.remove();
  };
}

// One failed tile among good ones isn't an outage, so the message waits for a run of failures.
function watchTiles(tiles, notice, message) {
  let failuresInARow = 0;
  tiles.on("tileload", () => {
    failuresInARow = 0;
    if (notice.textContent === message) notice.hidden = true;
  });
  tiles.on("tileerror", () => {
    failuresInARow += 1;
    if (failuresInARow >= TILE_FAILURES_FOR_NOTICE) {
      notice.textContent = message;
      notice.hidden = false;
    }
  });
}

// The Relief and Satellite buttons (FR-081). `choose` runs with the visitor's choice.
function addSwitcher(map, choose) {
  const buttons = {};
  const Switcher = L.Control.extend({
    onAdd() {
      const group = L.DomUtil.create("div", "basemap-switcher");
      group.setAttribute("role", "group");
      group.setAttribute("aria-label", STRINGS.basemapLabel);
      for (const [choice, text] of [["relief", STRINGS.basemapRelief], ["satellite", STRINGS.basemapSatellite]]) {
        const button = L.DomUtil.create("button", "basemap-button", group);
        button.type = "button";
        button.textContent = text;
        button.onclick = () => choose(choice);
        buttons[choice] = button;
      }
      // A tap here must not also tap the map.
      L.DomEvent.disableClickPropagation(group);
      return group;
    },
  });
  new Switcher({ position: "topleft" }).addTo(map);
  return buttons;
}

// The relief always stays on, so that it shows while imagery is slow to load or if it fails.
function addBackground(map, site, notice) {
  const sharp = satelliteTiles(map);
  const preview = satellitePreview(map);
  watchTiles(sharp, notice, STRINGS.satelliteUnavailable);
  showLoadingCount([preview, sharp], notice);
  if (site.relief_max_native_zoom == null) {
    document.body.classList.remove("relief-map");
    addSatellite(map, preview, sharp);
    return;
  }
  const relief = reliefTiles(map, site);
  watchTiles(relief, notice, STRINGS.backgroundUnavailable);
  relief.addTo(map);
  keepInsideRelief(map, site);
  let buttons = {};
  let removeSatellite = null;
  function show(choice) {
    document.body.classList.toggle("relief-map", choice === "relief");
    if (removeSatellite) removeSatellite();
    removeSatellite = null;
    if (choice === "satellite") {
      removeSatellite = addSatellite(map, preview, sharp);
    } else {
      if (notice.textContent !== STRINGS.backgroundUnavailable) notice.hidden = true;
    }
    for (const [name, button] of Object.entries(buttons)) button.setAttribute("aria-pressed", String(name === choice));
  }
  buttons = addSwitcher(map, (choice) => {
    saveBasemap(choice);
    show(choice);
  });
  show(savedBasemap());
}

function addTowns(map, towns, site) {
  L.geoJSON(outlinesInsideSite(towns, site), { style: TOWN_STYLE, interactive: false }).addTo(map);
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
  // The label sits just outside the ring's southern edge. At Mayon the northern edge puts it on
  // top of Tabaco City. A phone has no room for it there beside the towns and the map credits, so
  // it hangs inside the northern edge on two lines, and the town names keep their places.
  const onPhone = window.matchMedia(PHONE_LAYOUT).matches;
  return L.tooltip({ permanent: true, direction: "bottom", offset: [0, onPhone ? PHONE_LABEL_DROP_PX : 0], className: onPhone ? "zone-label zone-label-phone" : "zone-label", interactive: false })
    .setLatLng([onPhone ? ring.getBounds().getNorth() : ring.getBounds().getSouth(), site.summit_lon])
    .setContent(escapeText(site.danger_zone_label))
    .addTo(map);
}

function boxesTouch(a, b) {
  return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
}

// Zoomed out, labels crowd together. The danger zone matters most, so a town's name
// makes way for it until the visitor zooms back in.
function keepZoneLabelClear(map, zoneLabel, townLabels) {
  function update() {
    const zone = zoneLabel.getElement().getBoundingClientRect();
    for (const town of townLabels) {
      const touches = boxesTouch(town.getElement().getBoundingClientRect(), zone);
      town.getElement().style.visibility = touches ? "hidden" : "";
    }
  }
  map.on("zoomend moveend resize", update);
  update();
}

// On a phone a town's name matters more than a channel's, and the Channels list still names them all.
function keepTownLabelsClear(map, townLabels) {
  function update() {
    const towns = townLabels.map((town) => town.getElement())
      .filter((town) => town.style.visibility !== "hidden")
      .map((town) => town.getBoundingClientRect());
    for (const label of map.getContainer().querySelectorAll(".channel-label")) {
      const touches = towns.some((town) => boxesTouch(town, label.getBoundingClientRect()));
      label.style.visibility = touches ? "hidden" : "";
    }
  }
  map.on("zoomend moveend resize layeradd", update);
}

// A file's polygon outlines as lines, leaving out any stretch along the site's edge. Land and
// towns are clipped to the site, so those stretches are where the data stops, not a real line.
export function outlinesInsideSite(shapes, site) {
  const near = (a, b) => Math.abs(a - b) < 0.00002;
  const alongEdge = ([lon1, lat1], [lon2, lat2]) =>
    (near(lon1, site.bounds_west) && near(lon2, site.bounds_west))
    || (near(lon1, site.bounds_east) && near(lon2, site.bounds_east))
    || (near(lat1, site.bounds_south) && near(lat2, site.bounds_south))
    || (near(lat1, site.bounds_north) && near(lat2, site.bounds_north));
  const lines = [];
  for (const feature of shapes.features) {
    const { type, coordinates } = feature.geometry;
    for (const polygon of type === "Polygon" ? [coordinates] : coordinates) {
      for (const ring of polygon) {
        let line = [ring[0]];
        for (let i = 1; i < ring.length; i += 1) {
          if (alongEdge(ring[i - 1], ring[i])) {
            if (line.length > 1) lines.push(line);
            line = [];
          }
          line.push(ring[i]);
        }
        if (line.length > 1) lines.push(line);
      }
    }
  }
  return { type: "MultiLineString", coordinates: lines };
}

// The credit for this site's borders, as a link when the source asks for one.
function boundaryCredit(site) {
  const text = escapeText(site.boundary_credit);
  return site.boundary_credit_url ? `<a href="${site.boundary_credit_url}">${text}</a>` : text;
}

// Open at the site's own view. On a short phone screen the danger-zone ring runs behind the map
// credits, so the map opens one zoom step further out (FR-001).
export function showStartView(map, site) {
  const center = [site.center_lat, site.center_lon];
  map.setView(center, site.default_zoom, { animate: false });
  if (site.danger_zone_radius_km == null || !window.matchMedia(PHONE_LAYOUT).matches) return;
  const ring = L.latLng(site.summit_lat, site.summit_lon).toBounds(site.danger_zone_radius_km * 2000);
  const ringBottom = map.latLngToContainerPoint([ring.getSouth(), site.summit_lon]).y;
  const creditsTop = map.getSize().y - map.attributionControl.getContainer().offsetHeight;
  if (ringBottom + RING_ROOM_PX > creditsTop) {
    map.setView(center, site.default_zoom - 1, { animate: false });
  }
}

// Build the map for a site. `notice` is the "Background map unavailable" element.
export function createMap(site, siteData, notice) {
  const map = L.map("map", { minZoom: site.min_zoom, maxZoom: site.max_zoom })
    .setView([site.center_lat, site.center_lon], site.default_zoom);
  if (site.boundary_credit) map.attributionControl.addAttribution(boundaryCredit(site));
  map.createPane(RADAR_PANE).style.zIndex = 350;
  map.createPane(COMPARE_PANE).style.zIndex = 340;
  map.createPane(STRIP_PANE).style.zIndex = 345;
  // Above town borders and below the labels (Leaflet's label layer is 650).
  map.createPane(COMPARE_LINE_PANE).style.zIndex = 630;
  addBackground(map, site, notice);
  L.geoJSON(outlinesInsideSite(siteData.land, site), { style: COAST_STYLE, interactive: false }).addTo(map);
  const townLabels = addTowns(map, siteData.towns, site);
  const zoneLabel = addDangerZone(map, site);
  if (zoneLabel) keepZoneLabelClear(map, zoneLabel, townLabels);
  if (window.matchMedia(PHONE_LAYOUT).matches) keepTownLabelsClear(map, townLabels);
  return map;
}

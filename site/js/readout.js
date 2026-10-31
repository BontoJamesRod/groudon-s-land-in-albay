// Task T-026: the readout card. It answers "what did the radar find at this spot?"
// from the pair's value grid, entirely in the browser: nothing is sent anywhere.

import { loadGrid } from "./data.js";
import { STRINGS, textFor } from "./strings.js";
import { localDate } from "./timeline.js";

const EARTH_RADIUS_KM = 6371;
const NONE = 0;
const LOW = 1;
const HIGH = 2;

// Find the grid cell under a point. Row 0 is the northern edge, and each row runs
// west to east (docs/06, API-010). Returns the cell's value, or null if off the grid.
export function gridValue(layer, cells, lat, lon) {
  const column = Math.floor(((lon - layer.bounds_west) / (layer.bounds_east - layer.bounds_west)) * layer.grid_width);
  const row = Math.floor(((layer.bounds_north - lat) / (layer.bounds_north - layer.bounds_south)) * layer.grid_height);
  if (column < 0 || column >= layer.grid_width || row < 0 || row >= layer.grid_height) return null;
  return cells[row * layer.grid_width + column];
}

// Straight-line distance over the Earth's surface (the haversine formula).
export function distanceKm(lat1, lon1, lat2, lon2) {
  const toRadians = (degrees) => (degrees * Math.PI) / 180;
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2
    + Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(a));
}

// Is the point inside one ring? Count how many edges a line going east from it crosses:
// an odd number means inside.
function insideRing(ring, lat, lon) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
    const [lonA, latA] = ring[i];
    const [lonB, latB] = ring[j];
    const crosses = latA > lat !== latB > lat;
    if (crosses && lon < ((lonB - lonA) * (lat - latA)) / (latB - latA) + lonA) inside = !inside;
  }
  return inside;
}

// A polygon's first ring is its outline; any others are holes.
function insidePolygon(rings, lat, lon) {
  return insideRing(rings[0], lat, lon) && !rings.slice(1).some((hole) => insideRing(hole, lat, lon));
}

function insideShape({ type, coordinates }, lat, lon) {
  const polygons = type === "Polygon" ? [coordinates] : coordinates;
  return polygons.some((rings) => insidePolygon(rings, lat, lon));
}

export function findTown(towns, lat, lon) {
  const town = towns.features.find((item) => insideShape(item.geometry, lat, lon));
  return town ? town.properties.name : null;
}

// "In or near" a channel means inside its strip: the same ground its bars count.
export function channelsAt(channels, lat, lon) {
  return channels.features.filter((channel) => insideShape(channel.properties.strip_geometry, lat, lon));
}

// Turn a grid value into the card's result line and whether it is a "no data" answer.
export function resultLines(value, layer, text = STRINGS) {
  const code = value === null ? 255 : value;
  if (layer.no_data_codes && layer.no_data_codes[String(code)] !== undefined) {
    return [STRINGS.noRadarData, STRINGS.noDataReasons[code]];
  }
  if (code === NONE) return [text.noNewMaterial];
  const item = layer.legend.find((entry) => entry.value === code);
  return [STRINGS.classWithConfidence(item.label, item.confidence)];
}

function line(text, className) {
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  if (className) paragraph.className = className;
  return paragraph;
}

// Set up the card. Returns open(lat, lon, name, channel) and setPair(pair). `channels` is null when a
// site has none, or its file failed to load, and then the card has no channel line (03 section 5).
export function createReadout(elements, site, towns, channels) {
  let pair = null;
  let grid = null; // the grid of the selected pair, only downloaded when first needed
  let gridPairId = null;
  let spot = null;
  let request = 0; // a newer tap replaces an older one that is still loading

  function close() {
    spot = null;
    request += 1;
    elements.card.hidden = true;
  }

  // Tapping a channel's line says which channel it is, and the towns it passes through.
  function channelLines(channel) {
    const names = channel.properties.town_ids.map((id) => {
      const town = towns.features.find((item) => item.properties.id === id);
      return town ? town.properties.name : id;
    });
    return [line(channel.properties.name, "readout-place"), line(STRINGS.channelTowns(names.join(", ")))];
  }

  function placeLines(lat, lon, name, channel) {
    const lines = channel ? channelLines(channel) : [];
    lines.push(line(name || findTown(towns, lat, lon) || STRINGS.outsideTowns, channel ? "" : "readout-place"));
    if (site.summit_lat == null || site.summit_lon == null) return lines;
    const km = distanceKm(lat, lon, site.summit_lat, site.summit_lon);
    lines.push(line(STRINGS.distanceToSummit(km)));
    if (site.danger_zone_radius_km != null) {
      const inside = km <= site.danger_zone_radius_km;
      lines.push(line(inside ? STRINGS.insideDangerZone : STRINGS.outsideDangerZone, inside ? "readout-danger" : ""));
    }
    return lines;
  }

  // Beyond the reach, "none" only means this map didn't look, so it must not say nothing was found.
  function resultText(value, layer, lat, lon) {
    const reach = site.detection_reach_km;
    if (value === NONE && reach && distanceKm(lat, lon, site.summit_lat, site.summit_lon) > reach) {
      return [STRINGS.beyondReach(reach)];
    }
    return resultLines(value, layer, textFor(site));
  }

  // Only a flagged spot gets a channel line (03, Flow 3).
  function channelResult(value, lat, lon) {
    if (!channels || (value !== LOW && value !== HIGH)) return [];
    const names = channelsAt(channels, lat, lon).map((channel) => channel.properties.name);
    return [names.length ? STRINGS.inOrNearChannel(names.join(" and ")) : STRINGS.notInChannel];
  }

  function showLines(lines) {
    elements.body.replaceChildren(...lines);
    elements.card.hidden = false;
  }

  async function open(lat, lon, name, channel) {
    spot = { lat, lon, name, channel };
    request += 1;
    const thisRequest = request;
    const place = placeLines(lat, lon, name, channel);
    elements.retry.hidden = true;
    // With no pair on screen there are no radar values, but the place is still useful.
    if (!pair) {
      showLines(place);
      return;
    }
    const shownPair = pair;
    const layer = pair.layers.find((item) => item.kind === "new_material");
    showLines([...place, line(STRINGS.readoutLoading)]);
    let cells = gridPairId === shownPair.id ? grid : null;
    try {
      cells = cells || await loadGrid(shownPair.folder, layer);
    } catch (problem) {
      if (thisRequest !== request) return;
      console.error(problem.message);
      showLines([...place, line(STRINGS.readoutGridError)]);
      elements.retry.hidden = false;
      return;
    }
    // Keep a download only for the pair it belongs to, even if a newer tap came along.
    if (shownPair === pair) {
      grid = cells;
      gridPairId = shownPair.id;
    }
    if (thisRequest !== request) return;
    const value = gridValue(layer, cells, lat, lon);
    const results = [...resultText(value, layer, lat, lon), ...channelResult(value, lat, lon)].map((text) => line(text, "readout-result"));
    const dates = STRINGS.pairDates(localDate(pair.before_acquired_start, site.time_zone),
      localDate(pair.after_acquired_start, site.time_zone));
    showLines([...place, ...results, line(dates)]);
  }

  elements.close.onclick = close;
  elements.retry.onclick = () => spot && open(spot.lat, spot.lon, spot.name, spot.channel);

  // A new pair means new values: forget the old grid and refresh an open card.
  function setPair(newPair) {
    pair = newPair;
    grid = null;
    gridPairId = null;
    if (spot) open(spot.lat, spot.lon, spot.name, spot.channel);
  }

  return { open, setPair, close };
}

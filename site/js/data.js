// Task T-022: fetch the data files and turn every failure into one error object
// with a code from docs/06 section 2, so the screens only deal with those codes.

const SCHEMA_VERSION = "1.0";
const REQUEST_TIMEOUT_MS = 15000; // Not decided in the docs yet (06 Open Question 2).

export class DataError extends Error {
  constructor(code, path, issue) {
    super(`${code}: ${path}: ${issue}`);
    this.code = code; // NOT_FOUND, SERVER_ERROR, NETWORK_ERROR or INVALID_DATA
    this.details = [{ field: "url", issue: `${path} ${issue}` }];
  }
}

// Fetch one file, giving up after the timeout. A failure with no response is a network error.
async function request(path) {
  let response;
  try {
    response = await fetch(path, { signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS) });
  } catch (problem) {
    throw new DataError("NETWORK_ERROR", path, `got no response (${problem.name})`);
  }
  if (response.status === 404) throw new DataError("NOT_FOUND", path, "returned 404");
  if (!response.ok) throw new DataError("SERVER_ERROR", path, `returned ${response.status}`);
  return response;
}

async function readJson(path) {
  const response = await request(path);
  let text;
  try {
    text = await response.text();
  } catch (problem) {
    throw new DataError("NETWORK_ERROR", path, `stopped downloading (${problem.name})`);
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new DataError("INVALID_DATA", path, "can't be parsed as JSON");
  }
}

// Read a JSON file with the { data, meta } envelope and return its data.
export async function loadJson(path) {
  const content = await readJson(path);
  if (!content || content.data === undefined || !content.meta) {
    throw new DataError("INVALID_DATA", path, "has no data and meta envelope");
  }
  if (content.meta.schema_version !== SCHEMA_VERSION) {
    throw new DataError("INVALID_DATA", path, `has unknown schema_version ${content.meta.schema_version}`);
  }
  return content.data;
}

// Read a GeoJSON file and check its members.
export async function loadGeoJson(path) {
  const content = await readJson(path);
  if (!content || content.type !== "FeatureCollection" || !Array.isArray(content.features)) {
    throw new DataError("INVALID_DATA", path, "is not a FeatureCollection");
  }
  if (content.schema_version !== SCHEMA_VERSION) {
    throw new DataError("INVALID_DATA", path, `has unknown schema_version ${content.schema_version}`);
  }
  return content;
}

function requireFields(row, fields, path) {
  for (const field of fields) {
    if (row === null || typeof row !== "object" || row[field] === undefined) {
      throw new DataError("INVALID_DATA", path, `misses required field ${field}`);
    }
  }
}

// API-007: the total must equal high + low.
function checkAreas(pair, path) {
  const sum = pair.high_confidence_area_km2 + pair.low_confidence_area_km2;
  if (Math.abs(sum - pair.new_material_area_km2) > 1e-6) {
    throw new DataError("INVALID_DATA", path, `has a total area that isn't high + low for ${pair.id}`);
  }
}

const SITE_FIELDS = ["id", "name", "time_zone", "center_lat", "center_lon", "default_zoom", "min_zoom", "max_zoom",
  "bounds_west", "bounds_south", "bounds_east", "bounds_north"];
const PAIR_FIELDS = ["id", "status", "track", "frame", "orbit_direction", "before_acquired_start", "after_acquired_start",
  "new_material_area_km2"];
const LAYER_FIELDS = ["kind", "title", "image_path", "legend", "source_granule_ids",
  "bounds_west", "bounds_south", "bounds_east", "bounds_north"];

export async function loadSites() {
  const path = "data/sites.json";
  const sites = await loadJson(path);
  if (!Array.isArray(sites)) throw new DataError("INVALID_DATA", path, "is not a list");
  for (const site of sites) {
    requireFields(site, SITE_FIELDS, path);
    if (site.bounds_west >= site.bounds_east || site.bounds_south >= site.bounds_north) {
      throw new DataError("INVALID_DATA", path, `has reversed bounds for ${site.id}`);
    }
  }
  return sites;
}

// The events file is optional for the screen: without it, the timeline has no markers (03 section 5).
async function loadEvents(folder) {
  try {
    return await loadJson(`${folder}/events.json`);
  } catch (problem) {
    console.warn(problem.message);
    return [];
  }
}

// Load what a site needs before any pair is shown.
export async function loadSiteData(siteId) {
  const folder = `data/sites/${siteId}`;
  const [towns, land, pairs, events] = await Promise.all([
    loadGeoJson(`${folder}/towns.geojson`),
    loadGeoJson(`${folder}/land.geojson`),
    loadJson(`${folder}/pairs.json`),
    loadEvents(folder),
  ]);
  if (!Array.isArray(pairs)) throw new DataError("INVALID_DATA", `${folder}/pairs.json`, "is not a list");
  for (const pair of pairs) {
    requireFields(pair, PAIR_FIELDS, `${folder}/pairs.json`);
    if (pair.status !== "published") {
      throw new DataError("INVALID_DATA", `${folder}/pairs.json`, `lists unpublished pair ${pair.id}`);
    }
    checkAreas(pair, `${folder}/pairs.json`);
  }
  return { towns, land, pairs, events };
}

// Download a layer's value grid. Its size must match the record exactly (docs/06, API-010).
export async function loadGrid(folder, layer) {
  const path = `${folder}/${layer.grid_path}`;
  const response = await request(path);
  let bytes;
  try {
    bytes = await response.arrayBuffer();
  } catch (problem) {
    throw new DataError("NETWORK_ERROR", path, `stopped downloading (${problem.name})`);
  }
  if (bytes.byteLength !== layer.grid_width * layer.grid_height) {
    throw new DataError("INVALID_DATA", path, `has ${bytes.byteLength} bytes, which doesn't match the record`);
  }
  return new Uint8Array(bytes);
}

// Load one pair with its passes and layers. Image paths are relative to the pair's folder.
export async function loadPair(siteId, pairId) {
  const folder = `data/sites/${siteId}/pairs/${pairId}`;
  const path = `${folder}/pair.json`;
  const pair = await loadJson(path);
  requireFields(pair, [...PAIR_FIELDS, "passes", "layers"], path);
  pair.layers.forEach((layer) => requireFields(layer, LAYER_FIELDS, path));
  return { ...pair, folder };
}

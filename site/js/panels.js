// Tasks T-030, T-031 and T-032: the "What am I looking at?" panel, the Data sources
// panel and the site picker. Text from data files is set with textContent, never as HTML.

import { loadJson } from "./data.js";
import { STRINGS } from "./strings.js";
import { localDate } from "./timeline.js";

const VERTEX_URL = "https://search.asf.alaska.edu/#/?dataset=NISAR&searchType=List%20Search&searchList=";

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function list(items) {
  const holder = element("ul");
  holder.append(...items.map((item) => {
    const row = element("li");
    row.append(item instanceof Node ? item : document.createTextNode(item));
    return row;
  }));
  return holder;
}

function externalLink(text, url) {
  const link = element("a", text);
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

function retryButton(onRetry) {
  const button = element("button", STRINGS.retry);
  button.type = "button";
  button.onclick = onRetry;
  return button;
}

// One <dialog> panel. `fill(body)` writes its content each time it opens.
export function createPanel(dialog, fill) {
  dialog.querySelector("[data-close]").onclick = () => dialog.close();
  return function open() {
    const body = dialog.querySelector("[data-body]");
    body.replaceChildren();
    if (!dialog.open) dialog.showModal();
    return fill(body);
  };
}

function legendList(layer) {
  const rows = (layer ? layer.legend : []).map((item) => {
    const row = element("span", null, "legend-line");
    const swatch = element("span", undefined, "swatch");
    swatch.style.backgroundColor = item.color;
    row.append(swatch, element("span", STRINGS.classWithConfidence(item.label, item.confidence)));
    return row;
  });
  return list([...rows, STRINGS.helpNoColor]);
}

// SCR-05. `getPair` returns the selected pair, or null when there is none.
export function fillHelp(body, getPair) {
  const pair = getPair();
  const layer = pair ? pair.layers.find((item) => item.kind === "new_material") : null;
  const official = element("p", `${STRINGS.helpOfficial} `);
  official.append(externalLink(STRINGS.helpOfficialLink, STRINGS.helpOfficialUrl));
  body.append(
    element("h3", STRINGS.helpHowRadarTitle), ...STRINGS.helpHowRadar.map((text) => element("p", text)),
    element("h3", STRINGS.helpColorsTitle), legendList(layer),
    element("h3", STRINGS.helpConfidenceTitle), list(STRINGS.helpConfidence),
    element("h3", STRINGS.helpLimitsTitle), list(STRINGS.helpLimits),
    element("h3", STRINGS.helpOfficialTitle), official,
  );
}

// GUNW, GCOV and so on are in the product's name: NISAR_L2_PR_GCOV_...
function productType(granuleId) {
  return granuleId.split("_")[3] || "";
}

// The dates in a granule's name, shown in the site's own time zone.
function granuleDates(granuleId, timeZone) {
  const stamps = granuleId.match(/\d{8}T\d{6}/g) || [];
  const starts = productType(granuleId) === "GUNW" ? [stamps[0], stamps[2]] : [stamps[0]];
  return starts.filter(Boolean).map((stamp) => {
    const utc = `${stamp.slice(0, 4)}-${stamp.slice(4, 6)}-${stamp.slice(6, 8)}T${stamp.slice(9, 11)}:${stamp.slice(11, 13)}:${stamp.slice(13, 15)}Z`;
    return localDate(utc, timeZone);
  }).join(", ");
}

function granuleRow(granuleId, maturity, timeZone) {
  const row = element("div", undefined, "granule");
  row.append(
    element("p", STRINGS.sourcesProduct(productType(granuleId), maturity)),
    element("p", STRINGS.sourcesDates(granuleDates(granuleId, timeZone))),
    externalLink(granuleId, VERTEX_URL + granuleId),
  );
  return row;
}

function radarSources(pair, timeZone) {
  // GUNW maturity isn't a pair.json field, so all products use the pair's pass maturity.
  const maturity = pair.passes[0].maturity;
  const groups = [];
  for (const layer of pair.layers) {
    groups.push(element("h4", layer.title));
    groups.push(...layer.source_granule_ids.map((id) => granuleRow(id, maturity, timeZone)));
  }
  return groups;
}

function contextSources(rows) {
  return list(rows.map((row) => {
    const line = element("span", `${STRINGS.sourcesContextLine(row.name, row.provider, row.license)} `);
    line.append(externalLink(STRINGS.sourcesContextLink, row.url));
    return line;
  }));
}

// SCR-06: radar data for the selected pair, and context data from sources.json.
export async function fillSources(body, getPair, timeZone) {
  const pair = getPair();
  const radar = pair ? radarSources(pair, timeZone) : [element("p", STRINGS.sourcesEmpty)];
  body.replaceChildren(element("h3", STRINGS.sourcesRadarTitle), ...radar,
    element("h3", STRINGS.sourcesContextTitle), element("p", STRINGS.sourcesLoading));
  const contextHolder = body.lastChild;
  try {
    contextHolder.replaceWith(contextSources(await loadJson("data/sources.json")));
  } catch (problem) {
    console.error(problem.message);
    const failed = element("p", `${STRINGS.sourcesError} `);
    failed.append(retryButton(() => fillSources(body, getPair, timeZone)));
    contextHolder.replaceWith(failed);
  }
}

// SCR-08: every published site. `onPick` loads the site and shows its own errors.
export function fillPicker(body, sites, onPick) {
  if (sites.length === 0) {
    body.append(element("p", STRINGS.pickerEmpty));
    return;
  }
  body.append(list(sites.map((site) => {
    const button = element("button", STRINGS.pickerOption(site.name, site.country), "wide-button");
    button.type = "button";
    button.onclick = () => onPick(site);
    return button;
  })));
}

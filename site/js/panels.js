// Tasks T-030, T-031, T-035 and T-145: the "What am I looking at?" panel, the Data sources
// panel and the "How we checked this" panel, with "Tested in Panama". Text from data files is set with textContent, never as HTML.

import { loadJson, loadValidation } from "./data.js";
import { STRINGS, textFor } from "./strings.js";
import { localDate } from "./timeline.js";

const VERTEX_URL = "https://search.asf.alaska.edu/#/?dataset=NISAR&searchType=List%20Search&searchList=";

export function element(tag, text, className) {
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

function legendList(layer, text) {
  if (!layer) return list([...text.helpClasses, text.helpNoColor]);
  const rows = layer.legend.map((item) => {
    const row = element("span", null, "legend-line");
    const swatch = element("span", undefined, "swatch");
    swatch.style.backgroundColor = item.color;
    row.append(swatch, element("span", STRINGS.classWithConfidence(item.label, item.confidence)));
    return row;
  });
  return list([...rows, text.helpNoColor]);
}

// SCR-05. `getPair` returns the selected pair, or null when there is none.
export function fillHelp(body, getPair, site) {
  const text = textFor(site);
  const pair = getPair();
  const layer = pair ? pair.layers.find((item) => item.kind === "new_material") : null;
  const official = element("p", `${text.helpOfficial} `);
  official.append(externalLink(text.helpOfficialLink, text.helpOfficialUrl));
  body.append(
    element("h3", STRINGS.helpHowRadarTitle), ...text.helpHowRadar.map((paragraph) => element("p", paragraph)),
    element("h3", STRINGS.helpColorsTitle), legendList(layer, text),
    element("h3", STRINGS.helpConfidenceTitle), list(STRINGS.helpConfidence),
    element("h3", STRINGS.helpLimitsTitle), list(text.helpLimits),
    element("h3", STRINGS.helpOfficialTitle), official,
    moreLinks(body),
  );
}

// FR-090: on a phone the bottom bar is gone, so its two links are here. The CSS shows them on phones only.
function moreLinks(body) {
  const holder = element("div", undefined, "help-more");
  holder.append(element("h3", STRINGS.helpMoreTitle));
  for (const [id, text] of [["sources-button", STRINGS.sourcesButton], ["check-button", STRINGS.checkButton]]) {
    const button = element("button", text, "wide-button");
    button.type = "button";
    button.dataset.opens = id;
    button.onclick = () => {
      body.closest("dialog").close();
      document.getElementById(id).click();
    };
    holder.append(button);
  }
  return holder;
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

function sourceList(rows) {
  return list(rows.map((row) => {
    const line = element("span", `${STRINGS.sourcesContextLine(row.name, row.provider, row.license)} `);
    line.append(externalLink(STRINGS.sourcesContextLink, row.url));
    return line;
  }));
}

// SCR-06: radar data for the selected pair, and the rows of sources.json: this site's sources and
// the shared ones, which have no site_id. A radar source goes under the radar heading.
export async function fillSources(body, getPair, site) {
  const pair = getPair();
  const radar = pair ? radarSources(pair, site.time_zone) : [element("p", STRINGS.sourcesEmpty)];
  const radarHolder = element("div");
  body.replaceChildren(element("h3", STRINGS.sourcesRadarTitle), radarHolder, ...radar,
    element("h3", STRINGS.sourcesContextTitle), element("p", STRINGS.sourcesLoading));
  const contextHolder = body.lastChild;
  try {
    const rows = await loadJson("data/sources.json");
    const shown = rows.filter((row) => !row.site_id || row.site_id === site.id);
    radarHolder.replaceWith(sourceList(shown.filter((row) => row.used_for === "radar")));
    contextHolder.replaceWith(sourceList(shown.filter((row) => row.used_for !== "radar")));
  } catch (problem) {
    console.error(problem.message);
    radarHolder.remove();
    const failed = element("p", `${STRINGS.sourcesError} `);
    failed.append(retryButton(() => fillSources(body, getPair, site)));
    contextHolder.replaceWith(failed);
  }
}

function checkTable(items) {
  const table = element("table", undefined, "check-table");
  const head = element("tr");
  head.append(...STRINGS.checkColumns.map((title) => element("th", title)));
  table.append(head);
  for (const item of items) {
    const row = element("tr");
    row.append(
      element("td", item.place_name),
      element("td", item.reported_in_source ? STRINGS.checkYes : STRINGS.checkNo),
      element("td", STRINGS.checkDetected[item.detected]),
      element("td", item.note || ""),
    );
    table.append(row);
  }
  return table;
}

// SCR-07: the pair's validation record. No record is normal, not an error (FR-048).
// The earthquake pair is the one whose dates hold the site's event; the quiet pair comes just before it.
// Returns the sentence with both areas from the published records, or without numbers if they can't load.
async function testedMore(site) {
  try {
    const folder = `data/sites/${site.id}`;
    const [pairs, events] = await Promise.all([loadJson(`${folder}/pairs.json`), loadJson(`${folder}/events.json`)]);
    const when = new Date(events[0].event_date);
    const index = pairs.findIndex((pair) =>
      new Date(pair.before_acquired_start) < when && when <= new Date(pair.after_acquired_start));
    if (index < 1) return STRINGS.testedMoreNoNumbers;
    const area = (pair) => pair.new_material_area_km2.toFixed(2);
    return STRINGS.testedMore(area(pairs[index - 1]), area(pairs[index]));
  } catch (problem) {
    console.warn(problem.message);
    return STRINGS.testedMoreNoNumbers;
  }
}

// FR-100: on Mayon, the panel ends with the Panama test. `tested` is { site, open } or null.
async function testedSection(tested) {
  const section = element("section", undefined, "tested");
  const link = element("a", STRINGS.testedLink);
  link.href = `?site=${tested.site.id}`;
  link.onclick = (event) => {
    event.preventDefault();
    tested.open();
  };
  const more = element("p", await testedMore(tested.site));
  section.append(element("h3", STRINGS.testedTitle), element("p", STRINGS.testedMethod), more,
    element("p", STRINGS.testedMatch), element("p", undefined));
  section.lastChild.append(link);
  return section;
}

export async function fillCheck(body, getPair, tested = null) {
  // The Panama section comes after whatever this pair's check says, even when that fails.
  const withTested = async (...parts) => {
    body.replaceChildren(...parts);
    if (tested) body.append(await testedSection(tested));
  };
  const pair = getPair();
  if (!pair) {
    await withTested(element("p", STRINGS.checkEmpty));
    return;
  }
  body.replaceChildren(element("p", STRINGS.checkLoading));
  try {
    const record = await loadValidation(pair.folder);
    if (!record) {
      // A pair can say why it has no check of its own.
      await withTested(element("p", pair.check_note || STRINGS.checkEmpty));
      return;
    }
    const source = element("p", `${STRINGS.checkSource(record.source_name, record.source_date)} `);
    source.append(externalLink(STRINGS.checkSourceLink, record.source_url));
    await withTested(source, element("p", record.method), checkTable(record.items));
  } catch (problem) {
    console.error(problem.message);
    const failed = element("p", `${STRINGS.checkError} `);
    failed.append(retryButton(() => fillCheck(body, getPair, tested)));
    await withTested(failed);
  }
}

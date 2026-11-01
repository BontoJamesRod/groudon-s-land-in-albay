// Task T-105: the brightness histogram (F-21). It shows how much the ground's brightness changed,
// where the flag line falls, and which edges count as flagged. The line comes from the pair's own
// record and can't be moved: the rule was fixed first, so moving it would undo that (FR-074).

import { loadJson } from "./data.js";
import { STRINGS, textFor } from "./strings.js";

const SVG = "http://www.w3.org/2000/svg";
const WIDTH = 320;
const HEIGHT = 96;
const AXIS_ROOM = 16; // room under the bars for the dB labels
const TOP_ROOM = 14; // room over the bars for the line's labels

function svgElement(name, attributes, text) {
  const item = document.createElementNS(SVG, name);
  for (const [key, value] of Object.entries(attributes)) item.setAttribute(key, value);
  if (text !== undefined) item.textContent = text;
  return item;
}

// Each share as a fraction of its own ground, so that a strip can sit on the same chart as the whole site.
function sharesOf(row) {
  return row.counts.map((count) => (row.total_cells ? count / row.total_cells : 0));
}

function signedDb(value) {
  return value > 0 ? `+${value}` : `${value}`.replace("-", "−");
}

function draw(histogram, threshold, channelRow) {
  const { bin_start_db: start, bin_width_db: width } = histogram;
  const shares = sharesOf(histogram);
  const outline = channelRow ? sharesOf(channelRow) : null;
  const end = start + width * shares.length;
  const x = (db) => ((db - start) / (end - start)) * WIDTH;
  // Most cells sit in a few bins, and the flagged edges would be too small to see on a plain scale.
  // A square-root scale keeps both in view, and the caption says so.
  const tallest = Math.max(...shares, ...(outline || [0])) || 1;
  const floor = HEIGHT - AXIS_ROOM;
  const y = (share) => floor - Math.sqrt(share / tallest) * (floor - TOP_ROOM);

  const chart = svgElement("svg", { viewBox: `0 0 ${WIDTH} ${HEIGHT}`, role: "img", class: "histogram-chart",
    "aria-label": STRINGS.histogramAlt(threshold, histogram.flagged_share) });
  shares.forEach((share, index) => {
    if (!share) return;
    const low = start + index * width;
    const flagged = low >= threshold || low + width <= -threshold;
    const bar = svgElement("rect", { x: x(low), y: y(share), width: Math.max(x(low + width) - x(low) - 0.5, 0.5),
      height: floor - y(share), class: flagged ? "histogram-bar histogram-flagged" : "histogram-bar" });
    bar.append(svgElement("title", {}, STRINGS.histogramBin(signedDb(low), signedDb(low + width), share)));
    chart.append(bar);
  });
  if (outline) {
    const points = [`0,${floor}`];
    outline.forEach((share, index) => {
      const low = start + index * width;
      points.push(`${x(low)},${y(share)}`, `${x(low + width)},${y(share)}`);
    });
    points.push(`${WIDTH},${floor}`);
    chart.append(svgElement("polyline", { points: points.join(" "), class: "histogram-outline" }));
  }
  chart.append(svgElement("line", { x1: 0, x2: WIDTH, y1: floor, y2: floor, class: "histogram-axis" }));
  for (const side of [-threshold, threshold]) {
    chart.append(svgElement("line", { x1: x(side), x2: x(side), y1: TOP_ROOM - 2, y2: floor, class: "histogram-line", "data-db": side }));
    chart.append(svgElement("text", { x: x(side), y: 10, class: "histogram-label", "text-anchor": "middle" }, `${signedDb(side)} dB`));
  }
  const labels = [[0, "start", STRINGS.histogramDarker], [WIDTH / 2, "middle", STRINGS.histogramNoChange], [WIDTH, "end", STRINGS.histogramBrighter]];
  for (const [position, anchor, text] of labels) {
    chart.append(svgElement("text", { x: position, y: HEIGHT - 3, class: "histogram-label", "text-anchor": anchor }, text));
  }
  return chart;
}

// `elements` are the chart's box, its sentence and its note. Returns what the rest of the app calls.
export function createHistogram(elements, site) {
  let current = null; // what's on screen: the pair, its histogram and the channel rows
  let channel = null;
  let request = 0;

  function render() {
    if (!current) return;
    const row = channel && current.channels ? current.channels.find((item) => item.channel_id === channel.properties.id) : null;
    const channelRow = row && row.total_cells ? row : null;
    elements.chart.replaceChildren(draw(current.histogram, current.threshold, channelRow));
    elements.sentence.textContent = current.histogram.flagged_cells
      ? STRINGS.histogramSentence(current.histogram.flagged_share)
      : STRINGS.histogramNothingFlagged;
    elements.note.textContent = channelRow ? STRINGS.histogramChannelNote(channel.properties.name) : STRINGS.histogramScaleNote(site);
  }

  return {
    // Never rejects: a missing chart mustn't stop a pair from showing (US-027/AC-3).
    async show(pair) {
      request += 1;
      const thisRequest = request;
      try {
        const [histogram, channels] = await Promise.all([
          loadJson(`${pair.folder}/histogram.json`),
          site.channel_strip_half_width_m == null ? null
            : loadJson(`${pair.folder}/channel_histogram.json`).then((row) => row.channels).catch(() => null),
        ]);
        if (thisRequest !== request) return;
        current = { histogram, channels, threshold: pair.brightness_threshold_db };
        render();
      } catch (problem) {
        if (thisRequest !== request) return;
        console.error(problem.message);
        current = null;
        elements.chart.replaceChildren();
        elements.sentence.textContent = textFor(site).histogramMissing;
        elements.note.textContent = "";
      }
    },
    setChannel(selected) {
      channel = selected;
      render();
    },
  };
}

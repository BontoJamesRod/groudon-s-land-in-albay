// Task T-029: the before and after radar images on either side of a draggable divider.
//
// Both images sit on the map, one over the other. Each shows only its own side of
// the divider, using a clip that is worked out again whenever the map moves.

import { COMPARE_LINE_PANE, COMPARE_PANE } from "./map.js";
import { STRINGS } from "./strings.js";
import { localDate } from "./timeline.js";

const KEY_STEP_PX = 20;

function preload(url) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = resolve;
    image.onerror = () => reject(new Error(`Image failed to load: ${url}`));
    image.src = url;
  });
}

// `elements`: view, divider, beforeLabel, afterLabel, close, message.
// `hideRadar(hidden)` hides the new-material layer while comparing.
export function createCompare(map, elements, site, hideRadar) {
  let overlays = null;
  let fraction = 0.5; // where the divider is, as a share of the map's width
  let request = 0; // closing, or opening again, cancels a load that is still running
  let wanted = false; // the visitor asked for compare and hasn't closed it

  // The visible line sits in the map's own layers, under the labels, so that labels stay
  // still and readable while it passes behind them. The invisible grip above it takes the drag.
  const line = L.DomUtil.create("div", "compare-line", map.getPane(COMPARE_LINE_PANE));
  line.hidden = true;

  function placeLine(dividerX) {
    L.DomUtil.setPosition(line, map.containerPointToLayerPoint([dividerX, 0]));
    line.style.height = `${map.getSize().y}px`;
    line.hidden = false;
  }

  function applyClip() {
    if (!overlays) return;
    const width = map.getSize().x;
    const dividerX = fraction * width;
    elements.divider.style.left = `${dividerX}px`;
    elements.divider.setAttribute("aria-valuenow", String(Math.round(fraction * 100)));
    const left = map.latLngToContainerPoint(overlays.before.getBounds().getNorthWest()).x;
    const right = map.latLngToContainerPoint(overlays.before.getBounds().getSouthEast()).x;
    // How far the divider is from the image's left edge, kept within the image.
    const split = Math.min(Math.max(dividerX - left, 0), right - left);
    overlays.before.getElement().style.clipPath = `inset(0 ${right - left - split}px 0 0)`;
    overlays.after.getElement().style.clipPath = `inset(0 0 0 ${split}px)`;
    placeLine(dividerX);
  }

  function hide() {
    request += 1;
    if (!overlays) return;
    overlays.before.remove();
    overlays.after.remove();
    overlays = null;
    map.off("move zoom zoomend resize", applyClip);
    line.hidden = true;
    elements.view.hidden = true;
    hideRadar(false);
  }

  function close() {
    wanted = false;
    hide();
  }

  function moveDivider(clientX) {
    const box = map.getContainer().getBoundingClientRect();
    fraction = Math.min(Math.max((clientX - box.left) / box.width, 0), 1);
    applyClip();
  }

  elements.divider.onpointerdown = (event) => {
    elements.divider.setPointerCapture(event.pointerId);
    elements.divider.onpointermove = (move) => moveDivider(move.clientX);
    // A drag here must not also pan the map.
    event.stopPropagation();
    event.preventDefault();
  };
  elements.divider.onpointerup = () => {
    elements.divider.onpointermove = null;
  };
  // A phone can take a touch away, for example for a system gesture.
  elements.divider.onpointercancel = elements.divider.onpointerup;
  elements.divider.onkeydown = (event) => {
    const step = { ArrowLeft: -KEY_STEP_PX, ArrowRight: KEY_STEP_PX }[event.key];
    if (!step) return;
    event.preventDefault();
    const box = map.getContainer().getBoundingClientRect();
    moveDivider(box.left + fraction * box.width + step);
  };
  elements.close.onclick = close;

  function imageUrl(pair, kind) {
    const layer = pair.layers.find((item) => item.kind === kind);
    return layer ? { layer, url: `${pair.folder}/${layer.image_path}` } : null;
  }

  function addOverlay({ layer, url }) {
    const bounds = [[layer.bounds_south, layer.bounds_west], [layer.bounds_north, layer.bounds_east]];
    return L.imageOverlay(url, bounds, { pane: COMPARE_PANE, className: "radar-image", alt: layer.title }).addTo(map);
  }

  // Load both images first. If either fails, the map stays exactly as it was (FR-020).
  async function open(pair) {
    wanted = true;
    hide();
    const thisRequest = request;
    elements.message.textContent = STRINGS.compareLoading;
    const before = pair && imageUrl(pair, "before_db");
    const after = pair && imageUrl(pair, "after_db");
    try {
      if (!before || !after) throw new Error("The pair has no before or after layer");
      await Promise.all([preload(before.url), preload(after.url)]);
    } catch (problem) {
      console.error(problem.message);
      if (thisRequest === request) {
        wanted = false;
        elements.message.textContent = STRINGS.compareMissing;
      }
      return;
    }
    if (thisRequest !== request) return;
    elements.message.textContent = "";
    hideRadar(true);
    overlays = { before: addOverlay(before), after: addOverlay(after) };
    elements.beforeLabel.textContent = STRINGS.compareBefore(localDate(pair.before_acquired_start, site.time_zone));
    elements.afterLabel.textContent = STRINGS.compareAfter(localDate(pair.after_acquired_start, site.time_zone));
    elements.view.hidden = false;
    map.on("move zoom zoomend resize", applyClip);
    applyClip();
  }

  // A different pair is now selected. A visitor who is comparing keeps comparing, with the
  // new pair's images. Closing here is what used to make the view snap back: a pair that was
  // still loading when Compare was clicked closed the view as soon as it arrived.
  function pairChanged(pair) {
    elements.message.textContent = "";
    if (wanted) open(pair);
    else hide();
  }

  return { open, close, pairChanged };
}

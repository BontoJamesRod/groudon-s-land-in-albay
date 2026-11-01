// Task T-111: flagged cells as marks that stay visible at any zoom (F-22, FR-078).
// One radar cell can be smaller than a screen pixel, and then it vanishes from the image. This reads
// the pair's own image and draws each coloured cell again on a canvas above it, at a minimum size
// with a darker edge. Only the drawing changes: the image, the grid and the areas stay as published.

const MIN_MARK_PX = 5;
// Zoomed out, the same marks would run together and make the change look bigger than it is.
const MIN_MARK_PX_FAR = 3;
const FAR_BELOW_ZOOM = 12;
const EDGE_PX = 1;
const EDGE_COLOR = "#3b1d00";
const VISIBLE_ALPHA = 128; // the image's cells are either see-through or solid

// The coloured cells of a loaded image, in groups by colour.
function readCells(image) {
  const canvas = document.createElement("canvas");
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  context.drawImage(image, 0, 0);
  const { data } = context.getImageData(0, 0, canvas.width, canvas.height);
  const groups = new Map();
  for (let i = 0; i < data.length; i += 4) {
    if (data[i + 3] < VISIBLE_ALPHA) continue;
    const color = `rgb(${data[i]}, ${data[i + 1]}, ${data[i + 2]})`;
    if (!groups.has(color)) groups.set(color, { color, brightness: data[i] + data[i + 1] + data[i + 2], cells: [] });
    const cell = i / 4;
    groups.get(color).cells.push(cell % canvas.width, Math.floor(cell / canvas.width));
  }
  // Darker colours are the higher confidence, so they're drawn last, on top.
  const sorted = [...groups.values()].sort((a, b) => b.brightness - a.brightness);
  return { width: canvas.width, height: canvas.height, groups: sorted };
}

// A map layer for the given pane. `image` is the pair's loaded image, and `bounds` is where the map shows it.
export function createMarks(image, bounds, pane) {
  const { width, height, groups } = readCells(image);
  const canvas = L.DomUtil.create("canvas", "radar-marks leaflet-zoom-hide");
  canvas.setAttribute("aria-hidden", "true"); // the image beside it already has the text
  canvas.dataset.cells = groups.reduce((sum, group) => sum + group.cells.length / 2, 0);
  let map = null;

  function draw() {
    const size = map.getSize();
    const scale = window.devicePixelRatio || 1;
    canvas.width = size.x * scale;
    canvas.height = size.y * scale;
    canvas.style.width = `${size.x}px`;
    canvas.style.height = `${size.y}px`;
    L.DomUtil.setPosition(canvas, map.containerPointToLayerPoint([0, 0]));
    const context = canvas.getContext("2d");
    context.scale(scale, scale);
    // The map stretches the image evenly between its corners, so each cell is found the same way.
    const corner = map.latLngToContainerPoint([bounds[1][0], bounds[0][1]]);
    const opposite = map.latLngToContainerPoint([bounds[0][0], bounds[1][1]]);
    const cellWidth = (opposite.x - corner.x) / width;
    const cellHeight = (opposite.y - corner.y) / height;
    const smallest = map.getZoom() < FAR_BELOW_ZOOM ? MIN_MARK_PX_FAR : MIN_MARK_PX;
    const markWidth = Math.max(cellWidth, smallest);
    const markHeight = Math.max(cellHeight, smallest);
    canvas.dataset.markWidth = markWidth;

    function paint(color, grow) {
      context.fillStyle = color;
      for (const group of groups) {
        if (grow === 0) context.fillStyle = group.color;
        for (let i = 0; i < group.cells.length; i += 2) {
          const x = corner.x + (group.cells[i] + 0.5) * cellWidth - markWidth / 2 - grow;
          const y = corner.y + (group.cells[i + 1] + 0.5) * cellHeight - markHeight / 2 - grow;
          if (x > size.x || y > size.y || x + markWidth < -grow || y + markHeight < -grow) continue;
          context.fillRect(x, y, markWidth + grow * 2, markHeight + grow * 2);
        }
      }
    }

    // All the edges first, so that touching cells read as one patch with a dark outline.
    paint(EDGE_COLOR, EDGE_PX);
    paint(null, 0);
  }

  const Marks = L.Layer.extend({
    onAdd(added) {
      map = added;
      map.getPane(pane).append(canvas);
      map.on("moveend zoomend resize", draw);
      draw();
    },
    onRemove() {
      canvas.remove();
      map.off("moveend zoomend resize", draw);
    },
  });
  return new Marks();
}

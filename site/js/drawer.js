// The phone drawer: on a small screen the map comes first, and the pair's details
// and legend slide up when asked for. On a large screen the CSS hides the handle
// and always shows everything, so nothing here has any effect there.

import { STRINGS } from "./strings.js";

const SWIPE_PX = 30; // a finger moving less than this is a tap, not a swipe

// `onResize` runs after the drawer changes the map's height.
export function createDrawer(panel, toggle, onResize) {
  let startY = null;
  let swiped = false;

  function setOpen(open) {
    panel.classList.toggle("drawer-closed", !open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.textContent = open ? STRINGS.drawerHide : STRINGS.drawerShow;
    onResize();
  }

  const isOpen = () => !panel.classList.contains("drawer-closed");

  toggle.onpointerdown = (event) => {
    // Keep getting this pointer's events after it moves off the handle.
    toggle.setPointerCapture(event.pointerId);
    startY = event.clientY;
    swiped = false;
  };
  toggle.onpointerup = (event) => {
    if (startY === null) return;
    const moved = event.clientY - startY;
    startY = null;
    if (Math.abs(moved) < SWIPE_PX) return;
    swiped = true;
    setOpen(moved < 0); // up opens, down closes
  };
  toggle.onpointercancel = () => {
    startY = null;
  };
  // A swipe also ends in a click, which must not toggle the drawer straight back.
  toggle.onclick = () => {
    if (!swiped) setOpen(!isOpen());
    swiped = false;
  };

  setOpen(false);
  return { close: () => setOpen(false) };
}

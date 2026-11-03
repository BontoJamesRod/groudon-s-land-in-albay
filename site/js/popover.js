// Task T-132: one small info button (ⓘ) with a popover, used wherever a panel keeps only a short
// line and moves its explanation out of the way (FR-088, FR-089).
//
// It follows WCAG 1.4.13, "Content on hover or focus":
//   dismissible: Escape closes it without moving the pointer or the focus,
//   hoverable: the pointer can move from the button onto the popover without it closing,
//   persistent: it stays open until the pointer or the focus leaves, or the visitor closes it.
// A tap or Enter keeps it open until the visitor taps outside or presses Escape.

import { STRINGS } from "./strings.js";

const OPEN_DELAY_MS = 300; // a pointer passing over on its way somewhere else doesn't open it
const CLOSE_DELAY_MS = 400; // time to move from the button onto the popover
const EDGE_PX = 8; // keep the popover this far from the window's edges
let openInfo = null; // only one popover is open at a time
let count = 0;

function place(info) {
  const button = info.button.getBoundingClientRect();
  const popover = info.popover;
  const width = Math.min(300, window.innerWidth - 2 * EDGE_PX);
  popover.style.width = `${width}px`;
  const left = Math.min(Math.max(button.left + button.width / 2 - width / 2, EDGE_PX), window.innerWidth - EDGE_PX - width);
  // Below the button, or above it when there isn't room below.
  const below = button.bottom + 4;
  const above = button.top - 4 - popover.offsetHeight;
  const top = below + popover.offsetHeight > window.innerHeight - EDGE_PX && above > EDGE_PX ? above : below;
  popover.style.left = `${left}px`;
  popover.style.top = `${top}px`;
}

// Turn `holder` into an info button with a popover. Its children become the popover's content.
// `what` finishes the button's spoken name: "More about <what>".
export function makeInfo(holder, what) {
  count += 1;
  const button = document.createElement("button");
  button.type = "button";
  button.className = "info-button";
  button.setAttribute("aria-label", STRINGS.infoLabel(what));
  button.setAttribute("aria-expanded", "false");
  const glyph = document.createElement("span");
  glyph.className = "info-glyph";
  glyph.setAttribute("aria-hidden", "true");
  glyph.textContent = "i";
  button.append(glyph);
  const popover = document.createElement("div");
  popover.className = "info-popover";
  popover.id = `info-${count}`;
  popover.hidden = true;
  popover.append(...holder.childNodes);
  button.setAttribute("aria-controls", popover.id);
  holder.classList.add("info");
  holder.replaceChildren(button, popover);

  let openTimer = null;
  let closeTimer = null;
  let pinned = false; // opened by a tap, a click or Enter: it stays until closed on purpose
  const info = { holder, button, popover };

  function stopTimers() {
    clearTimeout(openTimer);
    clearTimeout(closeTimer);
  }

  info.show = () => {
    stopTimers();
    if (openInfo && openInfo !== info) openInfo.hide();
    popover.hidden = false;
    button.setAttribute("aria-expanded", "true");
    place(info);
    openInfo = info;
  };

  info.hide = () => {
    stopTimers();
    pinned = false;
    popover.hidden = true;
    button.setAttribute("aria-expanded", "false");
    if (openInfo === info) openInfo = null;
  };

  // A mouse: open after a short pause, and close a little after it leaves both button and popover.
  holder.addEventListener("pointerenter", (event) => {
    if (event.pointerType !== "mouse") return;
    clearTimeout(closeTimer);
    if (popover.hidden) openTimer = setTimeout(info.show, OPEN_DELAY_MS);
  });
  holder.addEventListener("pointerleave", (event) => {
    if (event.pointerType !== "mouse") return;
    clearTimeout(openTimer);
    if (!pinned && !holder.contains(document.activeElement)) closeTimer = setTimeout(info.hide, CLOSE_DELAY_MS);
  });

  // A tap, a click or Enter. A click on a popover that a hover opened keeps it open.
  button.addEventListener("click", (event) => {
    const byMouse = event.detail > 0 && event.pointerType === "mouse";
    if (popover.hidden) {
      pinned = true;
      info.show();
    } else if (byMouse && !pinned) {
      pinned = true;
    } else {
      info.hide();
    }
  });

  // The keyboard: reaching the button opens it, and moving on closes it.
  button.addEventListener("focus", () => {
    if (button.matches(":focus-visible") && popover.hidden) info.show();
  });
  holder.addEventListener("focusout", (event) => {
    if (!holder.contains(event.relatedTarget) && !pinned) info.hide();
  });
  return info;
}

// Make every `[data-info]` holder in `root` into an info button. Its value names what it explains.
export function setUpInfos(root = document) {
  root.querySelectorAll("[data-info]").forEach((holder) => {
    makeInfo(holder, STRINGS.infoWhat[holder.dataset.info]);
    holder.removeAttribute("data-info");
  });
}

// Make an info button with these nodes in its popover, for content built while the app runs.
export function newInfo(what, ...nodes) {
  const holder = document.createElement("span");
  holder.append(...nodes);
  return makeInfo(holder, what).holder;
}

// Escape and a tap or click outside close the open popover. A focus inside it goes back to its button.
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !openInfo) return;
  const info = openInfo;
  const hadFocus = info.holder.contains(document.activeElement);
  info.hide();
  if (hadFocus) info.button.focus();
  // Escape is for this popover only: a dialog or the compare view behind it stays open.
  event.stopPropagation();
  event.preventDefault();
}, true);
document.addEventListener("pointerdown", (event) => {
  if (openInfo && !openInfo.holder.contains(event.target)) openInfo.hide();
}, true);
// The popover sits over the page, so it follows its button when anything scrolls or resizes.
window.addEventListener("scroll", () => openInfo && place(openInfo), true);
window.addEventListener("resize", () => openInfo && place(openInfo));

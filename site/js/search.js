// Task T-027: find a town by name. Suggestions start after 2 letters (FR-007). Choosing
// a town centers the map and opens its readout (FR-008). Nothing typed leaves the browser.

import { STRINGS } from "./strings.js";

const MIN_LETTERS = 2;

export function matchingTowns(towns, text) {
  const wanted = text.trim().toLowerCase();
  if (wanted.length < MIN_LETTERS) return [];
  return towns.features.filter((town) => town.properties.name.toLowerCase().includes(wanted));
}

// What pressing Enter should pick: the town with exactly that name, or the only match.
function townToSubmit(matches, text) {
  const wanted = text.trim().toLowerCase();
  const exact = matches.find((town) => town.properties.name.toLowerCase() === wanted);
  if (exact) return exact;
  return matches.length === 1 ? matches[0] : null;
}

// `onPick` receives the chosen town. Returns open() and close().
export function createSearch(elements, towns, onPick) {
  function close() {
    elements.panel.hidden = true;
  }

  function pick(town) {
    close();
    onPick(town);
  }

  function showSuggestions(matches) {
    const rows = matches.map((town) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = town.properties.name;
      button.onclick = () => pick(town);
      const row = document.createElement("li");
      row.append(button);
      return row;
    });
    elements.suggestions.replaceChildren(...rows);
  }

  elements.input.oninput = () => {
    elements.message.textContent = elements.input.value ? "" : STRINGS.searchHint;
    showSuggestions(matchingTowns(towns, elements.input.value));
  };

  elements.form.onsubmit = (event) => {
    event.preventDefault();
    const text = elements.input.value;
    const matches = towns.features.filter((town) => town.properties.name.toLowerCase().includes(text.trim().toLowerCase()));
    if (!text.trim() || matches.length === 0) {
      showSuggestions([]);
      elements.message.textContent = STRINGS.searchNoMatch;
      return;
    }
    const town = townToSubmit(matches, text);
    if (town) pick(town);
    else showSuggestions(matches);
  };

  elements.close.onclick = close;

  function open() {
    elements.panel.hidden = false;
    elements.input.value = "";
    elements.message.textContent = STRINGS.searchHint;
    showSuggestions([]);
    elements.input.focus();
  }

  return { open, close };
}

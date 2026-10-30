// Task T-024: the pair list, Previous and Next, the label and the event markers.
// Pairs arrive oldest first (docs/06, API-007), so the latest pair is the last one.

const LATEST_MESSAGE = "This is the latest pass";

// Format a UTC time as a day in the site's own time zone (FR-014).
export function localDate(utcText, timeZone) {
  return new Intl.DateTimeFormat("en-PH", { timeZone, year: "numeric", month: "short", day: "numeric" })
    .format(new Date(utcText));
}

// The same day as YYYY-MM-DD, so it can be compared with an event's date.
function localIsoDate(utcText, timeZone) {
  return new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" })
    .format(new Date(utcText));
}

// Find the events whose date falls inside a pair's dates (FR-016).
export function eventsInPair(pair, events, timeZone) {
  const first = localIsoDate(pair.before_acquired_start, timeZone);
  const last = localIsoDate(pair.after_acquired_start, timeZone);
  return events.filter((event) => event.event_date >= first && event.event_date <= last);
}

function pairDates(pair, timeZone) {
  return `${localDate(pair.before_acquired_start, timeZone)} to ${localDate(pair.after_acquired_start, timeZone)}`;
}

function pairLabel(pair, timeZone) {
  return `${pairDates(pair, timeZone)} (${timeZone}), track ${pair.track}, frame ${pair.frame}, ${pair.orbit_direction}`;
}

function optionText(pair, events, timeZone) {
  const names = eventsInPair(pair, events, timeZone).map((event) => event.name);
  return names.length ? `${pairDates(pair, timeZone)}: ${names.join(", ")}` : pairDates(pair, timeZone);
}

// Set up the timeline. `onSelect` loads a pair and rejects if it can't.
export function createTimeline(elements, site, pairs, events, onSelect) {
  const timeZone = site.time_zone;
  let selected = pairs.length - 1;

  function showSelected() {
    const pair = pairs[selected];
    elements.list.value = pair.id;
    elements.label.textContent = pairLabel(pair, timeZone);
    const names = eventsInPair(pair, events, timeZone).map((event) => event.name);
    elements.events.textContent = names.length ? `Event in this period: ${names.join(", ")}` : "";
    elements.previous.disabled = selected === 0;
  }

  // Keep the current pair on screen until the new one has loaded (03 section 5).
  async function select(index) {
    elements.message.textContent = "";
    elements.retry.hidden = true;
    try {
      await onSelect(pairs[index]);
      selected = index;
    } catch (problem) {
      console.error(problem.message);
      elements.message.textContent = "Couldn't load this pass. Try again.";
      elements.retry.hidden = false;
      elements.retry.onclick = () => select(index);
    }
    showSelected();
  }

  for (const pair of pairs) {
    const option = document.createElement("option");
    option.value = pair.id;
    option.textContent = optionText(pair, events, timeZone);
    elements.list.append(option);
  }
  elements.previous.addEventListener("click", () => {
    if (selected > 0) select(selected - 1);
  });
  elements.next.addEventListener("click", () => {
    if (selected === pairs.length - 1) {
      elements.message.textContent = LATEST_MESSAGE;
    } else {
      select(selected + 1);
    }
  });
  elements.list.addEventListener("change", () => {
    select(pairs.findIndex((pair) => pair.id === elements.list.value));
  });
  return select(selected);
}

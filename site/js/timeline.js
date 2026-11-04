// Task T-024: the pair list, Previous and Next, the label and the event markers.
// Pairs arrive oldest first (docs/06, API-007), so the latest pair is the last one.

import { STRINGS } from "./strings.js";

const USUAL_GAP_DAYS = 12;
const MS_PER_DAY = 86400000;

// Format a UTC time as a day in the site's own time zone (FR-014).
export function localDate(utcText, timeZone) {
  return new Intl.DateTimeFormat("en-PH", { timeZone, year: "numeric", month: "short", day: "numeric" })
    .format(new Date(utcText));
}

// A day's month, day and year as separate words, in the site's time zone.
function dayParts(utcText, timeZone) {
  const parts = new Intl.DateTimeFormat("en-PH", { timeZone, year: "numeric", month: "short", day: "numeric" })
    .formatToParts(new Date(utcText));
  return Object.fromEntries(parts.map((part) => [part.type, part.value]));
}

// The pass card's title, as short as it can be: "Oct 8 – 20, 2026", "Sep 26 – Oct 8, 2026",
// or "Dec 27, 2026 – Jan 8, 2027".
// Without `withYear`, the year only shows when the two days are in different years.
export function passTitle(pair, timeZone, withYear = true) {
  const a = dayParts(pair.before_acquired_start, timeZone);
  const b = dayParts(pair.after_acquired_start, timeZone);
  if (a.year !== b.year) return `${a.month} ${a.day}, ${a.year} – ${b.month} ${b.day}, ${b.year}`;
  const year = withYear ? `, ${b.year}` : "";
  if (a.month !== b.month) return `${a.month} ${a.day} – ${b.month} ${b.day}${year}`;
  return `${a.month} ${a.day} – ${b.day}${year}`;
}

// The month a pair starts in, in full: "June".
export function startMonth(pair, timeZone) {
  return new Intl.DateTimeFormat("en-PH", { timeZone, month: "long" }).format(new Date(pair.before_acquired_start));
}

// A short month for the chart's axis, from the day a pair starts: "Jun".
export function shortMonth(pair, timeZone) {
  return new Intl.DateTimeFormat("en-PH", { timeZone, month: "short" }).format(new Date(pair.before_acquired_start));
}

// When the satellite passed, on the site's clock: "morning pass, 5:13 AM".
function passTime(pair, timeZone) {
  const when = new Date(pair.after_acquired_start);
  const hour = Number(new Intl.DateTimeFormat("en-US", { timeZone, hour: "numeric", hourCycle: "h23" }).format(when));
  const time = new Intl.DateTimeFormat("en-US", { timeZone, hour: "numeric", minute: "2-digit" }).format(when);
  let part = STRINGS.partOfDay.evening;
  if (hour < 12) part = STRINGS.partOfDay.morning;
  else if (hour < 18) part = STRINGS.partOfDay.afternoon;
  return STRINGS.passSub(pair.track, part, time);
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

export function pairDates(pair, timeZone) {
  return STRINGS.pairRange(localDate(pair.before_acquired_start, timeZone), localDate(pair.after_acquired_start, timeZone));
}

// A longer gap can show more change, so its pair can't be compared with the others (FR-066).
// Passes on a track come at about the same time of day, so rounding gives the whole days.
export function gapNote(pair) {
  const days = Math.round((new Date(pair.after_acquired_start) - new Date(pair.before_acquired_start)) / MS_PER_DAY);
  return days === USUAL_GAP_DAYS ? null : STRINGS.gapNote(days);
}

function pairLabel(pair, timeZone) {
  return STRINGS.pairLabel(pairDates(pair, timeZone), timeZone, pair.track, pair.frame, pair.orbit_direction);
}

function optionText(pair, events, timeZone) {
  const names = eventsInPair(pair, events, timeZone).map((event) => event.name);
  const text = names.length ? STRINGS.optionWithEvents(pairDates(pair, timeZone), names.join(", ")) : pairDates(pair, timeZone);
  const note = gapNote(pair);
  return note ? STRINGS.optionWithGap(text, note) : text;
}

// Set up the timeline. `onSelect` loads a pair and rejects if it can't. It also gets a
// function that says if this is still the latest choice, as a slow load can arrive late.
export function createTimeline(elements, site, pairs, events, siteIsShown, onSelect) {
  const timeZone = site.time_zone;
  let selected = pairs.length - 1;
  let latestChoice = 0;

  function showSelected() {
    const pair = pairs[selected];
    elements.list.value = pair.id;
    const names = eventsInPair(pair, events, timeZone).map((event) => event.name);
    // A short title and one line under it, and the full dates, time zone, track and frame in its popover.
    elements.label.textContent = passTitle(pair, timeZone);
    elements.sub.textContent = [names.join(", "), passTime(pair, timeZone)].filter(Boolean).join(" · ");
    elements.detail.textContent = pairLabel(pair, timeZone);
    elements.events.textContent = names.length ? STRINGS.eventInPeriod(names.join(", ")) : "";
    elements.gap.textContent = gapNote(pair) || "";
    elements.list.classList.toggle("pair-dim", gapNote(pair) !== null);
    elements.previous.disabled = selected === 0;
  }

  // Keep the current pair on screen until the new one has loaded (03 section 5).
  async function select(index) {
    elements.message.textContent = "";
    elements.retry.hidden = true;
    latestChoice += 1;
    const thisChoice = latestChoice;
    const isCurrent = () => thisChoice === latestChoice && siteIsShown();
    try {
      await onSelect(pairs[index], isCurrent);
      if (!isCurrent()) return;
      selected = index;
    } catch (problem) {
      if (!isCurrent()) return;
      console.error(problem.message);
      elements.message.textContent = STRINGS.passLoadError;
      elements.retry.hidden = false;
      elements.retry.onclick = () => select(index);
    }
    showSelected();
  }

  elements.list.replaceChildren();
  for (const pair of pairs) {
    const option = document.createElement("option");
    option.value = pair.id;
    option.textContent = optionText(pair, events, timeZone);
    option.classList.toggle("pair-dim", gapNote(pair) !== null);
    elements.list.append(option);
  }
  elements.previous.onclick = () => {
    if (selected > 0) select(selected - 1);
  };
  elements.next.onclick = () => {
    if (selected === pairs.length - 1) {
      elements.message.textContent = STRINGS.latestPass;
    } else {
      select(selected + 1);
    }
  };
  elements.list.onchange = () => {
    select(pairs.findIndex((pair) => pair.id === elements.list.value));
  };
  return select(selected);
}

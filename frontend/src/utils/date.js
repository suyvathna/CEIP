// Local calendar date, not UTC - new Date().toISOString() shifts by the
// browser's UTC offset and would show yesterday's date for part of the
// day in Cambodia (UTC+7). Shared here so every "default to today" field
// (events, diaries) computes the same date the same way, instead of each
// page re-deriving it slightly differently.
export function todayLocalISODate() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

// HH:MM in the browser's local time, for defaulting an event's time
// field to "right now" alongside its date.
export function nowLocalTime() {
  const d = new Date();
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}

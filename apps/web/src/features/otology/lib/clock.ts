/** Display conversion for a datetime-local field. Not a clinical calculation. */

function parseUtcInstant(iso: string): Date {
  const trimmed = iso.trim();
  // Stored instants are naive UTC. Without a zone, Date parses them as local.
  const zoned = /(?:Z|[+-]\d{2}:\d{2})$/.test(trimmed);
  return new Date(zoned ? trimmed : `${trimmed}Z`);
}

export function isoToDateTimeLocal(iso: string, timeZone: string): string {
  const date = parseUtcInstant(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  const pick = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((part) => part.type === type)?.value ?? "";
  const hour = pick("hour") === "24" ? "00" : pick("hour");
  return `${pick("year")}-${pick("month")}-${pick("day")}T${hour}:${pick("minute")}`;
}

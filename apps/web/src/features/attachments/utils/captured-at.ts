/** Clinic-local capture instants stored as UTC ISO strings. Display only. */

function ymdInTimeZone(date: Date, timeZone: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function startOfLocalDay(ymd: string, timeZone: string): Date {
  let low = Date.parse(`${ymd}T00:00:00Z`) - 16 * 3_600_000;
  let high = Date.parse(`${ymd}T00:00:00Z`) + 16 * 3_600_000;
  while (low < high) {
    const mid = Math.floor((low + high) / 2);
    const midYmd = ymdInTimeZone(new Date(mid), timeZone);
    if (midYmd < ymd) {
      low = mid + 1;
    } else {
      high = mid;
    }
  }
  return new Date(low);
}

function addDaysYmd(ymd: string, days: number): string {
  const [year, month, day] = ymd.split("-").map(Number);
  const next = new Date(Date.UTC(year, month - 1, day + days));
  return next.toISOString().slice(0, 10);
}

export function startOfClinicDayUtcIso(
  ymd: string,
  timeZone: string,
): string | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(ymd)) {
    return null;
  }
  return startOfLocalDay(ymd, timeZone).toISOString();
}

export function nextClinicDayUtcIso(
  ymd: string,
  timeZone: string,
): string | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(ymd)) {
    return null;
  }
  return startOfLocalDay(addDaysYmd(ymd, 1), timeZone).toISOString();
}

export function dateTimeLocalToUtcIso(
  value: string,
  timeZone: string,
): string | null {
  const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})/.exec(value);
  if (!match) {
    return null;
  }
  const ymd = match[1];
  const hours = Number(match[2]);
  const minutes = Number(match[3]);
  const dayStart = startOfLocalDay(ymd, timeZone).getTime();
  let candidate = dayStart + (hours * 60 + minutes) * 60_000;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone,
      hour: "numeric",
      minute: "numeric",
      hour12: false,
    }).formatToParts(new Date(candidate));
    const hour = Number(parts.find((part) => part.type === "hour")?.value ?? 0);
    const minute = Number(
      parts.find((part) => part.type === "minute")?.value ?? 0,
    );
    const normalizedHour = hour === 24 ? 0 : hour;
    const deltaMin = hours * 60 + minutes - (normalizedHour * 60 + minute);
    if (deltaMin === 0) {
      break;
    }
    candidate += deltaMin * 60_000;
  }
  return new Date(candidate).toISOString();
}

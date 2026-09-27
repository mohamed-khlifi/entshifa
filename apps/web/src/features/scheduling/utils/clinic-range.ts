/** Calendar bounds in clinic timezone, expressed as UTC ISO instants (display only). */

export type CalendarView = "day" | "week";

export function ymdInTimeZone(date: Date, timeZone: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function startOfLocalDayUtc(ymd: string, timeZone: string): Date {
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
  const [y, m, d] = ymd.split("-").map(Number);
  const next = new Date(Date.UTC(y, m - 1, d + days));
  return next.toISOString().slice(0, 10);
}

export function clinicLocalTimeToUtcIso(
  ymd: string,
  time: string,
  timeZone: string,
): string {
  const [hh, mm] = time.split(":").map(Number);
  const dayStart = startOfLocalDayUtc(ymd, timeZone).getTime();
  let candidate = dayStart + (hh * 60 + mm) * 60_000;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone,
      hour: "numeric",
      minute: "numeric",
      hour12: false,
    }).formatToParts(new Date(candidate));
    const hour = Number(parts.find((p) => p.type === "hour")?.value ?? 0);
    const minute = Number(parts.find((p) => p.type === "minute")?.value ?? 0);
    const deltaMin = hh * 60 + mm - (hour * 60 + minute);
    if (deltaMin === 0) {
      break;
    }
    candidate += deltaMin * 60_000;
  }
  return new Date(candidate).toISOString();
}

export function rangeForCalendarView(
  anchor: Date,
  view: CalendarView,
  timeZone: string,
): { startsAfter: string; startsBefore: string; on: string } {
  const on = ymdInTimeZone(anchor, timeZone);
  const start = startOfLocalDayUtc(on, timeZone);
  const dayCount = view === "week" ? 7 : 1;
  const endYmd = addDaysYmd(on, dayCount);
  const end = startOfLocalDayUtc(endYmd, timeZone);
  return {
    on,
    startsAfter: start.toISOString(),
    startsBefore: end.toISOString(),
  };
}

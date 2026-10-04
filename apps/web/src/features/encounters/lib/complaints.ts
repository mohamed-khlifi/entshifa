export const COMPLAINT_REGIONS = [
  "balance",
  "ear",
  "nose",
  "other",
  "throat",
  "voice",
] as const;

export type ComplaintRegion = (typeof COMPLAINT_REGIONS)[number];

const REGION_BY_CODE: Record<string, ComplaintRegion> = {
  "CC.EAR_PAIN": "ear",
  "CC.EPISTAXIS": "nose",
  "CC.FACIAL_PAIN": "nose",
  "CC.HEARING_LOSS": "ear",
  "CC.HOARSENESS": "voice",
  "CC.NASAL_OBSTRUCTION": "nose",
  "CC.RHINORRHEA": "nose",
  "CC.SORE_THROAT": "throat",
  "CC.TINNITUS": "ear",
  "CC.VERTIGO": "balance",
};

export type ComplaintChoice = {
  code: string;
  conceptPublicId: string;
  display: string;
};

export type SelectedComplaint = ComplaintChoice & {
  isPrimary: boolean;
};

export function complaintRegion(code: string): ComplaintRegion {
  return REGION_BY_CODE[code] ?? "other";
}

export function groupComplaints<T extends { code: string; display: string }>(
  members: readonly T[],
  search: string,
): { region: ComplaintRegion; items: T[] }[] {
  const needle = search.trim().toLocaleLowerCase();
  const grouped = new Map<ComplaintRegion, T[]>();
  for (const member of members) {
    if (needle.length > 0) {
      const haystack = `${member.display} ${member.code}`.toLocaleLowerCase();
      if (!haystack.includes(needle)) {
        continue;
      }
    }
    const region = complaintRegion(member.code);
    const bucket = grouped.get(region) ?? [];
    bucket.push(member);
    grouped.set(region, bucket);
  }
  return COMPLAINT_REGIONS.flatMap((region) => {
    const items = grouped.get(region);
    return items && items.length > 0 ? [{ region, items }] : [];
  });
}

export function toggleComplaint(
  items: readonly SelectedComplaint[],
  next: ComplaintChoice,
): SelectedComplaint[] {
  const existing = items.find((item) => item.code === next.code);
  if (!existing) {
    return [
      ...items,
      {
        ...next,
        isPrimary: items.length === 0,
      },
    ];
  }
  const rest = items.filter((item) => item.code !== next.code);
  if (existing.isPrimary && rest[0] && !rest.some((item) => item.isPrimary)) {
    return rest.map((item, index) =>
      index === 0 ? { ...item, isPrimary: true } : item,
    );
  }
  return [...rest];
}

export function makePrimary(
  items: readonly SelectedComplaint[],
  code: string,
): SelectedComplaint[] {
  if (!items.some((item) => item.code === code)) {
    return [...items];
  }
  return items.map((item) => ({ ...item, isPrimary: item.code === code }));
}

export function primaryComplaint(
  items: readonly SelectedComplaint[],
): SelectedComplaint | null {
  return items.find((item) => item.isPrimary) ?? items[0] ?? null;
}

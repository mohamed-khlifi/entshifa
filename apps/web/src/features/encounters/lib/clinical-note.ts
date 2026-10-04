export type NoteLine = {
  label: string;
  value: string;
};

const CHIEF_SUMMARY_MAX = 255;

export function composeClinicalNote(
  lines: readonly NoteLine[],
  freeText: string,
  formatLine: (line: NoteLine) => string = (line) =>
    `${line.label}: ${line.value}`,
): string {
  const structured = lines
    .map((line) => ({
      label: line.label.trim(),
      value: line.value.trim(),
    }))
    .filter((line) => line.label.length > 0 && line.value.length > 0)
    .map((line) => formatLine(line));
  const note = freeText.trim();
  const body = structured.join("\n");
  if (body.length > 0 && note.length > 0) {
    return `${body}\n\n${note}`;
  }
  return body || note;
}

export function chiefComplaintSummary(display: string | null): string | null {
  const trimmed = display?.trim() ?? "";
  if (trimmed.length === 0) {
    return null;
  }
  return trimmed.length <= CHIEF_SUMMARY_MAX
    ? trimmed
    : trimmed.slice(0, CHIEF_SUMMARY_MAX);
}

export function emptyToNull(value: string | null | undefined): string | null {
  const trimmed = value?.trim() ?? "";
  return trimmed.length > 0 ? trimmed : null;
}

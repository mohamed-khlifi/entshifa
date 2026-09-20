import { testId } from '@/lib/test/test-id';

/** Convert RHF field `name` (camelCase / dotted) to kebab test-id segments. */
export function fieldNameSegments(name: string): string[] {
  return name
    .split(/[.[\]]+/)
    .filter(Boolean)
    .map((part) => {
      if (/^\d+$/.test(part)) {
        return `i${part}`;
      }
      return part
        .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
        .replace(/_/g, '-')
        .toLowerCase();
    });
}

export function fieldTestId(name: string): string {
  return testId('forms', 'field', ...fieldNameSegments(name));
}

export function fieldErrorTestId(name: string): string {
  return testId('forms', 'field-error', ...fieldNameSegments(name));
}

export function columnTestId(columnId: string): string {
  const segment = columnId
    .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
    .replace(/_/g, '-')
    .toLowerCase();
  return testId('data', 'table', 'col', segment);
}

export function tableRowTestId(rowId: string): string {
  const segment = rowId
    .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
    .replace(/_/g, '-')
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, '-');
  if (!/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(segment)) {
    return testId('data', 'table', 'row', `id-${segment.replace(/^-+/, '') || 'unknown'}`);
  }
  return testId('data', 'table', 'row', segment);
}

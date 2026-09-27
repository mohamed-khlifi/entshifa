export function insertAtSelection(
  value: string,
  start: number,
  end: number,
  token: string,
): { value: string; cursor: number } {
  const next = `${value.slice(0, start)}${token}${value.slice(end)}`;
  return { value: next, cursor: start + token.length };
}

export function placeholderToken(path: string): string {
  return `{{ ${path} }}`;
}

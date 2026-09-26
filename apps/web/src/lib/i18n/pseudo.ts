/**
 * Pseudo-locale (en-XA): accents plus ~40% extra length to catch truncation
 * and hardcoded UI strings in development.
 */

const ACCENT_MAP: Record<string, string> = {
  a: 'á',
  e: 'é',
  i: 'í',
  o: 'ó',
  u: 'ú',
  A: 'Á',
  E: 'É',
  I: 'Í',
  O: 'Ó',
  U: 'Ú',
  c: 'ç',
  C: 'Ç',
  n: 'ñ',
  N: 'Ñ',
};

function accentify(text: string): string {
  return text.replace(/[aeiouAEIOUcnCN]/g, (char) => ACCENT_MAP[char] ?? char);
}

function padToExtraLength(text: string, factor = 1.4): string {
  const target = Math.ceil(text.length * factor);
  if (text.length >= target) {
    return text;
  }
  const pad = '·'.repeat(target - text.length);
  return `${text}${pad}`;
}

/**
 * Transform a leaf message string. ICU placeholders (`{name}`) and simple
 * plural/select skeletons are left intact so next-intl can still format them.
 */
export function toPseudoLocaleString(value: string): string {
  const parts = value.split(/(\{[^}]+\})/g);
  return parts
    .map((part) => {
      if (part.startsWith('{') && part.endsWith('}')) {
        return part;
      }
      return padToExtraLength(accentify(part));
    })
    .join('');
}

export function toPseudoLocaleMessages<T>(value: T): T {
  if (typeof value === 'string') {
    return toPseudoLocaleString(value) as T;
  }
  if (Array.isArray(value)) {
    return value.map((item) => toPseudoLocaleMessages(item)) as T;
  }
  if (value !== null && typeof value === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, nested] of Object.entries(value)) {
      result[key] = toPseudoLocaleMessages(nested);
    }
    return result as T;
  }
  return value;
}

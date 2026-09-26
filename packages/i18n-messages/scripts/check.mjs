#!/usr/bin/env node
/**
 * Translation catalog check (architecture §22 / CI gate 8).
 *
 * Fails when:
 * 1. A key present in the default locale (en) is missing from another locale
 * 2. A locale has orphan keys absent from the default locale
 * 3. ICU / simple placeholder sets differ across locales for the same key
 * 4. A catalog key is never referenced from apps/web/src (orphan in source)
 *
 * Usage (from repo root): node packages/i18n-messages/scripts/check.mjs
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = path.resolve(__dirname, '..');
const REPO_ROOT = path.resolve(PACKAGE_ROOT, '../..');
const WEB_SRC = path.join(REPO_ROOT, 'apps/web/src');
const DEFAULT_LOCALE = 'en';
const LOCALES = ['en', 'fr', 'ar'];
const NAMESPACES = ['common', 'auth', 'errors', 'forms', 'data', 'uiKit', 'attachments'];

/**
 * Keys resolved only through typed maps or API error codes (never a literal
 * t('…') call). Still must exist in every catalog.
 */
const ALLOWLISTED_KEYS = new Set([
  'common.locale.options.en',
  'common.locale.options.fr',
  'common.locale.options.ar',
  'forms.laterality.left',
  'forms.laterality.right',
  'forms.laterality.bilateral',
  'forms.laterality.unspecified',
  'attachments.viewer.statusValues.pending',
  'attachments.viewer.statusValues.processing',
  'attachments.viewer.statusValues.ready',
  'attachments.viewer.statusValues.failed',
  'attachments.viewer.errors.unauthenticated',
  'attachments.viewer.errors.load_failed',
]);

/** Entire namespace looked up from API `code` via apiErrorCodeToMessageKey. */
const DYNAMIC_NAMESPACES = new Set(['errors']);

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function flatten(tree, prefix = '', out = new Map()) {
  if (tree === null || typeof tree !== 'object' || Array.isArray(tree)) {
    out.set(prefix, tree);
    return out;
  }
  for (const [key, value] of Object.entries(tree)) {
    if (key.includes('.')) {
      throw new Error(`Catalog key must not contain '.': ${prefix ? `${prefix}.` : ''}${key}`);
    }
    const next = prefix ? `${prefix}.${key}` : key;
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      flatten(value, next, out);
    } else {
      out.set(next, value);
    }
  }
  return out;
}

function extractPlaceholders(message) {
  if (typeof message !== 'string') {
    return new Set();
  }
  const found = new Set();
  for (const match of message.matchAll(/\{([A-Za-z_][A-Za-z0-9_]*)\b/g)) {
    found.add(match[1]);
  }
  return found;
}

function loadLocaleMaps(locale) {
  const maps = new Map();
  for (const namespace of NAMESPACES) {
    const filePath = path.join(PACKAGE_ROOT, locale, `${namespace}.json`);
    if (!fs.existsSync(filePath)) {
      throw new Error(`Missing catalog file: ${path.relative(REPO_ROOT, filePath)}`);
    }
    const flat = flatten(readJson(filePath));
    for (const [key, value] of flat) {
      maps.set(`${namespace}.${key}`, value);
    }
  }
  return maps;
}

function walkSourceFiles(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name === '.next') {
        continue;
      }
      walkSourceFiles(full, files);
    } else if (
      /\.(ts|tsx)$/.test(entry.name) &&
      !entry.name.endsWith('.test.ts') &&
      !entry.name.endsWith('.test.tsx')
    ) {
      files.push(full);
    }
  }
  return files;
}

/**
 * Collect referenced message keys from t('...') calls paired with
 * useTranslations / getTranslations (runtime or typed).
 */
function collectReferencedKeys(sourceRoot) {
  const referenced = new Set(ALLOWLISTED_KEYS);
  const files = walkSourceFiles(sourceRoot);

  for (const file of files) {
    const source = fs.readFileSync(file, 'utf8');
    const namespaceBindings = new Map();

    for (const match of source.matchAll(
      /\b(?:const|let)\s+(\w+)\s*=\s*(?:await\s+)?(?:useTranslations|getTranslations)\(\s*['"]([\w]+)['"]\s*\)/g,
    )) {
      namespaceBindings.set(match[1], match[2]);
    }

    // Typed translator factories: createLoginSchema(t: ReturnType<typeof useTranslations<'auth'>>)
    for (const match of source.matchAll(
      /useTranslations\s*<\s*['"]([\w]+)['"]\s*>/g,
    )) {
      namespaceBindings.set('t', match[1]);
    }

    for (const match of source.matchAll(
      /\b([A-Za-z_][\w]*)\(\s*(?:['"`])([\w.]+)(?:['"`])/g,
    )) {
      const fn = match[1];
      const key = match[2];
      const ns = namespaceBindings.get(fn);
      if (!ns) {
        continue;
      }
      referenced.add(`${ns}.${key}`);
    }
  }

  return referenced;
}

function setEqual(a, b) {
  if (a.size !== b.size) {
    return false;
  }
  for (const value of a) {
    if (!b.has(value)) {
      return false;
    }
  }
  return true;
}

function main() {
  const errors = [];
  const localeMaps = Object.fromEntries(LOCALES.map((locale) => [locale, loadLocaleMaps(locale)]));
  const defaultKeys = [...localeMaps[DEFAULT_LOCALE].keys()].sort();

  for (const locale of LOCALES) {
    if (locale === DEFAULT_LOCALE) {
      continue;
    }
    const map = localeMaps[locale];
    for (const key of defaultKeys) {
      if (!map.has(key)) {
        errors.push(`[missing] ${locale}: ${key}`);
      }
    }
    for (const key of map.keys()) {
      if (!localeMaps[DEFAULT_LOCALE].has(key)) {
        errors.push(`[extra] ${locale}: ${key} (not in ${DEFAULT_LOCALE})`);
      }
    }
  }

  for (const key of defaultKeys) {
    const expected = extractPlaceholders(localeMaps[DEFAULT_LOCALE].get(key));
    for (const locale of LOCALES) {
      if (locale === DEFAULT_LOCALE) {
        continue;
      }
      if (!localeMaps[locale].has(key)) {
        continue;
      }
      const actual = extractPlaceholders(localeMaps[locale].get(key));
      if (!setEqual(expected, actual)) {
        errors.push(
          `[placeholders] ${key}: ${DEFAULT_LOCALE}={${[...expected].join(',')}} ${locale}={${[...actual].join(',')}}`,
        );
      }
    }
  }

  const referenced = collectReferencedKeys(WEB_SRC);
  for (const key of defaultKeys) {
    const namespace = key.split('.')[0];
    if (DYNAMIC_NAMESPACES.has(namespace)) {
      continue;
    }
    if (!referenced.has(key)) {
      errors.push(`[orphan-source] ${key} is in catalogs but not referenced in apps/web/src`);
    }
  }

  if (errors.length > 0) {
    console.error(`Translation check failed (${errors.length} issue(s)):\n`);
    for (const line of errors) {
      console.error(`  ${line}`);
    }
    process.exit(1);
  }

  console.log(
    `Translation check passed: ${defaultKeys.length} keys × ${LOCALES.length} locales (${NAMESPACES.join(', ')}).`,
  );
}

main();

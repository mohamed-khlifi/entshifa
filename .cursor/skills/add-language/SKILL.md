---
name: add-language
description: Add support for a new locale across the UI, clinical terminology, documents and reports, including right-to-left languages. Use when adding Arabic, Spanish or any additional language.
---

# Add a language

Adding a language is a data task. If it requires code changes beyond
configuration and fonts, the implementation has a bug worth fixing first.

## Steps

### 1. Register the locale
`apps/web/src/lib/i18n/config.ts`: add the locale code, its display name, its
direction (`ltr` or `rtl`) and its font stack. Add it to the clinic's
`supported_locales` options.

### 2. UI catalogs
Create `messages/<locale>/` with every file that exists in the default locale.
Every key must be present; CI fails otherwise. Use ICU plurals with the correct
categories for the language (Arabic has six).

### 3. Clinical terminology
Add `concept_translation` rows for the new locale: `display`, `full_name`,
`abbreviation`, `patient_friendly` and search `synonyms`. This is the largest
part of the work and it is data, not code.

Use the translation coverage screen to prioritize by usage frequency rather
than translating alphabetically.

### 4. Narrative phrases
Add phrase templates per finding concept for the new locale, plus the
language's grammar rules in `engines/narrative/grammar.py` if it needs
agreement, dual forms or a different clause order. Do not translate generated
sentences at runtime; generate them natively.

### 5. Documents
Add a `document_template_version` row per template for the new locale, with
`direction` set correctly. Verify a real rendered PDF, not just the screen:
- Arabic shaping and bidirectional text render correctly
- table column order flips in RTL while numeric columns keep alignment
- the clinic header, footer and signature block are positioned correctly
- page breaks and long words do not break the layout

### 6. Questionnaires
An instrument is only offered in a locale once every item and option is
translated. Verify the guard blocks incomplete ones.

### 7. RTL layout check (RTL languages only)
- layout uses logical properties, so no mirrored stylesheet should be needed
- directional icons flip; anatomical icons do not
- charts, audiograms and anatomical maps must NOT mirror
- numbers, units and clinical codes stay left-to-right inside RTL text
- date and number formatting follows the locale

### 8. Tests
Run the Playwright suite in the new locale. Run the pseudo-locale pass to catch
truncation. Print one document of each category and read it.

## Checklist

- [ ] Locale registered with direction and fonts
- [ ] Every UI key present, ICU plurals correct for the language
- [ ] Concept translations added, coverage screen reviewed
- [ ] Narrative phrases and grammar rules in place
- [ ] Document templates verified as rendered PDFs, not just on screen
- [ ] Questionnaires either fully translated or blocked in this locale
- [ ] Maps, charts and audiograms do not mirror
- [ ] E2E suite passes in the new locale
- [ ] No code change was needed beyond config and fonts

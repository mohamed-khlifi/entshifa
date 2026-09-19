---
name: add-anatomical-map
description: Add a new clickable anatomical examination map (tympanic membrane, nasal cavity, larynx, oral cavity, neck levels, face) as data rather than code. Use when a new body region needs a structured examination interface.
---

# Add an anatomical map

Maps are data. Adding one means adding an SVG plus a region definition plus
terminology rows. It must not require new React code. If you find yourself
writing map-specific components, the map engine needs extending instead, and
that is a separate conversation.

## Steps

### 1. Prepare the SVG
`apps/web/public/anatomy/<map-id>.svg`

- Every clickable region is a path or group with a stable `id` matching the
  region code (`tm.pars-tensa.antero-superior`).
- No text labels baked into the SVG. Labels come from translations.
- `viewBox` set, no fixed width or height, no inline fill colors on regions
  (state colors are applied at runtime through CSS variables).
- Paired organs: one SVG, mirrored at render time for the other side only if
  the anatomy is genuinely symmetric. Otherwise two SVGs.

### 2. Seed the terminology
For each region, create or reuse:
- an anatomy `concept` (kind `anatomy`), placed in the anatomy hierarchy with
  `parent_id`
- `concept_translation` rows for every locale
- a `value_set` of the findings allowed at that region, with
  `value_set_member` rows
- a default-normal concept for the region

Terminology goes in the seed script, never hardcoded in the frontend.

### 3. Write the region definition
`apps/web/src/lib/anatomy/<map-id>.map.ts`

```ts
export const tympanicMembraneMap: AnatomicalMapDefinition = {
  id: "tympanic-membrane",
  paired: true,
  svg: "/anatomy/tympanic-membrane.svg",
  regions: [
    {
      id: "tm.pars-tensa.antero-superior",
      pathId: "tm-pars-tensa-as",
      labelKey: "examination.tm.regions.anteroSuperior",
      conceptCode: "ANAT-TM-PT-AS",
      valueSetCode: "tm.findings",
      defaultNormalCode: "FIND-TM-NORMAL",
    },
    // ...
  ],
};
```

Register it in the map registry. No other code changes.

### 4. Behaviour the engine already provides
Do not reimplement any of this per map:
- first click marks normal, second opens the finding picker
- a "not examined" state that produces no report sentence
- right/left toggle with a keyboard shortcut
- keyboard navigation between regions in anatomical order
- long press or context menu to attach a photo to a region
- live narrative preview
- annotated PNG export for reports

### 5. Narrative phrases
For each finding concept used by this map, add phrase templates per locale so
reports can be generated in any language:

    concept: tm.perforation.central
    en: "central perforation of the {{quadrants}} quadrant(s)"
    fr: "perforation centrale du/des quadrant(s) {{quadrants}}"

Respect the ordering rules: right before left, positives before negatives,
negatives grouped.

### 6. Tests
- component test: keyboard navigation reaches every region in order
- component test: clicking a region writes an observation with the correct
  concept, body site, laterality and map region code
- snapshot of the generated narrative in each locale

## Checklist

- [ ] No map-specific React component was created
- [ ] Every region has an anatomy concept and translations in every locale
- [ ] Every region declares a value set and a default normal
- [ ] Findings are written as `observation` rows, not as columns or JSON
- [ ] Bilateral findings produce two rows, one per side
- [ ] Narrative phrases exist for every finding in every locale
- [ ] The map does not mirror in RTL

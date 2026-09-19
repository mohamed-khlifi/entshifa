---
name: add-questionnaire-instrument
description: Add a patient-reported or clinician-rated instrument (SNOT-22, NOSE, THI, DHI, VHI, RSI, EAT-10, Epworth, STOP-BANG, OSA-18) as versioned data with scoring, translations and severity bands. Use when a new score must be collectible and trendable.
---

# Add a questionnaire instrument

Instruments are versioned data rows, never code. Adding one must not require a
deploy once the engine exists.

## Before starting

1. Check the licensing note. Several instruments are copyrighted and need
   permission for commercial use. Record the licence status on the instrument
   row. If it is unclear, flag it and do not ship the instrument.
2. Get the authoritative item list, response options, scoring rule and severity
   bands from `docs/clinical/feature-specification.txt` appendix A or from the
   cited publication. Never reconstruct items from memory.
3. Confirm whether the respondent is the patient, a parent or the clinician,
   and whether subscales exist.

## Steps

### 1. Seed the instrument

    instrument                 code, category, respondent, scoring_type,
                               min_score, max_score, mcid, licence note, reference
    instrument_version         version, effective_from, is_current, scoring_config
    instrument_item            position, code, subscale, is_reverse_scored, weight
    instrument_option          value, position
    instrument_translation     title, item texts and option texts, per locale

`scoring_config` holds subscale definitions, reverse-scored items and severity
bands. Scoring must be expressible as a sum or weighted sum. Anything with
branching logic needs a dedicated scorer in `engines/scoring/` and a decision
from a human first.

### 2. Scoring

Generic sum and weighted-sum instruments use `engines/scoring/sum_scorer.py`
and need no new Python. Only write a dedicated scorer when the rule genuinely
cannot be expressed in the config, and then follow the
`add-clinical-calculator` skill: pure function, version, reference, known-answer
tests including the minimum and maximum possible scores and each band boundary.

### 3. Translations

Every item and every option in every supported locale. A partially translated
instrument must not be offered in that locale: a mistranslated item invalidates
the score. Add a guard so an instrument without complete translations for a
locale is not selectable there.

### 4. Delivery

Wire it into:
- the waiting-room tablet flow
- the invitation flow (SMS, WhatsApp, email link) with a single-use, hashed,
  expiring token scoped to one instrument and one patient
- the consultation cockpit, so the score appears with its date and whether the
  patient or staff entered it
- the post-operative outcome schedule, if it measures a surgical outcome

### 5. Presentation

- total, subscales, severity band
- change from the previous administration, with the MCID shown when published
- trend graph over time with treatment events marked
- item-level view so the doctor can see which items drive the score

### 6. Tests

Known-answer tests for: all-minimum answers, all-maximum answers, each severity
band boundary, reverse-scored items, an incomplete response (must not silently
score as zero).

## Checklist

- [ ] Licence status recorded; unclear licences flagged, not shipped
- [ ] Items and options match the published instrument exactly
- [ ] Complete translations for every locale it is offered in
- [ ] Scoring covered by known-answer tests including boundaries
- [ ] Incomplete responses rejected rather than scored
- [ ] Trend, change-from-previous and MCID wired
- [ ] No instrument content hardcoded in the frontend

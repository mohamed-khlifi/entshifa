# Phase 5: scores and calculators

**Goal:** patients fill questionnaires before the visit and the score is waiting
for the doctor. Every formula in the app lives in one engine with one endpoint.
**Depends on:** phase 2. Can run in parallel with phases 3 and 4.
**Estimated:** 4 weeks.
**Modules:** questionnaires, calculators.

Reference: feature spec sections 11 and 12. Architecture section 25.10.

---

## - [ ] P5-01 Instrument model and scoring engine (backend)

`instrument`, `instrument_version`, `instrument_item`, `instrument_option`,
`instrument_translation`, plus the generic sum and weighted-sum scorer.

Instruments are data. Adding one after this ticket must not require a deploy.

---

## - [ ] P5-02 Seed the launch instruments

SNOT-22, NOSE, THI, DHI, VHI-10, RSI, EAT-10, Epworth, STOP-BANG, OSA-18.
Use the `add-questionnaire-instrument` skill for each.

**Check the licence for every instrument before seeding it. Several are
copyrighted and need permission for commercial use. Flag anything unclear and
do not ship it.** Take items, options, ranges and severity bands from feature
spec appendix A or the publication, never from memory.

---

## - [ ] P5-03 Patient-facing questionnaire flow (backend and frontend)

Single-use hashed expiring tokens, a public route with no auth and no patient
data beyond a first name, tablet mode for the waiting room, SMS, WhatsApp and
email invitations in the patient's language, rate limiting on the public
endpoint.

---

## - [ ] P5-04 Score presentation (frontend)

Total, subscales, severity band, change from previous with the MCID where
published, trend graph with treatment events marked, item-level view.

---

## - [ ] P5-05 Calculator registry and endpoint (backend and frontend)

One registry, one generic endpoint pair, one frontend page that renders any
calculator from its metadata. Move the phase 3 and 4 engines into it.

---

## - [ ] P5-06 Remaining calculators

Pediatric dosing (already built in phase 2, register it here), BMI, BSA,
corrected age, surgical decision checklists (Paradise criteria, tube criteria,
adenotonsillectomy, cochlear implant candidacy), Lund-Mackay CT entry,
Myer-Cotton, endotracheal tube size by age.

Same rule as always: nothing invented, every formula cited, every one tested
against its reference case.

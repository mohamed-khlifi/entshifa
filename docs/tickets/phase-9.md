# Phase 9: analytics and AI

**Goal:** the structured data collected over the previous phases becomes
outcome measurement and a small amount of typing assistance.
**Depends on:** everything.
**Estimated:** open-ended.
**Modules:** analytics, ai.

Reference: feature spec sections 17 and 18.

Do not start this phase early. Both modules are only as good as the data model
beneath them, and building either before the clinical phases are solid produces
impressive demos and useless software.

---

## - [ ] P9-01 Today dashboard

Today's list with questionnaire status and recall reasons, drafts to sign,
results to review, surgical waiting list gaps, overdue recalls by type.

---

## - [ ] P9-02 Practice analytics

Volumes by complaint, diagnosis, procedure and age group. Referral sources.
Documentation quality metrics.

All built from the structured data already collected. **If a metric needs new
data entry, it is not worth the metric.**

---

## - [ ] P9-03 Outcome analytics

Mean change in SNOT-22 after FESS, NOSE after septoplasty, VHI after
phonosurgery, THI after tinnitus management, Epworth or AHI after sleep
surgery, air-bone gap closure after ear surgery, BPPV resolution after one
maneuver, tube complication rates, complication rates per procedure.

Private to each doctor by default; clinic-wide only for the admin.

---

## - [ ] P9-04 Research export and cohort builder

Anonymized export with identifiers removed and dates shifted per patient,
admin-approved and logged. Cohort builder over the structured data.

---

## - [ ] P9-05 AI assistant, five functions only

1. Free text to proposed structured fields, each accepted individually.
2. Report conclusion and referral letter drafting from structured findings.
3. Patient-friendly explanation in the patient's language.
4. Transcription of a scanned external audiogram or sleep study into fields,
   verified field by field.
5. Pre-visit three-line summary from the timeline and recalls.

**Hard constraints:**
- Nothing is written into the record without a human accepting it.
- Everything is visibly labelled as a draft.
- Identifiers are stripped before anything leaves the process.
- The clinic can disable AI entirely.
- Every request and response is logged with whether the suggestion was
  accepted, so usefulness and cost are measurable.

**Explicitly out of scope, permanently:** diagnosis suggestion, treatment
recommendation, image interpretation, triage, or anything a doctor could read
as a clinical opinion from the software.

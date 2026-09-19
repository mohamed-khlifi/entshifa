# Phase 8: sub-specialty modules

**Goal:** the sub-specialty work an ENT doctor does weekly, which generic
software never supports.
**Depends on:** phases 3, 4, 5 and 7.
**Estimated:** 8 weeks.
**Modules:** sleep, allergy, headneck, pediatrics, voice_swallowing.

Reference: feature spec section 10. Architecture section 25.14.

Each module attaches to a consultation when the matching complaint or diagnosis
is selected. None of them is a separate application.

---

## - [ ] P8-01 Sleep and snoring

Adult assessment fields, sleep study result entry with AHI severity banding,
DISE using the VOTE classification with video clips, treatment tracking
including CPAP adherence values, pediatric OSA-18 pathway with growth
percentiles.

---

## - [ ] P8-02 Allergy

Skin prick test panel entry with wheal sizes and both controls, specific IgE
results, ARIA classification, immunotherapy plan with per-dose records and
reaction grading, next-dose recalls, environmental control handouts selected by
positive allergens.

**The allergen panel is regional and configurable, never hardcoded.**

---

## - [ ] P8-03 Head and neck

Neck mass records linked to the neck map, ultrasound findings with TI-RADS,
FNA with Bethesda, tumor records with staging.

**TNM staging must record the AJCC edition explicitly and derive the stage
group from the site-specific tables. Do not let anything generate a stage from
memory. Every table needs a cited source and known-answer tests.**

Tumor board sheet in one click, treatment records, surveillance schedules with
the visit checklist, functional outcomes, thyroid nodule follow-up by TI-RADS
category and size, mandatory pre- and post-thyroidectomy vocal fold checks.

---

## - [ ] P8-04 Pediatric ENT

Growth charts on WHO curves, recurrent AOM episode log feeding the tube
criteria, adenotonsillar disease with the tonsillitis episode log feeding
Paradise criteria, ventilation tube registry, speech and language milestones,
congenital anomaly records, parent handouts in the family's language.

**Button battery ingestion is an emergency alert, not a routine finding.**

---

## - [ ] P8-05 Voice and swallowing

VHI with trend, GRBAS, maximum phonation time, voice recordings playable next
to the previous one, acoustic analysis value entry, RSI and RFS with their
cut-offs, EAT-10, FEES results, diet recommendation level, pre- and
post-treatment comparison.

---

## - [ ] P8-06 Smaller modules

Tinnitus (THI, pitch and loudness matching, management tracking, pulsatile red
flag), facial nerve (House-Brackmann and Sunnybrook trends, eye protection
checklist, electrodiagnostics, recovery tracking), epistaxis (episode log, risk
factors, localization, prevention handout).

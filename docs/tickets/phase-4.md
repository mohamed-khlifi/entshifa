# Phase 4: audiology

**Goal:** a technician enters hearing test data and the doctor reads a finished
dashboard with comparisons and flags. No more scanned audiograms.
**Depends on:** phase 2. Can run in parallel with phase 3.
**Estimated:** 6 weeks.
**Module:** audiology.

Reference: feature spec section 8. Architecture section 25.8.

This is one module but it is large. Expect to split most tickets further once
you start.

---

## - [ ] P4-01 Audiogram data model and entry API (backend)

`audiogram` plus the narrow `audiogram_threshold` table. Air and bone
conduction, masked flags, no-response flags, extended high frequencies
optional. Transducer, method, reliability, equipment and calibration recorded.

**Key constraint:** thresholds are numbers in their own rows, never a blob and
never an image. Everything else in this phase depends on that.

---

## - [ ] P4-02 Audiology calculation engines (backend)

Use the `add-clinical-calculator` skill for each: pure tone average with the
formula variants, air-bone gap, interaural difference, WHO 2021 grading, loss
type, configuration description, impairment percentage, asymmetry criterion,
significant threshold shift against a chosen baseline, speech and pure tone
agreement check.

**Take every formula, band boundary and criterion from feature spec appendix A
or the cited publication. Do not reconstruct any of them from memory.** Each
needs known-answer tests including every band boundary.

The clinic chooses the PTA formula, the asymmetry rule and the shift rule as
settings. Every stored result records which one was used.

---

## - [ ] P4-03 Speech, tympanometry, reflexes, OAE, ABR (backend)

The remaining test types from feature spec 8.2 to 8.4. Tympanogram type is
suggested by the engine and overridable by the doctor, with the override
recorded.

---

## - [ ] P4-04 Audiogram chart and entry grid (frontend)

Two-way binding between a keyboard-navigable numeric grid and the plotted
chart. Standard audiometric symbols and colors. Overlay of previous audiograms.
Print stylesheet producing the standard form.

**Conventions are fixed, not configurable:** dB HL descending on Y, log
frequency on X, red circles right, blue crosses left, brackets for bone,
arrows for no response. The chart never mirrors in RTL.

---

## - [ ] P4-05 Audiology dashboard and comparison (frontend)

The layout in feature spec 8.6: both ears side by side, PTA and grade large,
alerts row, history strip with overlay, threshold evolution per frequency.

---

## - [ ] P4-06 Hearing devices and pediatric audiology (backend and frontend)

`hearing_device` tracking, candidacy checklists, newborn screening chain with
the 1-3-6 targets, behavioral test methods, OME tracking with the 3-month
watchful waiting recall.

---

## - [ ] P4-07 Audiology report and technician role

The audiology report template with the plotted audiogram. The technician role
enters data but does not see consultation notes beyond what the task needs.

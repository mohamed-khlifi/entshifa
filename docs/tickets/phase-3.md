# Phase 3: office procedures

**Goal:** the doctor performs an endoscopy, laryngoscopy or ear procedure and
signs the report before the patient leaves the room.
**Depends on:** phase 2 complete.
**Estimated:** 6 weeks.
**Modules:** endoscopy, laryngoscopy, otology.

Reference: feature spec section 7. Architecture section 25.7.

---

## - [ ] P3-01 Procedure record core (backend)

**Scope**
- `procedure_record` as the parent of every procedure, with the shared fields:
  indication, anesthesia, instrument, tolerance, laterality, complications,
  draft and signed status.
- The `ProcedurePerformed` domain event.

**Acceptance**
- Every procedure type reuses this parent instead of repeating the fields.
- Signing locks the record; corrections are addenda.

---

## - [ ] P3-02 Nasal endoscopy (backend)

**Scope**
- `endoscopy_exam` plus structure-level findings written as observations.
- Structures in scope order per side: vestibule and valve, septum, inferior
  turbinate and meatus, middle turbinate and meatus, uncinate, bulla, superior
  turbinate and meatus, sphenoethmoidal recess, olfactory cleft, nasopharynx,
  post-FESS cavity.
- Scoring engines: Lund-Kennedy (0 to 20), modified Lund-Kennedy (0 to 12),
  polyp grade with the clinic's chosen scale, adenoid obstruction percentage.
  Use the `add-clinical-calculator` skill; take the item definitions from
  feature spec appendix A. Do not reconstruct them from memory.

**Acceptance**
- Scores recompute deterministically from the stored observations.
- Known-answer tests cover the minimum, maximum and each item.
- The polyp scale is a clinic setting, and the printed report names which scale
  was used.

---

## - [ ] P3-03 Nasal endoscopy builder (frontend)

**Scope**
- Nasal endoscopy map extending P2-04 with the full endoscopic structure list.
- Image capture or upload attached to a structure, with annotation.
- Side-by-side comparison with the previous endoscopy, structure by structure,
  with changed items highlighted and the score trend.
- Special templates: post-FESS cavity check, epistaxis localization.

**Acceptance**
- A normal endoscopy is documented and signed in under two minutes.
- Comparison shows the previous and current value per structure without the
  doctor hunting through old reports.

---

## - [ ] P3-04 Laryngoscopy and stroboscopy (backend)

**Scope**
- `laryngoscopy_exam` with the vocal fold fields: mobility and position per
  side, glottic closure pattern, supraglottic activity, lesions placed on a
  fold diagram by third and surface.
- Stroboscopy fields: symmetry, periodicity, amplitude, mucosal wave, phase
  closure, non-vibrating segment.
- Scores: Reflux Finding Score, GRBAS, Penetration-Aspiration Scale for FEES.

**Acceptance**
- Vocal fold mobility is a structured value per side, never prose.
- FEES fields record consistencies tested and residue location.

---

## - [ ] P3-05 Laryngoscopy builder and video (frontend)

**Scope**
- Larynx map with the vocal fold diagram.
- Video clip capture, attachment and playback next to the previous study.
- Templates: pre- and post-thyroidectomy check, paralysis workup, FEES,
  pediatric airway, tracheostomy check.

**Acceptance**
- A pre-thyroidectomy vocal fold check is a one-click template.
- Video plays inline without download.

---

## - [ ] P3-06 Otology procedures and device tracking (backend and frontend)

**Scope**
- `otology_exam` at microscopy detail, plus tuning fork results.
- Office ear procedures: wax removal, foreign body, otitis externa toilet with
  wick, myringotomy and tube insertion, tube removal, intratympanic injection,
  cavity cleaning.
- `ear_device` registry for tubes and cavities, with status and next check due.

**Acceptance**
- Inserting a tube creates the device record and its follow-up schedule.
- The patient card shows any ear with a tube, a cavity or a cholesteatoma.

---

## - [ ] P3-07 Short office procedure forms (backend and frontend)

**Scope**
Structured short forms for: epistaxis management, fine needle aspiration,
oral or pharyngeal biopsy, botulinum injection, peritonsillar abscess drainage,
nasal fracture reduction, sialendoscopy. Each produces a report and, where
relevant, a removal or result-review date.

**Acceptance**
- Each form fits on one screen and is signed in under a minute.
- A pack, wick or splint records its planned removal date.

---

## - [ ] P3-08 Recall protocols from procedures (backend)

**Scope**
- `protocol` and `protocol_rule` models, and the protocol resolver listening to
  `ProcedurePerformed`.
- Seed protocols for the procedures in this phase: pack removal 48 to 72 hours,
  wick 48 to 72 hours, splints 5 to 7 days, tube check at 3 to 4 weeks then
  every 6 months, cavity cleaning every 6 to 12 months, specimen result review
  at 7 to 10 days.
- Use the `add-recall-protocol` skill. Intervals from feature spec appendix C.

**Acceptance**
- Every interval is editable data, never a constant in code.
- Completing the expected event closes the recall automatically.
- Repeating series have explicit stop conditions.

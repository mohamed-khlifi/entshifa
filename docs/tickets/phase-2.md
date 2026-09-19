# Phase 2: the consultation

**Goal:** a doctor completes a full visit in the app: complaint, history,
examination, diagnosis, plan, prescription, report, follow-up. After this phase
the product is usable in a real clinic.
**Depends on:** phase 1 complete.
**Estimated:** 8 weeks.
**Modules:** encounters, observations, examination, diagnoses, prescriptions,
documents (full), recalls (manual).

Reference: feature spec sections 5, 6, 14 and 15. Architecture sections 25.5,
25.6, 25.11, 25.12, 25.15 and 26.

---

## - [ ] P2-01 Observation engine (backend)

The most consequential ticket in the project. Read architecture section 26
before writing anything.

**Scope**
- Models: `observation`, `observation_component`, `examination_snapshot`.
- Typed values: code, numeric, boolean, text, range, ordinal, each with its own
  column, plus unit, qualifiers JSON, laterality, body site, map region code.
- Provenance on every row: source, recorded by, confirmed by, effective at.
- Repository: write a set of observations for an encounter, read by encounter,
  read by patient and concept over time, diff two encounters by body site.

**Acceptance**
- A bilateral finding on a paired structure creates two rows, one per side.
- Comparing two visits is one grouped query, not application-side looping.
- A cohort query ("patients with polyp grade 3 in 2026") uses an index.
- No finding is stored as free text or as a JSON blob.

---

## - [ ] P2-02 Encounters (backend)

**Scope**
- Models: `encounter`, `encounter_complaint`, `encounter_addendum`,
  `encounter_signature`, `encounter_template`.
- Draft, sign, amend lifecycle. Signing hashes the canonical content.
- Copy forward from the previous encounter with provenance marking.
- PATCH endpoint supporting autosave of a dirty subset with version checking.

**Acceptance**
- A signed encounter cannot be mutated by any code path. Test it at the
  repository level, not only the API.
- A correction after signing creates an addendum with its own author and time.
- A concurrent edit returns 409 with both versions, never a silent overwrite.

---

## - [ ] P2-03 Visit templates and chief complaint routing (backend)

**Scope**
- `encounter_template` with `trigger_concept_ids` and a config holding history
  fields, exam sections, suggested instruments, suggested tests, suggested
  documents, favourite diagnoses, default follow-up interval.
- Seed templates for the ten most common complaints, using the mapping in
  feature spec appendix B.
- Clinic-level and doctor-level overrides of any template.

**Acceptance**
- Selecting "nasal obstruction" returns a different field set than "vertigo",
  driven entirely by data.
- A doctor editing their template does not affect colleagues.

---

## - [ ] P2-04 Anatomical maps: ear, nose, oral cavity, neck (frontend + seed)

**Scope**
Use the `add-anatomical-map` skill for each. Four maps in this ticket:
- tympanic membrane with quadrants, pars flaccida, canal
- nasal cavity, coronal, right and left
- oral cavity and oropharynx, including tonsil grading
- neck with lymph node levels, thyroid, salivary glands

Each needs: SVG with stable region ids, anatomy concepts and translations,
value sets per region, default normals, narrative phrase templates in en and
fr.

**Acceptance**
- No map-specific React component was written; all four use the same engine.
- Keyboard navigation reaches every region in anatomical order.
- Clicking a region writes an observation with the right concept, body site,
  side and region code.
- The generated narrative reads correctly in en and fr, right before left,
  positives before negatives.

---

## - [ ] P2-05 One-click normals and copy forward (frontend)

**Scope**
- "Normal ENT examination" filling every section, and per-region normals.
- "Copy from last visit" pre-filling history, exam and problem list, with
  copied values shown in a distinct style until confirmed or changed.

**Acceptance**
- Marking a full normal exam takes one click and produces correct negative
  findings text.
- A copied value that the doctor never touches is still marked as copied in the
  data, so audits can tell.

---

## - [ ] P2-06 Consultation cockpit (frontend)

**Scope**
- Three-column layout: patient card, consultation sections, live report
  preview.
- Complaint selector grid, grouped by region, with search and multi-select.
- Structured history blocks that change with the complaint.
- Examination sections using the P2-04 maps.
- Assessment and plan with coded diagnoses and structured plan items.
- Bottom bar: autosave status, normals, sign, print, copy forward.
- Red flag capture and display.

**Acceptance**
- A routine visit is completed in under 10 minutes by a doctor who has seen the
  screen once.
- The report preview updates as fields are filled.
- A browser crash mid-visit loses nothing.
- Every element is keyboard reachable.

---

## - [ ] P2-07 Diagnoses and problem list (backend and frontend)

**Scope**
- `diagnosis` and `problem_list_entry` models. ICD-10 concepts seeded for the
  ENT chapters plus room for a local code system in parallel.
- Side, status (suspected, confirmed, ruled out), promotion to the problem
  list.
- Favourites per doctor and per complaint.

**Acceptance**
- A diagnosis is always a concept id, never typed text.
- The problem list shows active and resolved separately, with dates.

---

## - [ ] P2-08 Prescriptions (backend)

**Scope**
- Models: `drug`, `drug_form`, `formulary_entry`, `prescription`,
  `prescription_item`, `prescription_template`.
- Weight-based pediatric dosing through an engine (use the
  `add-clinical-calculator` skill). Output includes mg per dose, mL per dose for
  the available syrup concentration, doses per day and the mg/kg/day rule used.
- Safety checks: allergy block with override reason, ototoxic warning when
  hearing loss is on the problem list, duplicate class, dose above maximum for
  weight or age, pregnancy and breastfeeding.
- Steroid taper schedules generated day by day.

**Acceptance**
- Prescribing a known allergen is blocked, and an override records who and why.
- A pediatric prescription without a recorded weight is blocked.
- Every dosing rule comes from `formulary_entry`, editable by the clinic, never
  from code.
- Dosing has known-answer tests.

---

## - [ ] P2-09 Prescriptions (frontend)

**Scope**
- Drug search with clinic formulary first and complaint-specific favourites on
  top.
- Prescription builder with the ENT helpers: saline irrigation protocol, spray
  technique note, ear drop technique, taper builder.
- Template prescriptions the doctor saves and reuses.
- Print in the clinic's legal format, in the patient's language.

**Acceptance**
- Safety blocks appear before the doctor finishes, not on submit.
- A saved template applies in one click and stays editable.

---

## - [ ] P2-10 Clinical documents (backend and frontend)

**Scope**
Templates for: consultation report, referral reply letter, sick leave, medical
certificate, imaging request, lab request. Use the `add-document-template`
skill for each.
- Imaging request carries the ENT modality list, the auto-written clinical
  question, and the contrast, renal, pregnancy, pacemaker and implant flags.
- Referral reply is generated in the referring doctor's locale.
- Batch print of the whole visit in one action.

**Acceptance**
- A visit's documents print as one batch in mixed languages correctly.
- The imaging request blocks an MRI request for a patient flagged with a
  non-MRI-safe implant, with an override path.

---

## - [ ] P2-11 Manual recalls and the patient timeline (backend and frontend)

**Scope**
- `recall` and `recall_action` models, manual creation from the plan.
- Assistant work list: overdue and upcoming, call, SMS, book, mark unreachable
  with attempt count.
- Patient timeline: virtualized, filterable by type and by problem, click to
  open, printable as a one-page history.

**Acceptance**
- "See in 6 weeks with an audiogram" creates both the recall and, optionally,
  the appointment.
- The timeline loads 10 years of history without a visible delay.
- Protocol-driven automatic recalls are out of scope here; they arrive in phase
  3 onward.

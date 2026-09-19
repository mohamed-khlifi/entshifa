# Phase 7: surgery

**Goal:** from "we should operate" to a signed operative note and an automatic
post-operative pathway, without leaving the app.
**Depends on:** phase 2, phase 5 (outcome questionnaires).
**Estimated:** 8 weeks.
**Module:** surgery.

Reference: feature spec section 13. Architecture section 25.13.

---

## - [ ] P7-01 Surgery proposal and the surgery bundle

`surgery_case` created from the consultation plan. One click generates the
bundle: information sheet, consent with the procedure-specific risk list, quote,
pre-anesthesia request, pre-operative test requests, pre-operative instructions
including which medications to stop and when.

Risk lists are an editable library per procedure, in every patient language.

---

## - [ ] P7-02 Waiting list and pre-operative checklist

Per surgeon, with days waiting and priority. Checklist items with blocking
flags: consent signed, anesthesia consult, labs, imaging, **pre-operative vocal
fold check before thyroid and laryngeal surgery**, **hearing test before ear
surgery**, anticoagulant plan, implants and pacemaker noted, insurance
approval, quote accepted.

Blocking items appear in red on the operating day list.

---

## - [ ] P7-03 Operating day list

Procedure, side shown large and unmissable and matching the consent, allergies,
anticoagulants, airway alerts, checklist status, team, room, order. Optional WHO
surgical safety checklist fields.

---

## - [ ] P7-04 Operative note templates

One template per procedure family with structured fields, so a tonsillectomy
note takes 90 seconds. Shared fields plus procedure-specific structured fields.

Start with the fifteen commonest procedures from feature spec 13.4. Implant and
graft entries record lot numbers for traceability, so a recalled batch can be
traced to every patient in seconds.

---

## - [ ] P7-05 Specimens and pathology

Specimen records with site, laboratory, expected date, result entry, and a
result-review recall. A "result explained to patient" tick with its date.

---

## - [ ] P7-06 Post-operative pathways

Default plans per procedure from feature spec appendix C, creating appointments
and recalls automatically. Use the `add-recall-protocol` skill.

Post-op visit template capturing pain, bleeding, fever, intake, wound or cavity
check, packing or splint removal, structured complications, return to work date.

---

## - [ ] P7-07 Outcome measurement

The questionnaire that justified the surgery is re-sent automatically at 3, 6
and 12 months. Ear surgery compares audiograms against the pre-operative
baseline. These feed the dashboard in phase 9.

---

## - [ ] P7-08 Surgeon logbook

Every procedure with role, complexity, complications and outcome. Filters and
export for training or accreditation. Complication rate per procedure over
time, private to the surgeon.

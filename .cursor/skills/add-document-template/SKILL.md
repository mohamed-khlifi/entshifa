---
name: add-document-template
description: Add a printable document template (consultation report, procedure report, prescription, certificate, imaging request, referral letter, consent, patient handout) with typed placeholders and per-locale versions. Use when the app must produce a new printed or PDF output.
---

# Add a document template

Everything the doctor prints comes from a versioned template row rendered from
structured data. Nothing is assembled by string concatenation in Python or
React.

## Steps

### 1. Declare the template
`document_template`: code, category, the typed `placeholders` map. Placeholders
are declared and validated at save time, so a template cannot reference a field
that does not exist.

Categories in use: consultation_report, endoscopy_report, laryngoscopy_report,
audiology_report, vestibular_report, operative_note, prescription, certificate,
imaging_request, lab_request, referral_letter, handout, consent, quote,
tumor_board.

### 2. Write the body per locale
`document_template_version`: header, body, footer, CSS, page setup and
`direction`, one row per locale. The body uses only declared placeholders.

Content rules for clinical reports:
- right before left, consistently
- positive findings before negatives; negatives grouped
- scores always with their scale name and range (`SNOT-22: 58/110`)
- every calculated value shows the formula or scale used (`PTA4`, `WHO 2021`)
- the conclusion is the doctor's own text, never generated silently
- the plan is numbered
- units are never translated

### 3. Data snapshot
When a document is finalized, store `content_snapshot` with the exact data used
to render it, plus the template version id and a content hash. A report printed
today must reproduce identically in five years, after templates have changed.

### 4. Rendering
HTML and CSS to PDF on the server, in the worker. Never render a clinical PDF in
the browser. Verify the output for every locale, including RTL, as a real PDF.

### 5. Wire it up
- attach it to the relevant plan item or procedure so it is offered
  automatically
- add it to the end-of-visit batch print
- add recipients where relevant (patient, referring doctor, insurer) with the
  recipient's own locale, which may differ from the clinic's
- respect the patient's `preferred_document_locale`

### 6. Tests
- render each locale with a full fixture and with a minimal fixture
- a snapshot test on the rendered HTML
- assert the finalized document is immutable and the hash matches

## Checklist

- [ ] Placeholders declared and typed; none undeclared in the body
- [ ] A version row exists for every supported locale, with correct direction
- [ ] RTL output verified as a rendered PDF
- [ ] Content snapshot and hash stored on finalization
- [ ] Finalized documents are immutable
- [ ] No string assembly of clinical text outside the narrative engine
- [ ] Patient, referrer and clinic locales handled independently

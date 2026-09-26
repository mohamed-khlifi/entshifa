# Phase 1: foundation

**Goal:** a clinic can register patients, book them, and the system knows who
may see what. No clinical content yet.
**Depends on:** phase 0 complete.
**Estimated:** 6 weeks.
**Modules:** auth, users, clinics, terminology (extended), patients,
scheduling, attachments, documents (base), admin.

Reference for every ticket: `docs/architecture/architecture-and-structure.txt`
section 25 for schema, `docs/clinical/feature-specification.txt` section 4 for
clinical requirements.

---

## - [ ] P1-01 Clinics and sites (backend)

**Scope**
- `features/clinics/`: models `clinic`, `site`.
- Fields per architecture 25.1, including `default_locale`,
  `supported_locales`, `timezone`, `country_code`, `currency`, `settings` JSON.
- CRUD endpoints, admin permission only.
- Clinic-level clinical settings in `setting`: PTA formula, asymmetry rule,
  polyp scale, tube recall interval, follow-up defaults.

**Acceptance**
- A clinic setting resolves user → clinic → system default, in that order.
- No clinical default is hardcoded anywhere in Python.

---

## - [ ] P1-02 Users, roles and permissions (backend)

**Scope**
- `features/users/`: `user`, `user_clinic_role`, invitation flow, password
  reset, optional TOTP.
- Seed the five roles: clinic admin, doctor, assistant, audiology technician,
  read-only, with the permission matrix from architecture 29.
- A user may belong to more than one clinic and switch between them.

**Acceptance**
- A permission change takes effect on the next request, without a redeploy.
- A clinic admin can create a custom role from seeded permissions.
- Switching the active clinic changes every subsequent query's scope.

---

## - [ ] P1-03 Users and clinic admin UI (frontend)

**Scope**
- Login, password reset, TOTP enrolment screens.
- User list and invite, role assignment, clinic switcher in the topbar.
- Clinic profile and settings screens, including logo upload and document
  header and footer text.

**Acceptance**
- Actions the user lacks permission for are not rendered, and the server
  rejects them anyway if called.
- The clinic switcher is visible only to users in more than one clinic.

---

## - [ ] P1-04 Terminology admin (backend and frontend)

**Scope**
- Extend the P0-08 module: concept CRUD for clinic-owned concepts, translation
  editing, value set membership editing.
- Translation coverage screen: untranslated concepts per locale, sorted by
  usage frequency.

**Acceptance**
- A clinic can rename a term locally without affecting other clinics.
- A concept that is in use cannot be deleted, only deactivated.

---

## - [ ] P1-05 Patients (backend) — the reference implementation

This is the module every later feature copies. Build it carefully and review it
line by line.

**Scope**
- Models per architecture 25.3: `patient`, `patient_identifier`,
  `patient_contact`, `patient_allergy`, `patient_medication`, `patient_flag`,
  `patient_problem`, `patient_history`, `patient_merge_log`.
- Key patient fields: MRN per clinic, name plus alternate-script name,
  `name_normalized` for search, birth date with estimated flag, sex,
  `preferred_locale`, contacts, insurance, referring doctor with their own
  locale, guardian for minors, consent flags, smoking and alcohol, occupation
  and noise exposure.
- Search: accent-insensitive and case-insensitive, Latin and Arabic script,
  by name, phone, MRN and birth date.
- Duplicate detection on create: same name plus birth date, or same phone.
- Merge patients, admin only, fully audited.
- The ENT safety flags from feature spec 4.5 as structured `patient_flag` rows,
  not free text.

**Acceptance**
- Cross-tenant isolation test passes for every endpoint.
- Searching "Ben Ali" finds "Bén Alï" and the Arabic-script equivalent.
- Creating a likely duplicate prompts instead of silently creating one.
- A merge preserves every clinical record and writes a merge log row.
- `only_hearing_ear` and the other flags are queryable, dated and sourced.

---

## - [ ] P1-06 Patients (frontend) — the reference implementation

**Scope**
- Patient list with search, filters and pagination, using `DataTable`.
- Patient create and edit form with the full field set and validation.
- Patient detail shell: header card with alerts, age (months under 3 years),
  allergies, active problems, current medications, last visits.
- Alert banner rendering the safety flags prominently.

**Acceptance**
- The header card is a single component reused on every patient sub-page.
- The `only_hearing_ear` alert is visually unmissable.
- The form autosaves drafts and warns on navigation with unsaved changes.
- Every string is a translation key; the screen is correct in `en`, `fr`, and `ar`.

---

## - [ ] P1-07 Scheduling (backend and frontend)

**Scope**
- `appointment_type` with default durations, `appointment`, waiting room list.
- Day and week views per doctor and per room.
- Status flow: scheduled → arrived → in room → completed, plus no-show and
  cancelled with a reason.
- Waiting room shows arrival time and questionnaire status (the questionnaire
  field exists now, is populated in phase 5).

**Acceptance**
- Double-booking a doctor warns but does not block, since clinics overbook
  deliberately.
- Times are stored UTC and displayed in the clinic timezone.
- No online booking, no recurring rules. Out of scope by design.

---

## - [ ] P1-08 Attachments (frontend)

**Scope**
- Upload component using the P0-13 pre-signed flow, with progress and retry.
- Gallery and viewer with tags: category, date, body site, side.
- External document upload: scanned reports, letters, external audiograms.

**Acceptance**
- A 200 MB endoscopy video uploads without touching the API process.
- Images render as thumbnails in lists and full size in the viewer.
- Consent-for-teaching flag is captured at upload.

---

## - [ ] P1-09 Document engine base (backend)

**Scope**
- Models: `document_template`, `document_template_version`, `document`,
  `document_recipient`, `phrase_library`.
- HTML and CSS to PDF rendering in the worker.
- Typed, validated placeholders. Content snapshot and hash on finalization.
- One real template implemented end to end: a simple patient summary, in en,
  fr and ar.

**Acceptance**
- The Arabic PDF renders with correct shaping, bidirectional text and RTL table
  column order. Verify as a printed PDF, not on screen.
- A finalized document is immutable and reproduces identically after the
  template changes.
- A template referencing an undeclared placeholder is rejected at save time.

**This ticket proves RTL works. Do not defer it.**

---

## - [ ] P1-10 Documents UI and template admin (frontend)

**Scope**
- Template editor with live preview per locale, placeholder picker.
- Document list per patient, preview, print, download.
- Clinic header, footer and signature configuration.

**Acceptance**
- A clinic admin can change the letterhead without a developer.
- Preview matches the rendered PDF.

---

## - [ ] P1-11 Phase 1 hardening

**Scope**
- Cross-tenant isolation test generated over every endpoint registered so far.
- Audit coverage check: every clinical write and read produces a log row.
- Seed scripts split into `seed_system`, `seed_demo`, `seed_test`.
- `make anonymize` producing a safe development dump.
- Backup and restore runbook written and a restore actually performed once.

**Acceptance**
- The restore drill is documented with the date it was performed.
- A new developer can go from clone to a working seeded app in under 30
  minutes using only the README.

---
name: add-recall-protocol
description: Add a follow-up protocol that automatically creates recalls from a procedure, diagnosis, finding or surgery (tube checks, pack removal, cancer surveillance, immunotherapy doses, post-op outcome questionnaires). Use when a clinical event should schedule future actions.
---

# Add a recall protocol

The recall engine is what stops patients being forgotten. Protocols are data:
adding one must not require code.

## Before starting

Get the intervals from `docs/clinical/feature-specification.txt` (appendix C
lists default post-operative plans per procedure). Never invent a surveillance
interval. If the clinical source is unclear, ask, and mark it `# VERIFY:`.

All intervals are editable defaults, never hardcoded constants.

## Steps

### 1. Define the protocol

    protocol        code, name_key, trigger_type, trigger_concept_ids, version
    protocol_rule   sequence, offset_days, window_days, action_type,
                    action_config, condition, label_key

`trigger_type` is one of `procedure`, `diagnosis`, `finding`, `surgery`,
`manual`. `action_type` is one of `visit`, `test`, `call`, `questionnaire`,
`document`.

Example, ventilation tube insertion:

    rule 1  offset +21d  window 7d   visit          "tube patency check"
    rule 2  offset +90d  window 14d  test           audiogram, condition: pre-op
                                                     hearing loss recorded
    rule 3  offset +180d window 30d  visit          "tube check", repeating

### 2. Conditions
Use `condition` to avoid noise: only schedule the audiogram if a hearing loss
was documented, only schedule the calcium check after a total thyroidectomy.
A protocol that generates recalls nobody acts on trains staff to ignore the
work list.

### 3. Wire the trigger
The protocol resolver listens for the domain event
(`ProcedurePerformed`, `SurgeryCompleted`, `DiagnosisRecorded`) and
materializes `recall` rows. Do not create recalls directly from a service; go
through the resolver so every recall has a traceable source.

### 4. Repeating and terminating rules
State explicitly when a repeating rule stops: tube checks stop when the
`ear_device` status becomes extruded or removed; surveillance stops at the end
of the protocol period or on a status change. A recall series with no
termination is a bug.

### 5. Cancellation
When the expected event happens early (the patient comes in and the audiogram
is done), the matching recall must close automatically through the event
handler. Never leave a doctor to close it by hand.

### 6. Work list and reminders
Confirm the recall appears on the assistant's work list with the right reason
text, and that the reminder message template exists in every patient locale.

### 7. Tests
- the trigger creates exactly the expected rules with the expected dates
- a condition that is not met creates no recall
- the closing event cancels the pending recall
- a repeating series terminates on its stop condition
- timezone: due dates are clinic-local dates, not UTC timestamps

## Checklist

- [ ] Intervals come from the documented protocol, not from memory
- [ ] Every interval is an editable default, not a constant in code
- [ ] Conditions prevent recalls that nobody will action
- [ ] Repeating rules have an explicit stop condition
- [ ] The completing event closes the recall automatically
- [ ] Reminder templates exist in every patient locale
- [ ] Due dates are clinic-local dates

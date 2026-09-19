# Tickets

One file per phase. Work one ticket at a time, in order.

| File | Phase | Modules | Depends on |
|---|---|---|---|
| `phase-0.md` | Skeleton and foundations | infrastructure, core packages | nothing |
| `phase-1.md` | Foundation | auth, users, clinics, terminology, patients, scheduling, attachments, documents base, admin | phase 0 |
| `phase-2.md` | Consultation | encounters, observations, examination, diagnoses, prescriptions, documents full, recalls manual | phase 1 |
| `phase-3.md` | Office procedures | endoscopy, laryngoscopy, otology | phase 2 |
| `phase-4.md` | Audiology | audiology | phase 2 |
| `phase-5.md` | Scores and calculators | questionnaires, calculators | phase 2 |
| `phase-6.md` | Vestibular | vestibular | phase 3, phase 5 |
| `phase-7.md` | Surgery | surgery | phase 2, phase 5 |
| `phase-8.md` | Sub-specialties | sleep, allergy, headneck, pediatrics, voice_swallowing | phase 3, 4, 5, 7 |
| `phase-9.md` | Analytics and AI | analytics, ai | everything |

## Detail level

Phases 0 to 3 are specified in detail: field lists, schema references, test
requirements. Phases 4 to 9 give scope, dependencies and the constraints that
matter, but deliberately leave details open, because they depend on decisions
made while building the earlier phases. Fill them in when you get there.

## How to use a ticket with Cursor

    Do ticket P1-05 from docs/tickets/phase-1.md.
    Use the add-backend-feature skill.
    Show me the plan and the file list before generating anything.

Rules:
- One ticket per chat session. Start a new session between tickets so context
  stays clean.
- Backend ticket first, then `make contracts`, then the frontend ticket.
- Never skip a ticket's acceptance criteria. If Cursor says it is done, check
  the criteria yourself before moving on.
- If a ticket turns out to be bigger than expected, split it in the file rather
  than letting one session sprawl.

## Ticket status

Mark tickets as you go, in the file itself:

    - [ ] not started
    - [~] in progress
    - [x] done and reviewed

## Reference documents

- `docs/clinical/feature-specification.txt` — what each module must do
- `docs/architecture/architecture-and-structure.txt` — layering, schema, conventions
- `AGENTS.md` and `.cursor/rules/` — how all code must look

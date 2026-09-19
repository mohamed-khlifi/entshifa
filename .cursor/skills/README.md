# Cursor skills for this project

Skills load only when the agent decides the task matches, which keeps the
context window clean. Invoke one explicitly with `/` in agent chat, or just
describe the task and let it be picked up.

| Skill | Use it when |
|---|---|
| `add-backend-feature` | adding a new clinical domain to the API |
| `add-frontend-feature` | adding the UI for a domain, screen or flow |
| `add-clinical-calculator` | anything computed from clinical data |
| `add-anatomical-map` | a new clickable examination map |
| `add-questionnaire-instrument` | a new score or questionnaire |
| `add-language` | adding a locale, including RTL |
| `add-document-template` | a new printed or PDF output |
| `add-recall-protocol` | a clinical event should schedule future actions |

Standing rules that always apply live in `AGENTS.md` and `.cursor/rules/`.
Skills describe how to do a specific job; rules describe how all code must look.

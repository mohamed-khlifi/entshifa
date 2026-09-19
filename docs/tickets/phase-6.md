# Phase 6: vestibular

**Goal:** a vertigo consultation is structured enough that the history alone
produces a usable summary card, and maneuvers are documented with outcomes.
**Depends on:** phase 3 (procedure records), phase 5 (DHI).
**Estimated:** 4 weeks.
**Module:** vestibular.

Reference: feature spec section 9. Architecture section 25.9.

---

## - [ ] P6-01 Structured vertigo history (backend and frontend)

The timing-and-triggers approach: character, timing pattern, episode duration,
triggers, auditory symptoms and side, neurological symptoms, migraine features,
cardiovascular history.

Auto-generated summary card, for example: "Recurrent episodes lasting seconds,
triggered by turning in bed, no auditory symptoms, no neurological symptoms,
DHI 48 (moderate)." This card is what the doctor reads before examining, so it
must be accurate and short.

---

## - [ ] P6-02 Bedside examination including positional tests

Spontaneous and gaze-evoked nystagmus, head impulse, test of skew, the three
HINTS findings displayed without a verdict, head-shaking, Dix-Hallpike right
and left, supine roll, Romberg, gait, cerebellar tests.

Positional test results record nystagmus direction, latency, duration,
fatigability and reversal.

---

## - [ ] P6-03 Canal pattern engine

From the positional test results, name the canal pattern the findings match
("consistent with right posterior canal"), which the doctor confirms or
overrides.

**This is pattern matching against documented criteria, not diagnosis. The
wording must never assert a diagnosis.** Take the patterns from the source
criteria, not from memory, and test each one.

---

## - [ ] P6-04 Criteria checklists

Barany Society criteria for Meniere's, vestibular migraine, BPPV by canal,
PPPD, vestibular paroxysmia, bilateral vestibulopathy, as data-driven
checklists that tick what is already documented and show what is missing.

Store the criteria text with its version and year. The doctor decides; the app
never concludes.

---

## - [ ] P6-05 Vestibular laboratory results

vHIT gains per canal, caloric with the Jongkees calculation and the clinic's
significance threshold, cervical and ocular VEMP, posturography and rotary
chair summaries.

---

## - [ ] P6-06 Repositioning maneuvers and rehabilitation

Maneuver documentation with side, canal, repetitions, nystagmus during,
immediate re-test and outcome at follow-up. Home exercise handouts in the
patient's language. Two-week recall with a repeat DHI. Outcomes feed the
doctor's maneuver success statistics in phase 9.

---
name: add-clinical-calculator
description: Add a clinical calculation, score or grading system as a versioned pure-function engine with known-answer tests. Use for anything computed from clinical data — PTA, air-bone gap, questionnaire scoring, TNM staging, pediatric dosing, Jongkees, threshold shift.
---

# Add a clinical calculator

This is the highest-risk code in the project. A wrong number here reaches a
patient. Follow every step.

## Non-negotiable rules

- Pure function. No database, no HTTP, no settings lookup, no `datetime.now()`.
  If it needs the current date, it is a parameter.
- Lives in `engines/<area>/<name>.py`, never in a service, never in the frontend.
- Exposes `VERSION` and `REFERENCE`.
- Returns a `CalculationResult` dataclass, never a bare number or a tuple.
- Has known-answer tests citing the source publication.
- **Never invent a formula, cut-off, threshold or staging table from memory.**
  Use the value documented in `docs/clinical/feature-specification.txt`
  (appendix A lists the scores with their ranges and bands), or ask. Mark
  anything unverified with `# VERIFY:` naming exactly what needs checking
  against which publication.

## Steps

### 1. Write the engine

```python
# engines/audiology/pta.py
VERSION = "1.0.0"
REFERENCE = "WHO 2021 grades of hearing impairment"

@dataclass(frozen=True)
class PtaInput:
    thresholds_db: Mapping[int, float | None]   # frequency Hz -> dB HL
    formula: PtaFormula

def pure_tone_average(data: PtaInput) -> CalculationResult:
    """Mean threshold over the formula's frequencies.

    Raises IncompleteThresholdsError when a required frequency is missing or
    is a no-response.
    """
```

- Validate inputs explicitly and raise a typed domain error. Never return a
  silent default, never return None for "could not compute".
- Handle the clinical edge cases: no response at the audiometer limit, masked
  values, missing frequencies, values outside plausible range.
- Keep units explicit in names and in the result.

### 2. Register it

Add to `engines/registry.py` with its input schema, unit, formula string and
reference, so the generic calculator endpoint and the frontend can render it
without new code.

### 3. Write known-answer tests

`tests/clinical/test_<name>.py`. Each test docstring cites the source and the
worked example. Cover:
- the reference case from the publication
- boundary values on every severity band
- each edge case above
- a property test where one applies (monotonicity, symmetry, range)

### 4. Persist results correctly

When a service stores the output, write `calculation_result` with the inputs,
the value, the `engine_version`, the formula and the reference, so the number
can be reproduced years later even after the engine changes.

### 5. Versioning

Any change to the numeric output bumps `VERSION`. Never silently change a
formula: stored historical results keep their original version, and the
comparison views must be able to say which version produced which number.

## Checklist

- [ ] Pure: no I/O, no clock, no globals
- [ ] `VERSION` and `REFERENCE` present
- [ ] Returns `CalculationResult` with inputs, formula, version, flags
- [ ] Registered in the calculator registry
- [ ] Known-answer tests citing the source
- [ ] Edge cases covered: no response, masked, missing frequency, out of range
- [ ] Nothing invented; uncertainties marked `# VERIFY:`
- [ ] Result persistence records the engine version

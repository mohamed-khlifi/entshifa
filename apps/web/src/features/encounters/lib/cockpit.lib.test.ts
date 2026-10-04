import { describe, expect, it } from "vitest";

import {
  chiefComplaintSummary,
  composeClinicalNote,
  emptyToNull,
} from "./clinical-note";
import { problemStatusFor } from "./cockpit-state";
import {
  groupComplaints,
  makePrimary,
  primaryComplaint,
  toggleComplaint,
  type ComplaintChoice,
} from "./complaints";
import { asLaterality, diffEncounterPatch } from "./encounter-patch";
import { mapsForSections, unmappedSections } from "./exam-sections";
import { draftKey, resolveHydration } from "./hydration";
import { removePlanItem, toggleSuggestion } from "./plan-items";
import { suggestedRedFlags, toggleRedFlag } from "./red-flags";
import { parseTemplateConfig } from "./template-config";

const nasal: ComplaintChoice = {
  code: "CC.NASAL_OBSTRUCTION",
  conceptPublicId: "01NASAL0000000000000000000",
  display: "Nasal obstruction",
};
const pain: ComplaintChoice = {
  code: "CC.EAR_PAIN",
  conceptPublicId: "01EARPAIN00000000000000000",
  display: "Ear pain",
};

const emptySnapshot = {
  chiefComplaintSummary: null,
  historyText: null,
  assessmentText: null,
  planText: null,
  complaints: [],
};

describe("clinical note", () => {
  it("composes structured lines and a free-text note", () => {
    expect(
      composeClinicalNote(
        [
          { label: "Onset", value: "  3 days " },
          { label: " ", value: "ignored" },
          { label: "Course", value: "" },
        ],
        "  Worse at night  ",
        (line) => `${line.label}: ${line.value}`,
      ),
    ).toBe("Onset: 3 days\n\nWorse at night");
  });

  it("keeps the chief complaint summary inside the column limit", () => {
    expect(chiefComplaintSummary("  ")).toBeNull();
    expect(chiefComplaintSummary("Ear pain")).toBe("Ear pain");
    expect(chiefComplaintSummary("x".repeat(300))).toHaveLength(255);
  });

  it("treats blank text as null", () => {
    expect(emptyToNull("   ")).toBeNull();
    expect(emptyToNull("note")).toBe("note");
  });
});

describe("complaints", () => {
  it("groups seeded complaints by region and filters on display or code", () => {
    const groups = groupComplaints(
      [nasal, pain, { ...pain, code: "CC.UNKNOWN", display: "Other" }],
      "nasal",
    );
    expect(groups).toEqual([{ region: "nose", items: [nasal] }]);
  });

  it("makes the first selection primary and promotes the next when it is removed", () => {
    const first = toggleComplaint([], nasal);
    const both = toggleComplaint(first, pain);
    expect(primaryComplaint(both)?.code).toBe("CC.NASAL_OBSTRUCTION");
    const remaining = toggleComplaint(both, nasal);
    expect(remaining).toEqual([{ ...pain, isPrimary: true }]);
  });

  it("moves the primary flag without dropping the other complaints", () => {
    const selected = toggleComplaint(toggleComplaint([], nasal), pain);
    expect(primaryComplaint(makePrimary(selected, pain.code))?.code).toBe(
      "CC.EAR_PAIN",
    );
    expect(makePrimary(selected, "CC.MISSING")).toEqual(selected);
  });
});

describe("encounter patch", () => {
  it("sends only the dirty fields and the current version", () => {
    expect(diffEncounterPatch(3, emptySnapshot, emptySnapshot)).toBeNull();
    expect(
      diffEncounterPatch(4, emptySnapshot, {
        ...emptySnapshot,
        historyText: "Onset: 3 days",
        complaints: [
          {
            conceptCode: "CC.EAR_PAIN",
            isPrimary: true,
            laterality: "sideways",
            durationText: null,
            sortOrder: 0,
          },
        ],
      }),
    ).toEqual({
      version: 4,
      historyText: "Onset: 3 days",
      complaints: [
        {
          conceptCode: "CC.EAR_PAIN",
          durationText: null,
          isPrimary: true,
          laterality: null,
          sortOrder: 0,
        },
      ],
    });
  });

  it("accepts only the laterality vocabulary", () => {
    expect(asLaterality("left")).toBe("left");
    expect(asLaterality("sideways")).toBeNull();
  });
});

describe("template, flags, exam, and plan helpers", () => {
  it("rejects a template config that is not the documented shape", () => {
    expect(parseTemplateConfig({ historyFields: [{ id: "" }] })).toMatchObject({
      historyFields: [],
      examSections: [],
      favoriteDiagnoses: [],
    });
    expect(
      parseTemplateConfig({
        historyFields: [
          {
            id: "pattern",
            labelKey: "encounters.templates.nasal_obstruction.fields.pattern",
            fieldType: "select",
          },
        ],
        examSections: ["nose", "endoscopy"],
        defaultFollowUpDays: 14,
      }).historyFields,
    ).toHaveLength(1);
  });

  it("suggests red flags from the selected complaints and toggles confirmation", () => {
    expect(suggestedRedFlags(["CC.HOARSENESS", "CC.TINNITUS"])).toEqual([
      "dysphagiaWeightLoss",
      "hoarsenessSmoker",
      "unilateralTinnitus",
    ]);
    expect(toggleRedFlag(["stridor"], "stridor")).toEqual([]);
    expect(toggleRedFlag([], "stridor")).toEqual(["stridor"]);
  });

  it("maps exam sections onto anatomical maps and leaves the rest pending", () => {
    expect(mapsForSections(["ear", "nose", "ear", "laryngoscopy"])).toEqual([
      "tympanic-membrane",
      "nasal-cavity",
    ]);
    expect(unmappedSections(["ear", "laryngoscopy", "face"])).toEqual([
      "laryngoscopy",
      "face",
    ]);
  });

  it("toggles a suggestion by source and removes a plan row by id", () => {
    const added = toggleSuggestion(
      [],
      "test:AUDIO",
      "test_requested",
      "Audiometry",
      "row-1",
    );
    expect(
      toggleSuggestion(
        added,
        "test:AUDIO",
        "test_requested",
        "Audiometry",
        "row-2",
      ),
    ).toEqual([]);
    expect(removePlanItem(added, "row-1")).toEqual([]);
  });

  it("maps a confirmed diagnosis to an active problem", () => {
    expect(problemStatusFor("confirmed")).toBe("active");
    expect(problemStatusFor("suspected")).toBe("suspected");
    expect(problemStatusFor("ruled_out")).toBe("ruled_out");
  });
});

describe("hydration", () => {
  it("keeps a local draft, including when the server version moved", () => {
    expect(resolveHydration(null, 2)).toEqual({
      source: "server",
      conflict: false,
      state: null,
    });
    expect(
      resolveHydration({ baseVersion: 1, state: { onset: "3 days" } }, 4),
    ).toEqual({
      source: "draft",
      conflict: true,
      state: { onset: "3 days" },
    });
  });

  it("keys the crash draft by the encounter id", () => {
    expect(draftKey("01ENCOUNTER000000000000000")).toBe(
      "encounter:01ENCOUNTER000000000000000",
    );
  });
});

import { describe, expect, it } from "vitest";

import { timelineHref } from "./timeline-href";
import { TIMELINE_ROW_HEIGHT, timelineWindow } from "./timeline-window";

describe("timelineWindow", () => {
  it("returns an empty window for an empty history", () => {
    expect(timelineWindow(0, 400, 0)).toEqual({
      start: 0,
      end: 0,
      paddingTop: 0,
      paddingBottom: 0,
    });
  });

  it("keeps the first screen plus overscan at the top", () => {
    const window = timelineWindow(
      0,
      TIMELINE_ROW_HEIGHT * 2,
      40,
      TIMELINE_ROW_HEIGHT,
      1,
    );
    expect(window.start).toBe(0);
    expect(window.end).toBe(4);
    expect(window.paddingTop).toBe(0);
    expect(window.paddingBottom).toBe(36 * TIMELINE_ROW_HEIGHT);
  });

  it("slides the window with the scroll offset", () => {
    const window = timelineWindow(
      TIMELINE_ROW_HEIGHT * 10,
      TIMELINE_ROW_HEIGHT,
      30,
      TIMELINE_ROW_HEIGHT,
      0,
    );
    expect(window).toEqual({
      start: 10,
      end: 11,
      paddingTop: 10 * TIMELINE_ROW_HEIGHT,
      paddingBottom: 19 * TIMELINE_ROW_HEIGHT,
    });
  });

  it("clamps the window at the end of the list", () => {
    const window = timelineWindow(10_000, 200, 3, TIMELINE_ROW_HEIGHT, 2);
    expect(window.start).toBe(0);
    expect(window.end).toBe(3);
    expect(window.paddingTop).toBe(0);
    expect(window.paddingBottom).toBe(0);
  });
});

describe("timelineHref", () => {
  const patientId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

  it("opens a visit on the encounter", () => {
    expect(
      timelineHref(patientId, {
        eventType: "consultation",
        publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB0",
        encounterPublicId: null,
      }),
    ).toBe(`/patients/${patientId}/encounters/01ARZ3NDEKTSV4RRFFQ69G5FB0`);
  });

  it("opens a diagnosis on its encounter and a recall on the work list", () => {
    expect(
      timelineHref(patientId, {
        eventType: "diagnosis",
        publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB1",
        encounterPublicId: "01ARZ3NDEKTSV4RRFFQ69G5FB2",
      }),
    ).toBe(`/patients/${patientId}/encounters/01ARZ3NDEKTSV4RRFFQ69G5FB2`);
    expect(
      timelineHref(patientId, {
        eventType: "recall",
        publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB1",
        encounterPublicId: null,
      }),
    ).toBe("/recalls");
  });
});

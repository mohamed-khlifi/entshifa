import { cleanup, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it } from "vitest";

import type { QuestionnaireResponseRead } from "@/lib/api/generated";
import { testIds } from "@/lib/test/test-id";

import enQuestionnaires from "../../../../../../packages/i18n-messages/en/questionnaires.json";

import { QuestionnaireScoreSummaryCard } from "./QuestionnaireScoreSummaryCard";

function mockResponse(
  overrides: Partial<QuestionnaireResponseRead> = {},
): QuestionnaireResponseRead {
  return {
    publicId: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    completedAt: "2025-06-01T14:30:00Z",
    totalScore: "66",
    minScore: 0,
    maxScore: 110,
    instrumentCode: "snot22",
    instrumentTitle: "SNOT-22",
    locale: "en",
    enteredBy: "patient",
    encounterId: null,
    severityBand: "moderate",
    subscaleScores: { rhinologic: "30", extranasal: "12" },
    changeFromPrevious: "-12",
    mcid: "8.9",
    mcidReached: true,
    ...overrides,
  };
}

describe("QuestionnaireScoreSummaryCard", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders total, severity band, subscales, and MCID change", () => {
    render(
      <NextIntlClientProvider
        locale="en"
        messages={{ questionnaires: enQuestionnaires }}
      >
        <QuestionnaireScoreSummaryCard response={mockResponse()} />
      </NextIntlClientProvider>,
    );

    expect(screen.getByTestId(testIds.questionnaires.scoreCard)).toBeTruthy();
    expect(
      screen.getByTestId(testIds.questionnaires.totalScore).textContent,
    ).toBe("66");
    expect(
      screen.getByTestId(testIds.questionnaires.severityBand).textContent,
    ).toBe("Moderate");
    expect(
      screen.getByTestId(testIds.questionnaires.subscaleList),
    ).toBeTruthy();
    expect(
      screen.getByTestId(testIds.questionnaires.changeFromPrevious),
    ).toBeTruthy();
    expect(
      screen.getByTestId(testIds.questionnaires.mcidBadge).textContent,
    ).toContain("Clinically meaningful change");
  });

  it("shows no prior administration when delta is absent", () => {
    render(
      <NextIntlClientProvider
        locale="en"
        messages={{ questionnaires: enQuestionnaires }}
      >
        <QuestionnaireScoreSummaryCard
          response={mockResponse({
            changeFromPrevious: null,
            mcid: null,
            mcidReached: null,
          })}
        />
      </NextIntlClientProvider>,
    );

    expect(screen.getByText("No prior administration")).toBeTruthy();
    expect(screen.queryByTestId(testIds.questionnaires.mcidBadge)).toBeNull();
  });
});

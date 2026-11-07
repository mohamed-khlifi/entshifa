import { render, screen } from "@testing-library/react";

import { testIds } from "@/lib/test/test-id";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";

import enQuestionnaires from "../../../../../../packages/i18n-messages/en/questionnaires.json";
import enErrors from "../../../../../../packages/i18n-messages/en/errors.json";

import { PublicQuestionnaireRunner } from "./PublicQuestionnaireRunner";

vi.mock("../hooks/use-questionnaire-queries", () => ({
  usePublicQuestionnaireSession: () => ({
    isLoading: false,
    isError: false,
    data: {
      patientFirstName: "Sam",
      clinicName: "Demo Clinic",
      locale: "en",
      channel: "tablet",
      expiresAt: "2099-01-01T00:00:00Z",
      instrument: {
        code: "snot22",
        title: "SNOT-22",
        category: "sinonasal",
        respondent: "patient",
        items: [
          {
            code: "q1",
            position: 1,
            text: "Question one",
            options: [{ value: 0, position: 1, text: "None" }],
          },
        ],
      },
    },
  }),
  useSubmitPublicQuestionnaire: () => ({
    isPending: false,
    mutateAsync: vi.fn(),
  }),
}));

describe("PublicQuestionnaireRunner", () => {
  it("renders greeting and question", () => {
    render(
      <NextIntlClientProvider
        locale="en"
        messages={{ questionnaires: enQuestionnaires, errors: enErrors }}
      >
        <PublicQuestionnaireRunner token="test-token" />
      </NextIntlClientProvider>,
    );
    expect(screen.getByTestId(testIds.questionnaires.runner)).toBeTruthy();
    expect(screen.getByText("Question one")).toBeTruthy();
  });
});

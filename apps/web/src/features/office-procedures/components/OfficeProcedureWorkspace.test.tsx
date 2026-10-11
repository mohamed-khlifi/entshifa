import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { testIds } from "@/lib/test/test-id";
import messages from "../../../../../../packages/i18n-messages/en/officeProcedures.json";

import { OfficeProcedureWorkspace } from "./OfficeProcedureWorkspace";

const patientId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

const harness = vi.hoisted(() => ({
  save: vi.fn(),
  sign: vi.fn(),
}));

vi.mock("../hooks/use-office-procedures", () => ({
  usePatientOfficeProcedures: () => ({
    data: { items: [], page: { limit: 50, offset: 0, total: 0 } },
    isLoading: false,
    isError: false,
  }),
  useSaveOfficeProcedure: () => ({
    mutateAsync: harness.save,
    isPending: false,
  }),
  useSignOfficeProcedure: () => ({
    mutateAsync: harness.sign,
    isPending: false,
  }),
}));

vi.mock("@/features/clinics", () => ({
  useCurrentClinicQuery: () => ({
    data: { timezone: "UTC" },
    isLoading: false,
  }),
}));

vi.mock("@/features/attachments", () => ({
  dateTimeLocalToUtcIso: (value: string) =>
    value.length > 0 ? `${value}:00.000Z` : null,
}));

describe("OfficeProcedureWorkspace", () => {
  afterEach(() => {
    cleanup();
    harness.save.mockReset();
    harness.sign.mockReset();
  });

  it("saves an epistaxis cautery from one screen", async () => {
    harness.save.mockResolvedValue({
      publicId: "01ARZ3NDEKTSV4RRFFQ69G5FB2",
      procedureId: "01ARZ3NDEKTSV4RRFFQ69G5FB3",
      version: 1,
    });
    const view = render(
      <NextIntlClientProvider
        locale="en"
        messages={{ officeProcedures: messages }}
      >
        <OfficeProcedureWorkspace
          patientId={patientId}
          procedureId={null}
          onProcedureChange={() => undefined}
        />
      </NextIntlClientProvider>,
    );
    expect(view.getByTestId(testIds.officeProcedures.root)).toBeTruthy();
    expect(view.getByTestId(testIds.officeProcedures.report)).toBeTruthy();
    fireEvent.change(view.getByTestId(testIds.officeProcedures.systolic), {
      target: { value: "148" },
    });
    fireEvent.change(view.getByTestId(testIds.officeProcedures.diastolic), {
      target: { value: "86" },
    });
    fireEvent.click(view.getByTestId(testIds.officeProcedures.save));
    await waitFor(() => {
      expect(harness.save).toHaveBeenCalled();
    });
    const input = harness.save.mock.calls[0]?.[0] as {
      procedureId: string | null;
      createBody: {
        patientPublicId: string;
        detail: { subtype: string; method: string };
      };
    };
    expect(input.procedureId).toBeNull();
    expect(input.createBody.patientPublicId).toBe(patientId);
    expect(input.createBody.detail.subtype).toBe("epistaxis_management");
    expect(input.createBody.detail.method).toBe("silver_nitrate");
    expect(harness.sign).not.toHaveBeenCalled();
  });
});

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PrescriptionPaper } from "./PrescriptionPaper";
import { testIds } from "@/lib/test/test-id";

describe("PrescriptionPaper", () => {
  it("prints the clinic identifiers in the patient language", () => {
    const view = render(
      <PrescriptionPaper
        locale="fr"
        model={{
          clinicName: "Clinique du Centre",
          legalName: "Clinique du Centre SARL",
          addressLines: ["12 rue de la Santé"],
          phone: null,
          email: null,
          registrationNumber: "RC-10",
          taxId: null,
          patientName: "Ada Martin",
          birthDate: "1 janv. 1990",
          mrn: "MRN1",
          weightKg: null,
          identifier: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
          lines: [
            {
              title: "Amoxicilline",
              dose: "400",
              unit: "mg",
              route: "oral",
              frequencyPerDay: 2,
              durationDays: 7,
              instructions: "Après le repas.",
              renewable: false,
              substitutionAllowed: false,
              taper: [],
            },
          ],
        }}
      />,
    );
    const paper = view.getByTestId(testIds.prescriptions.paper);
    expect(paper.textContent).toContain("Ordonnance");
    expect(paper.textContent).toContain("Clinique du Centre SARL");
    expect(paper.textContent).toContain("Non substituable");
    expect(paper.textContent).toContain("Après le repas.");
  });
});

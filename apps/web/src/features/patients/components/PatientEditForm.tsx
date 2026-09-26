"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";

import { updatePatient } from "../api/patients.api";
import { PatientFieldGroups } from "../components/PatientFieldGroups";
import { partialFormToUpdate, patientToFormValues } from "../lib/map-patient";
import { createPatientFormSchema } from "../schemas/patient-form.schema";
import { AutosaveIndicator, DirtyGuard, Form } from "@/components/forms";
import { Button } from "@/components/ui/button";
import type { PatientRead } from "@/lib/api/generated";
import { queryKeys } from "@/lib/api/query-keys";
import { useClinicalForm } from "@/lib/forms/createForm";
import { Permission } from "@/lib/permissions";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { usePermission } from "@/providers/permission-provider";
import { useSession } from "@/providers/session-provider";

export function PatientEditForm({ patient }: { patient: PatientRead }) {
  const t = useTranslations("patients");
  const canWrite = usePermission(Permission.PATIENT_WRITE);
  const locale = useLocale();
  const { session } = useSession();
  const queryClient = useQueryClient();
  const [conflict, setConflict] = useState(false);
  const schema = createPatientFormSchema(t);

  const { form, autosaveStatus, handleSubmit } = useClinicalForm({
    schema,
    defaultValues: patientToFormValues(patient),
    autosave:
      canWrite && session
        ? {
            key: `patient:${patient.publicId}`,
            version: patient.version,
            onSave: async ({ values, version }) => {
              const updated = await updatePatient(
                patient.publicId,
                partialFormToUpdate(values, version),
                { locale, clinicPublicId: session.clinicPublicId },
              );
              queryClient.setQueryData(
                queryKeys.patients.detail(patient.publicId),
                updated,
              );
              setConflict(false);
              return { version: updated.version };
            },
            onConflict: () => setConflict(true),
          }
        : undefined,
    onSubmit: async () => undefined,
  });

  if (!canWrite) {
    return null;
  }

  return (
    <section className="space-y-4" {...testIdProps(testIds.patients.editForm)}>
      <h2 className="text-lg font-semibold">{t("form.editTitle")}</h2>
      <p className="text-sm text-muted-foreground">
        {t("header.mrn", { mrn: patient.mrn })}
      </p>
      {conflict ? (
        <div className="space-y-2" {...testIdProps(testIds.patients.conflict)}>
          <p className="text-sm text-destructive">{t("form.conflict")}</p>
          <Button
            type="button"
            variant="secondary"
            {...testIdProps(testIds.patients.conflictReload)}
            onClick={() => {
              void queryClient
                .invalidateQueries({
                  queryKey: queryKeys.patients.detail(patient.publicId),
                })
                .then(() => {
                  window.location.reload();
                });
            }}
          >
            {t("form.reload")}
          </Button>
        </div>
      ) : null}
      <Form form={form} onSubmit={handleSubmit}>
        <AutosaveIndicator status={autosaveStatus} />
        <DirtyGuard>
          <fieldset disabled={!canWrite} className="space-y-8">
            <PatientFieldGroups mode="edit" />
          </fieldset>
        </DirtyGuard>
      </Form>
    </section>
  );
}

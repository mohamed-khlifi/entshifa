"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useRef, useState } from "react";
import { toast } from "sonner";

import { PatientFieldGroups } from "../components/PatientFieldGroups";
import { createPatient } from "../api/patients.api";
import { duplicateCandidateIds } from "../lib/duplicates";
import { formValuesToCreate } from "../lib/map-patient";
import {
  createPatientFormSchema,
  emptyPatientFormValues,
} from "../schemas/patient-form.schema";
import { AutosaveIndicator, DirtyGuard, Form } from "@/components/forms";
import { Button } from "@/components/ui/button";
import { Link, useRouter } from "@/lib/i18n/navigation";
import { queryKeys } from "@/lib/api/query-keys";
import { useClinicalForm } from "@/lib/forms/createForm";
import { publicIdTestId, testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

export function PatientCreateForm() {
  const t = useTranslations("patients");
  const locale = useLocale();
  const router = useRouter();
  const { session } = useSession();
  const queryClient = useQueryClient();
  const confirmDuplicate = useRef(false);
  const idempotencyKey = useRef(crypto.randomUUID());
  const [candidates, setCandidates] = useState<string[] | null>(null);
  const schema = createPatientFormSchema(t);

  const { form, autosaveStatus, handleSubmit } = useClinicalForm({
    schema,
    defaultValues: emptyPatientFormValues,
    autosave: session
      ? {
          key: `patient-new:${session.clinicPublicId}`,
          version: 0,
          onSave: async () => ({ version: 0 }),
        }
      : undefined,
    onSubmit: async (values) => {
      if (!session) {
        return;
      }
      try {
        const created = await createPatient(
          formValuesToCreate(values, confirmDuplicate.current),
          { locale, clinicPublicId: session.clinicPublicId },
          idempotencyKey.current,
        );
        await queryClient.invalidateQueries({
          queryKey: queryKeys.patients.all,
        });
        toast.success(t("form.created"));
        router.push(`/patients/${created.publicId}`);
      } catch (error) {
        const matches = duplicateCandidateIds(error);
        if (matches) {
          setCandidates(matches);
          confirmDuplicate.current = false;
          idempotencyKey.current = crypto.randomUUID();
          return;
        }
        throw error;
      }
    },
  });

  return (
    <div
      className="mx-auto max-w-3xl space-y-4"
      {...testIdProps(testIds.patients.createForm)}
    >
      <Form form={form} onSubmit={handleSubmit} className="space-y-6">
        <div className="flex items-center justify-between gap-3">
          <AutosaveIndicator status={autosaveStatus} />
        </div>
        <DirtyGuard>
          <PatientFieldGroups mode="create" />
          <Button type="submit" {...testIdProps(testIds.patients.createSubmit)}>
            {t("form.submitCreate")}
          </Button>
        </DirtyGuard>
      </Form>
      {candidates ? (
        <div
          role="alertdialog"
          className="space-y-3 rounded-xl border border-border bg-card p-4"
          {...testIdProps(testIds.patients.duplicate)}
        >
          <h3 className="font-semibold">{t("duplicate.title")}</h3>
          <p className="text-sm text-muted-foreground">{t("duplicate.body")}</p>
          <ul className="space-y-2">
            {candidates.map((publicId) => (
              <li key={publicId}>
                <Link
                  href={`/patients/${publicId}`}
                  className="text-sm font-medium underline"
                  {...testIdProps(
                    publicIdTestId("patients.duplicate.candidate", publicId),
                  )}
                >
                  {t("duplicate.open")}
                </Link>
              </li>
            ))}
          </ul>
          <div className="flex gap-2">
            <Button
              type="button"
              onClick={() => {
                confirmDuplicate.current = true;
                void handleSubmit();
              }}
              {...testIdProps(testIds.patients.duplicateConfirm)}
            >
              {t("duplicate.confirm")}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setCandidates(null)}
              {...testIdProps(testIds.patients.duplicateCancel)}
            >
              {t("duplicate.cancel")}
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

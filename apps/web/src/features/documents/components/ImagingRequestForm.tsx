"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { formControlClass } from "@/components/ui/form-control";
import type { ImagingRequestInput } from "@/lib/api/generated";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

import {
  IMAGING_MODALITIES,
  MIN_OVERRIDE_REASON_LENGTH,
  mriOverrideRequired,
  overrideReasonAccepted,
} from "../lib/visit-documents";

type ImagingRequestFormProps = {
  flagCodes: readonly string[];
  suggestedQuestion: string;
  pending: boolean;
  onSubmit: (body: ImagingRequestInput) => void;
  onClose: () => void;
};

export function ImagingRequestForm({
  flagCodes,
  suggestedQuestion,
  pending,
  onSubmit,
  onClose,
}: ImagingRequestFormProps) {
  const t = useTranslations("documents");
  const [modality, setModality] = useState<ImagingRequestInput["modality"]>(
    "ct_sinuses_noncontrast",
  );
  const [question, setQuestion] = useState(suggestedQuestion);
  const [renal, setRenal] = useState(false);
  const [contrast, setContrast] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const blocked = mriOverrideRequired(modality, flagCodes);
  const canSubmit = !blocked || overrideReasonAccepted(overrideReason);

  return (
    <form
      className="space-y-3"
      {...testIdProps(testIds.documents.imagingForm)}
      onSubmit={(event) => {
        event.preventDefault();
        if (!canSubmit) {
          return;
        }
        onSubmit({
          modality,
          clinicalQuestion: question.trim() || null,
          renalImpairment: renal,
          contrastAllergy: contrast,
          overrideReason: blocked ? overrideReason.trim() : null,
        });
      }}
    >
      <div className="space-y-2">
        <Label htmlFor="imaging-modality">{t("visit.modality")}</Label>
        <Select
          id="imaging-modality"
          value={modality}
          onChange={(event) =>
            setModality(event.target.value as ImagingRequestInput["modality"])
          }
          {...testIdProps(testIds.documents.modality)}
        >
          {IMAGING_MODALITIES.map((code) => (
            <option key={code} value={code}>
              {modalityLabel(t, code)}
            </option>
          ))}
        </Select>
      </div>
      <SafetyFlags flagCodes={flagCodes} />
      <div className="space-y-2">
        <Label htmlFor="imaging-question">{t("visit.question")}</Label>
        <textarea
          id="imaging-question"
          className={cn(formControlClass, "min-h-24 py-2")}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          {...testIdProps(testIds.documents.clinicalQuestion)}
        />
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={contrast}
          onChange={(event) => setContrast(event.target.checked)}
          {...testIdProps(testIds.documents.contrast)}
        />
        {t("visit.contrast")}
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={renal}
          onChange={(event) => setRenal(event.target.checked)}
          {...testIdProps(testIds.documents.renal)}
        />
        {t("visit.renal")}
      </label>
      {blocked ? (
        <div
          className="space-y-2 rounded-lg border border-destructive bg-destructive/10 p-3"
          role="alert"
          {...testIdProps(testIds.documents.mriWarning)}
        >
          <p className="text-sm font-medium">{t("visit.mriWarning")}</p>
          <Label htmlFor="imaging-override">{t("visit.override")}</Label>
          <Input
            id="imaging-override"
            value={overrideReason}
            onChange={(event) => setOverrideReason(event.target.value)}
            {...testIdProps(testIds.documents.overrideReason)}
          />
          <p className="text-sm text-muted-foreground">
            {t("visit.overrideHint", { min: MIN_OVERRIDE_REASON_LENGTH })}
          </p>
        </div>
      ) : null}
      <div className="flex gap-2">
        <Button
          type="submit"
          disabled={pending || !canSubmit}
          {...testIdProps(testIds.documents.visitCreate)}
        >
          {t("visit.create")}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={onClose}
          {...testIdProps(testIds.documents.visitClose)}
        >
          {t("visit.close")}
        </Button>
      </div>
    </form>
  );
}

function SafetyFlags({ flagCodes }: { flagCodes: readonly string[] }) {
  const t = useTranslations("documents");
  const shown = [
    flagCodes.includes("pregnancy") ? t("visit.pregnancy") : null,
    flagCodes.includes("pacemaker") ? t("visit.pacemaker") : null,
    flagCodes.includes("cochlear_implant") ? t("visit.cochlearImplant") : null,
  ].filter((item): item is string => item != null);
  if (shown.length === 0) {
    return null;
  }
  return (
    <ul className="flex flex-wrap gap-2">
      {shown.map((label) => (
        <li
          key={label}
          className="rounded-full border border-border px-2 py-1 text-xs"
        >
          {label}
        </li>
      ))}
    </ul>
  );
}

function modalityLabel(
  t: ReturnType<typeof useTranslations<"documents">>,
  code: ImagingRequestInput["modality"],
): string {
  switch (code) {
    case "ct_sinuses_noncontrast":
      return t("visit.modalities.ct_sinuses_noncontrast");
    case "ct_temporal_bone_hr":
      return t("visit.modalities.ct_temporal_bone_hr");
    case "ct_neck_contrast":
      return t("visit.modalities.ct_neck_contrast");
    case "mri_iac_gadolinium":
      return t("visit.modalities.mri_iac_gadolinium");
    case "mri_neck":
      return t("visit.modalities.mri_neck");
    case "pet_ct":
      return t("visit.modalities.pet_ct");
    case "us_neck_fna":
      return t("visit.modalities.us_neck_fna");
    case "panoramic_dental":
      return t("visit.modalities.panoramic_dental");
    case "lateral_neck_adenoids":
      return t("visit.modalities.lateral_neck_adenoids");
  }
}

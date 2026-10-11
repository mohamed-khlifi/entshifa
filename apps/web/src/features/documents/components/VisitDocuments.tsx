"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { formControlClass } from "@/components/ui/form-control";
import { Card } from "@/components/ui/card";
import type {
  CertificateInput,
  DocumentCreate,
  LabRequestInput,
} from "@/lib/api/generated";
import { publicIdTestId, testIdProps, testIds } from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

import {
  useBatchPreviewMutation,
  useCreateDocumentMutation,
  useEncounterDocumentsQuery,
} from "../hooks/use-document-queries";
import {
  CERTIFICATE_PURPOSES,
  LAB_PANELS,
  type VisitDocumentKind,
} from "../lib/visit-documents";
import { ImagingRequestForm } from "./ImagingRequestForm";

const DOCUMENT_LOCALES = ["en", "fr", "ar"] as const;

type VisitDocumentsProps = {
  patientId: string;
  encounterId: string;
  flagCodes: readonly string[];
  suggestedQuestion: string;
  kind: VisitDocumentKind | null;
  onKind: (kind: VisitDocumentKind | null) => void;
};

export function VisitDocuments({
  patientId,
  encounterId,
  flagCodes,
  suggestedQuestion,
  kind,
  onKind,
}: VisitDocumentsProps) {
  const t = useTranslations("documents");
  const create = useCreateDocumentMutation(patientId);

  function submit(
    body: Omit<DocumentCreate, "patientPublicId" | "encounterPublicId">,
  ) {
    create.mutate(
      {
        ...body,
        patientPublicId: patientId,
        encounterPublicId: encounterId,
      },
      {
        onSuccess: () => {
          toast.success(t("visit.created"));
          onKind(null);
        },
      },
    );
  }

  return (
    <section className="space-y-3" {...testIdProps(testIds.documents.visitBar)}>
      <h2 className="text-lg font-semibold">{t("visit.title")}</h2>
      <div className="flex flex-wrap gap-2">
        <KindButton kind="consultation" current={kind} onKind={onKind} />
        <KindButton kind="referral" current={kind} onKind={onKind} />
        <KindButton kind="sick_leave" current={kind} onKind={onKind} />
        <KindButton kind="certificate" current={kind} onKind={onKind} />
        <KindButton kind="imaging" current={kind} onKind={onKind} />
        <KindButton kind="laboratory" current={kind} onKind={onKind} />
        <KindButton kind="batch" current={kind} onKind={onKind} />
      </div>
      {kind == null ? null : (
        <Card className="space-y-3 p-4">
          {kind === "imaging" ? (
            <ImagingRequestForm
              flagCodes={flagCodes}
              suggestedQuestion={suggestedQuestion}
              pending={create.isPending}
              onClose={() => onKind(null)}
              onSubmit={(imaging) =>
                submit({ templateCode: "imaging_request", imaging })
              }
            />
          ) : null}
          {kind === "laboratory" ? (
            <LaboratoryForm
              pending={create.isPending}
              onClose={() => onKind(null)}
              onSubmit={(laboratory) =>
                submit({ templateCode: "lab_request", laboratory })
              }
            />
          ) : null}
          {kind === "sick_leave" ? (
            <SickLeaveForm
              pending={create.isPending}
              onClose={() => onKind(null)}
              onSubmit={(sickLeave) =>
                submit({ templateCode: "sick_leave", sickLeave })
              }
            />
          ) : null}
          {kind === "certificate" ? (
            <CertificateForm
              pending={create.isPending}
              onClose={() => onKind(null)}
              onSubmit={(certificate) =>
                submit({ templateCode: "medical_certificate", certificate })
              }
            />
          ) : null}
          {kind === "referral" ? (
            <TextDocumentForm
              title={t("visit.referral")}
              fieldLabel={t("visit.recommendations")}
              showLocale
              pending={create.isPending}
              onClose={() => onKind(null)}
              onSubmit={(text, locale) =>
                submit({
                  templateCode: "referral_letter",
                  locale,
                  referral: { recommendations: text || null },
                })
              }
            />
          ) : null}
          {kind === "consultation" ? (
            <TextDocumentForm
              title={t("visit.consultation")}
              fieldLabel={t("visit.conclusion")}
              pending={create.isPending}
              onClose={() => onKind(null)}
              onSubmit={(text, locale) =>
                submit({
                  templateCode: "consultation_report",
                  locale,
                  consultation: { conclusion: text || null },
                })
              }
            />
          ) : null}
          {kind === "batch" ? (
            <BatchPrint
              patientId={patientId}
              encounterId={encounterId}
              onClose={() => onKind(null)}
            />
          ) : null}
        </Card>
      )}
    </section>
  );
}

function KindButton({
  kind,
  current,
  onKind,
}: {
  kind: VisitDocumentKind;
  current: VisitDocumentKind | null;
  onKind: (kind: VisitDocumentKind | null) => void;
}) {
  const t = useTranslations("documents");
  const testId = {
    consultation: testIds.documents.consultation,
    referral: testIds.documents.referral,
    sick_leave: testIds.documents.sickLeave,
    certificate: testIds.documents.certificate,
    imaging: testIds.documents.imaging,
    laboratory: testIds.documents.laboratory,
    batch: testIds.documents.batch,
  }[kind];
  const label = {
    consultation: t("visit.consultation"),
    referral: t("visit.referral"),
    sick_leave: t("visit.sickLeave"),
    certificate: t("visit.certificate"),
    imaging: t("visit.imaging"),
    laboratory: t("visit.laboratory"),
    batch: t("visit.batch"),
  }[kind];
  return (
    <Button
      type="button"
      variant={current === kind ? "default" : "secondary"}
      onClick={() => onKind(current === kind ? null : kind)}
      {...testIdProps(testId)}
    >
      {label}
    </Button>
  );
}

function LaboratoryForm({
  pending,
  onSubmit,
  onClose,
}: {
  pending: boolean;
  onSubmit: (body: LabRequestInput) => void;
  onClose: () => void;
}) {
  const t = useTranslations("documents");
  const [panels, setPanels] = useState<LabRequestInput["panels"]>([]);
  const [indication, setIndication] = useState("");
  return (
    <form
      className="space-y-3"
      onSubmit={(event) => {
        event.preventDefault();
        if (panels.length === 0) {
          return;
        }
        onSubmit({ panels, indication: indication.trim() || null });
      }}
    >
      <ul className="space-y-2">
        {LAB_PANELS.map((code) => (
          <li key={code}>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={panels.includes(code)}
                onChange={(event) => {
                  setPanels((current) =>
                    event.target.checked
                      ? [...current, code]
                      : current.filter((item) => item !== code),
                  );
                }}
              />
              {panelLabel(t, code)}
            </label>
          </li>
        ))}
      </ul>
      <Label htmlFor="lab-indication">{t("visit.indication")}</Label>
      <textarea
        id="lab-indication"
        className={cn(formControlClass, "min-h-20 py-2")}
        value={indication}
        onChange={(event) => setIndication(event.target.value)}
      />
      <FormActions pending={pending || panels.length === 0} onClose={onClose} />
    </form>
  );
}

function SickLeaveForm({
  pending,
  onSubmit,
  onClose,
}: {
  pending: boolean;
  onSubmit: (body: DocumentCreate["sickLeave"]) => void;
  onClose: () => void;
}) {
  const t = useTranslations("documents");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [absenceType, setAbsenceType] = useState<"work" | "school">("work");
  const [reasonMode, setReasonMode] = useState<"medical_reasons" | "diagnosis">(
    "medical_reasons",
  );
  const [reasonText, setReasonText] = useState("");
  return (
    <form
      className="space-y-3"
      onSubmit={(event) => {
        event.preventDefault();
        if (!start || !end) {
          return;
        }
        onSubmit({
          startDate: start,
          endDate: end,
          absenceType,
          reasonMode,
          reasonText: reasonText.trim() || null,
        });
      }}
    >
      <Label htmlFor="leave-type">{t("visit.absenceType")}</Label>
      <Select
        id="leave-type"
        value={absenceType}
        onChange={(event) =>
          setAbsenceType(event.target.value as "work" | "school")
        }
      >
        <option value="work">{t("visit.work")}</option>
        <option value="school">{t("visit.school")}</option>
      </Select>
      <Label htmlFor="leave-start">{t("visit.start")}</Label>
      <Input
        id="leave-start"
        type="date"
        value={start}
        onChange={(event) => setStart(event.target.value)}
      />
      <Label htmlFor="leave-end">{t("visit.end")}</Label>
      <Input
        id="leave-end"
        type="date"
        value={end}
        onChange={(event) => setEnd(event.target.value)}
      />
      <Label htmlFor="leave-mode">{t("visit.reasonMode")}</Label>
      <Select
        id="leave-mode"
        value={reasonMode}
        onChange={(event) =>
          setReasonMode(event.target.value as "medical_reasons" | "diagnosis")
        }
      >
        <option value="medical_reasons">{t("visit.medicalReasons")}</option>
        <option value="diagnosis">{t("visit.diagnosis")}</option>
      </Select>
      <Label htmlFor="leave-reason">{t("visit.reasonText")}</Label>
      <Input
        id="leave-reason"
        value={reasonText}
        onChange={(event) => setReasonText(event.target.value)}
      />
      <FormActions pending={pending || !start || !end} onClose={onClose} />
    </form>
  );
}

function CertificateForm({
  pending,
  onSubmit,
  onClose,
}: {
  pending: boolean;
  onSubmit: (body: CertificateInput) => void;
  onClose: () => void;
}) {
  const t = useTranslations("documents");
  const [purpose, setPurpose] =
    useState<CertificateInput["purpose"]>("fitness");
  const [body, setBody] = useState("");
  return (
    <form
      className="space-y-3"
      onSubmit={(event) => {
        event.preventDefault();
        if (body.trim().length === 0) {
          return;
        }
        onSubmit({ purpose, bodyText: body.trim() });
      }}
    >
      <Label htmlFor="certificate-purpose">{t("visit.purpose")}</Label>
      <Select
        id="certificate-purpose"
        value={purpose}
        onChange={(event) =>
          setPurpose(event.target.value as CertificateInput["purpose"])
        }
      >
        {CERTIFICATE_PURPOSES.map((code) => (
          <option key={code} value={code}>
            {purposeLabel(t, code)}
          </option>
        ))}
      </Select>
      <Label htmlFor="certificate-body">{t("visit.statement")}</Label>
      <textarea
        id="certificate-body"
        className={cn(formControlClass, "min-h-28 py-2")}
        value={body}
        onChange={(event) => setBody(event.target.value)}
      />
      <FormActions
        pending={pending || body.trim().length === 0}
        onClose={onClose}
      />
    </form>
  );
}

function TextDocumentForm({
  title,
  fieldLabel,
  showLocale = false,
  pending,
  onSubmit,
  onClose,
}: {
  title: string;
  fieldLabel: string;
  showLocale?: boolean;
  pending: boolean;
  onSubmit: (text: string, locale: "en" | "fr" | "ar" | null) => void;
  onClose: () => void;
}) {
  const t = useTranslations("documents");
  const [text, setText] = useState("");
  const [locale, setLocale] = useState<"" | (typeof DOCUMENT_LOCALES)[number]>(
    "",
  );
  return (
    <form
      className="space-y-3"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(text.trim(), locale === "" ? null : locale);
      }}
    >
      <h3 className="font-medium">{title}</h3>
      {showLocale ? (
        <>
          <Label htmlFor="doc-locale">{t("visit.locale")}</Label>
          <Select
            id="doc-locale"
            value={locale}
            onChange={(event) =>
              setLocale(
                event.target.value as "" | (typeof DOCUMENT_LOCALES)[number],
              )
            }
          >
            <option value="">{t("visit.localeAuto")}</option>
            {DOCUMENT_LOCALES.map((code) => (
              <option key={code} value={code}>
                {localeOptionLabel(t, code)}
              </option>
            ))}
          </Select>
        </>
      ) : null}
      <Label htmlFor="doc-text">{fieldLabel}</Label>
      <textarea
        id="doc-text"
        className={cn(formControlClass, "min-h-28 py-2")}
        value={text}
        onChange={(event) => setText(event.target.value)}
      />
      <FormActions pending={pending} onClose={onClose} />
    </form>
  );
}

function BatchPrint({
  patientId,
  encounterId,
  onClose,
}: {
  patientId: string;
  encounterId: string;
  onClose: () => void;
}) {
  const t = useTranslations("documents");
  const documents = useEncounterDocumentsQuery(patientId, encounterId, true);
  const preview = useBatchPreviewMutation(encounterId);
  const rows = documents.data?.items ?? [];
  const [selected, setSelected] = useState<string[] | null>(null);
  const [html, setHtml] = useState("");
  const chosen = selected ?? rows.map((row) => row.publicId);

  return (
    <div className="space-y-3">
      <h3 className="font-medium">{t("visit.selectDocuments")}</h3>
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("visit.batchEmpty")}</p>
      ) : (
        <ul className="space-y-2" {...testIdProps(testIds.documents.batchList)}>
          {rows.map((row) => (
            <li key={row.publicId}>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={chosen.includes(row.publicId)}
                  onChange={(event) => {
                    const base = selected ?? rows.map((item) => item.publicId);
                    setSelected(
                      event.target.checked
                        ? [...base, row.publicId]
                        : base.filter((id) => id !== row.publicId),
                    );
                  }}
                  {...testIdProps(
                    publicIdTestId("documents.batch-row", row.publicId),
                  )}
                />
                {`${row.title} · ${row.locale}`}
              </label>
            </li>
          ))}
        </ul>
      )}
      <div className="flex gap-2">
        <Button
          type="button"
          disabled={preview.isPending || chosen.length === 0}
          onClick={() => {
            preview.mutate(
              { documentPublicIds: chosen },
              {
                onSuccess: (result) => {
                  setHtml(result.html);
                  const frame = document.createElement("iframe");
                  frame.setAttribute("title", t("visit.preview"));
                  frame.style.position = "fixed";
                  frame.style.width = "0";
                  frame.style.height = "0";
                  frame.srcdoc = result.html;
                  document.body.appendChild(frame);
                  frame.onload = () => {
                    frame.contentWindow?.print();
                    window.setTimeout(() => frame.remove(), 1000);
                  };
                },
              },
            );
          }}
          {...testIdProps(testIds.documents.batchPrint)}
        >
          {t("visit.printBatch")}
        </Button>
        <Button type="button" variant="secondary" onClick={onClose}>
          {t("visit.close")}
        </Button>
      </div>
      {html ? (
        <iframe
          title={t("visit.preview")}
          className="h-96 w-full rounded-lg border border-border bg-card"
          srcDoc={html}
          {...testIdProps(testIds.documents.batchFrame)}
        />
      ) : null}
    </div>
  );
}

function FormActions({
  pending,
  onClose,
}: {
  pending: boolean;
  onClose: () => void;
}) {
  const t = useTranslations("documents");
  return (
    <div className="flex gap-2">
      <Button
        type="submit"
        disabled={pending}
        {...testIdProps(testIds.documents.visitCreate)}
      >
        {t("visit.create")}
      </Button>
      <Button type="button" variant="secondary" onClick={onClose}>
        {t("visit.close")}
      </Button>
    </div>
  );
}

function localeOptionLabel(
  t: ReturnType<typeof useTranslations<"documents">>,
  code: (typeof DOCUMENT_LOCALES)[number],
): string {
  switch (code) {
    case "en":
      return t("locale.en");
    case "fr":
      return t("locale.fr");
    case "ar":
      return t("locale.ar");
  }
}

function panelLabel(
  t: ReturnType<typeof useTranslations<"documents">>,
  code: (typeof LAB_PANELS)[number],
): string {
  switch (code) {
    case "preoperative":
      return t("visit.panels.preoperative");
    case "thyroid_calcitonin":
      return t("visit.panels.thyroid_calcitonin");
    case "allergy_ige":
      return t("visit.panels.allergy_ige");
    case "autoimmune_inner_ear":
      return t("visit.panels.autoimmune_inner_ear");
    case "sudden_hearing_loss_screen":
      return t("visit.panels.sudden_hearing_loss_screen");
    case "ear_discharge_culture":
      return t("visit.panels.ear_discharge_culture");
    case "hpv_status":
      return t("visit.panels.hpv_status");
    case "epistaxis_coagulation":
      return t("visit.panels.epistaxis_coagulation");
  }
}

function purposeLabel(
  t: ReturnType<typeof useTranslations<"documents">>,
  code: CertificateInput["purpose"],
): string {
  switch (code) {
    case "fitness":
      return t("visit.purposes.fitness");
    case "swimming_tubes":
      return t("visit.purposes.swimming_tubes");
    case "air_travel":
      return t("visit.purposes.air_travel");
    case "diving":
      return t("visit.purposes.diving");
    case "voice":
      return t("visit.purposes.voice");
    case "attendance":
      return t("visit.purposes.attendance");
    case "other":
      return t("visit.purposes.other");
  }
}

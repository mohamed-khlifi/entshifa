"use client";

import { useTranslations } from "next-intl";

import type { OtologyDraft } from "../lib/draft";
import { drugLabel, optionLabel } from "../lib/labels";
import type { EarDeviceRead } from "@/lib/api/generated";
import { testIdProps, testIds } from "@/lib/test/test-id";

type OtologyProcedureFormProps = {
  draft: OtologyDraft;
  devices: readonly EarDeviceRead[];
  readOnly: boolean;
  onChange: (draft: OtologyDraft) => void;
};

const selectClass =
  "flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm";

export function OtologyProcedureForm({
  draft,
  devices,
  readOnly,
  onChange,
}: OtologyProcedureFormProps) {
  const t = useTranslations("otology");
  const set = (patch: Partial<OtologyDraft>) =>
    onChange({ ...draft, ...patch });

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <label className="space-y-1 text-sm md:col-span-2">
        {t("fields.procedure")}
        <select
          className={selectClass}
          disabled={readOnly}
          value={draft.subtype}
          onChange={(event) =>
            set({ subtype: event.target.value as OtologyDraft["subtype"] })
          }
          {...testIdProps(testIds.otology.subtype)}
        >
          {(
            [
              "none",
              "wax_removal",
              "foreign_body",
              "wick",
              "tube_insertion",
              "tube_removal",
              "intratympanic_injection",
              "cavity_cleaning",
            ] as const
          ).map((value) => (
            <option key={value} value={value}>
              {optionLabel(t, "subtype", value)}
            </option>
          ))}
        </select>
      </label>
      {draft.subtype === "wax_removal" ? (
        <>
          <Choice
            label={t("fields.procedure")}
            value={draft.waxMethod}
            options={["microsuction", "curette", "irrigation"]}
            group="waxMethod"
            disabled={readOnly}
            onChange={(waxMethod) =>
              set({ waxMethod: waxMethod as OtologyDraft["waxMethod"] })
            }
          />
          <Choice
            label={t("completeness.complete")}
            value={draft.completeness}
            options={["complete", "partial"]}
            group="completeness"
            disabled={readOnly}
            onChange={(completeness) =>
              set({
                completeness: completeness as OtologyDraft["completeness"],
              })
            }
          />
          <Choice
            label={t("canal.clear")}
            value={draft.canalCondition}
            options={["clear", "residual_wax", "inflamed", "traumatized"]}
            group="canal"
            disabled={readOnly}
            onChange={(canalCondition) =>
              set({
                canalCondition:
                  canalCondition as OtologyDraft["canalCondition"],
              })
            }
          />
        </>
      ) : null}
      {draft.subtype === "foreign_body" ? (
        <>
          <label className="space-y-1 text-sm md:col-span-2">
            {t("fields.object")}
            <input
              className={selectClass}
              disabled={readOnly}
              value={draft.objectText}
              onChange={(event) => set({ objectText: event.target.value })}
            />
          </label>
          <Choice
            label={t("fields.procedure")}
            value={draft.foreignBodyMethod}
            options={["microsuction", "forceps", "irrigation", "hook"]}
            group="fbMethod"
            disabled={readOnly}
            onChange={(foreignBodyMethod) =>
              set({
                foreignBodyMethod:
                  foreignBodyMethod as OtologyDraft["foreignBodyMethod"],
              })
            }
          />
          <Choice
            label={t("trauma.none")}
            value={draft.trauma}
            options={["none", "canal", "tympanic"]}
            group="trauma"
            disabled={readOnly}
            onChange={(trauma) =>
              set({ trauma: trauma as OtologyDraft["trauma"] })
            }
          />
        </>
      ) : null}
      {draft.subtype === "wick" ? (
        <Choice
          label={t("wickType.pope")}
          value={draft.wickType}
          options={["pope", "ribbon", "merocel"]}
          group="wickType"
          disabled={readOnly}
          onChange={(wickType) =>
            set({ wickType: wickType as OtologyDraft["wickType"] })
          }
        />
      ) : null}
      {draft.subtype === "tube_insertion" ? (
        <>
          <Choice
            label={t("tubeModel.shepard")}
            value={draft.tubeModel}
            options={["shepard", "armstrong", "t_tube", "bobbin", "paparella"]}
            group="tubeModel"
            disabled={readOnly}
            onChange={(tubeModel) =>
              set({ tubeModel: tubeModel as OtologyDraft["tubeModel"] })
            }
          />
          <Choice
            label={t("effusion.none")}
            value={draft.effusion}
            options={["none", "serous", "mucoid", "purulent", "bloody"]}
            group="effusion"
            disabled={readOnly}
            onChange={(effusion) =>
              set({ effusion: effusion as OtologyDraft["effusion"] })
            }
          />
          <Choice
            label={t("complication.none")}
            value={draft.complication}
            options={["", "bleeding", "otorrhea", "vertigo", "perforation"]}
            group="complication"
            disabled={readOnly}
            onChange={(complication) =>
              set({
                complication: complication as OtologyDraft["complication"],
              })
            }
          />
        </>
      ) : null}
      {draft.subtype === "tube_removal" ? (
        <label className="space-y-1 text-sm md:col-span-2">
          {t("fields.device")}
          <select
            className={selectClass}
            disabled={readOnly}
            value={draft.devicePublicId}
            onChange={(event) => set({ devicePublicId: event.target.value })}
          >
            <option value="">{t("devicesEmpty")}</option>
            {devices.map((device) => (
              <option key={device.publicId} value={device.publicId}>
                {optionLabel(t, "deviceType", device.deviceType)}{" "}
                {optionLabel(t, "laterality", device.laterality)}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      {draft.subtype === "intratympanic_injection" ? (
        <>
          <label className="space-y-1 text-sm">
            {t("fields.procedure")}
            <select
              className={selectClass}
              disabled={readOnly}
              value={draft.drugCode}
              onChange={(event) =>
                set({
                  drugCode: event.target.value as OtologyDraft["drugCode"],
                })
              }
            >
              {(
                [
                  "DRUG.IT.DEXAMETHASONE",
                  "DRUG.IT.METHYLPREDNISOLONE",
                  "DRUG.IT.GENTAMICIN",
                ] as const
              ).map((code) => (
                <option key={code} value={code}>
                  {drugLabel(t, code)}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1 text-sm">
            {t("fields.dose")}
            <input
              className={selectClass}
              disabled={readOnly}
              inputMode="decimal"
              value={draft.doseAmount}
              onChange={(event) => set({ doseAmount: event.target.value })}
            />
          </label>
          <Choice
            label={t("fields.unit")}
            value={draft.doseUnit}
            options={["mg", "mL"]}
            group="unit"
            disabled={readOnly}
            onChange={(doseUnit) =>
              set({ doseUnit: doseUnit as OtologyDraft["doseUnit"] })
            }
          />
          <label className="space-y-1 text-sm">
            {t("fields.indication")}
            <input
              className={selectClass}
              disabled={readOnly}
              value={draft.indicationText}
              onChange={(event) => set({ indicationText: event.target.value })}
            />
          </label>
        </>
      ) : null}
      {draft.subtype === "cavity_cleaning" ? (
        <Choice
          label={t("cavity.dry")}
          value={draft.cavityCondition}
          options={[
            "dry",
            "moist",
            "granulation",
            "debris",
            "exposed_structures",
          ]}
          group="cavity"
          disabled={readOnly}
          onChange={(cavityCondition) =>
            set({
              cavityCondition:
                cavityCondition as OtologyDraft["cavityCondition"],
            })
          }
        />
      ) : null}
      {draft.removalDueDate ? (
        <p className="text-sm text-muted-foreground md:col-span-2">
          {t("removalDue", { date: draft.removalDueDate })}
        </p>
      ) : null}
    </div>
  );
}

function Choice({
  label,
  value,
  options,
  group,
  disabled,
  onChange,
}: {
  label: string;
  value: string;
  options: readonly string[];
  group: string;
  disabled: boolean;
  onChange: (value: string) => void;
}) {
  const t = useTranslations("otology");
  return (
    <label className="space-y-1 text-sm">
      {label}
      <select
        className={selectClass}
        disabled={disabled}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option || "none"} value={option}>
            {group === "unit" ? option : optionLabel(t, group, option)}
          </option>
        ))}
      </select>
    </label>
  );
}

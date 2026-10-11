"use client";

import { useLocale, useTranslations } from "next-intl";

import {
  LK_ITEM_CHOICES,
  LK_ITEMS,
  polypGradeChoices,
  type EndoscopyDraft,
  type PolypScaleName,
  withLkItem,
} from "../lib/draft";
import { lkItemLabel, polypScaleLabel, scoreCodeLabel } from "../lib/labels";
import type { EndoscopyExamRead } from "@/lib/api/generated";
import { MEDICAL_UNITS, formatNumber, formatQuantity } from "@/lib/i18n/format";
import {
  endoscopyLkTestId,
  endoscopyPolypTestId,
  testIdProps,
  testIds,
} from "@/lib/test/test-id";

type EndoscopyScorePanelProps = {
  draft: EndoscopyDraft;
  scale: PolypScaleName | null;
  saved: EndoscopyExamRead | null;
  readOnly: boolean;
  onChange: (draft: EndoscopyDraft) => void;
};

export function EndoscopyScorePanel({
  draft,
  scale,
  saved,
  readOnly,
  onChange,
}: EndoscopyScorePanelProps) {
  const t = useTranslations("endoscopy");
  const locale = useLocale();
  const grades = scale ? polypGradeChoices(scale) : [];

  return (
    <section className="space-y-4" {...testIdProps(testIds.endoscopy.scores)}>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold">{t("scores.title")}</h3>
        <p className="text-xs text-muted-foreground">
          {polypScaleLabel(t, scale ?? "")}
        </p>
      </div>
      {(["right", "left"] as const).map((side) => (
        <div key={side} className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {LK_ITEMS.map((item) => (
            <GradeSelect
              key={`${side}-${item}`}
              label={t("scores.sideItem", {
                item: lkItemLabel(t, item),
                side: side === "right" ? t("scores.right") : t("scores.left"),
              })}
              testId={endoscopyLkTestId(side, item)}
              value={
                draft[
                  side === "right" ? "lundKennedyRight" : "lundKennedyLeft"
                ][item]
              }
              choices={LK_ITEM_CHOICES}
              disabled={readOnly}
              onChange={(value) => {
                if (value === null) {
                  return;
                }
                onChange(withLkItem(draft, side, item, value));
              }}
            />
          ))}
        </div>
      ))}
      <div className="grid gap-2 sm:grid-cols-3">
        <GradeSelect
          label={t("scores.sideItem", {
            item: t("scores.polypGrade"),
            side: t("scores.right"),
          })}
          testId={endoscopyPolypTestId("right")}
          value={draft.polypGradeRight}
          choices={grades}
          allowEmpty
          disabled={readOnly}
          onChange={(value) => onChange({ ...draft, polypGradeRight: value })}
        />
        <GradeSelect
          label={t("scores.sideItem", {
            item: t("scores.polypGrade"),
            side: t("scores.left"),
          })}
          testId={endoscopyPolypTestId("left")}
          value={draft.polypGradeLeft}
          choices={grades}
          allowEmpty
          disabled={readOnly}
          onChange={(value) => onChange({ ...draft, polypGradeLeft: value })}
        />
        <label className="space-y-1 text-xs text-muted-foreground">
          {t("scores.adenoid")}
          <input
            inputMode="numeric"
            className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm text-foreground"
            disabled={readOnly}
            value={draft.adenoidObstructionPct ?? ""}
            {...testIdProps(testIds.endoscopy.adenoid)}
            onChange={(event) => {
              const text = event.target.value.trim();
              if (text !== "" && !/^\d{1,3}$/.test(text)) {
                return;
              }
              onChange({
                ...draft,
                adenoidObstructionPct: text === "" ? null : Number(text),
              });
            }}
          />
        </label>
      </div>
      {saved ? (
        <dl className="grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">{t("scores.lundKennedy")}</dt>
            <dd>{formatNumber(saved.lundKennedyTotal, locale)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("scores.modified")}</dt>
            <dd>{formatNumber(saved.modifiedLkTotal, locale)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("scores.polypGrade")}</dt>
            <dd>
              {saved.polypGradeRight === null || saved.polypGradeLeft === null
                ? t("scores.notRecorded")
                : t("scores.pair", {
                    right: formatNumber(saved.polypGradeRight, locale),
                    left: formatNumber(saved.polypGradeLeft, locale),
                  })}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("scores.adenoid")}</dt>
            <dd>
              {saved.adenoidObstructionPct === null
                ? t("scores.notRecorded")
                : formatQuantity(
                    saved.adenoidObstructionPct,
                    MEDICAL_UNITS.percent,
                    locale,
                    0,
                  )}
            </dd>
          </div>
          {saved.scores.map((score) => (
            <div key={score.code} className="sm:col-span-2">
              <dt className="text-muted-foreground">
                {scoreCodeLabel(t, score.code)}
              </dt>
              <dd>
                <span>{score.value}</span>
                {score.unit ? <span className="ms-1">{score.unit}</span> : null}
              </dd>
              <dd className="text-xs text-muted-foreground">
                {score.reference}
              </dd>
            </div>
          ))}
        </dl>
      ) : (
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.endoscopy.scorePending)}
        >
          {t("scores.pending")}
        </p>
      )}
    </section>
  );
}

function GradeSelect({
  label,
  testId,
  value,
  choices,
  allowEmpty = false,
  disabled,
  onChange,
}: {
  label: string;
  testId: string;
  value: number | null;
  choices: readonly number[];
  allowEmpty?: boolean;
  disabled: boolean;
  onChange: (value: number | null) => void;
}) {
  const t = useTranslations("endoscopy");
  return (
    <label className="space-y-1 text-xs text-muted-foreground">
      {label}
      <select
        className="flex h-10 w-full rounded-lg border border-input bg-card px-2 text-sm text-foreground"
        disabled={disabled}
        value={value ?? ""}
        onChange={(event) => {
          if (event.target.value === "") {
            onChange(null);
            return;
          }
          onChange(Number(event.target.value));
        }}
        {...testIdProps(testId)}
      >
        {allowEmpty ? (
          <option value="">{t("scores.notRecorded")}</option>
        ) : null}
        {!allowEmpty && value === null ? (
          <option value="">{t("scores.notRecorded")}</option>
        ) : null}
        {choices.map((choice) => (
          <option key={choice} value={choice}>
            {choice}
          </option>
        ))}
      </select>
    </label>
  );
}

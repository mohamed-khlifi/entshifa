import type { useTranslations } from "next-intl";

type TQuestionnaires = ReturnType<typeof useTranslations<"questionnaires">>;

const SEVERITY_LABEL_KEYS = {
  abnormal: "severityBands.abnormal",
  catastrophic: "severityBands.catastrophic",
  extreme: "severityBands.extreme",
  high: "severityBands.high",
  intermediate: "severityBands.intermediate",
  low: "severityBands.low",
  mild: "severityBands.mild",
  moderate: "severityBands.moderate",
  none: "severityBands.none",
  normal: "severityBands.normal",
  severe: "severityBands.severe",
  slight: "severityBands.slight",
} as const;

const SUBSCALE_LABEL_KEYS = {
  caregiver_concerns: "subscales.caregiver_concerns",
  daytime_problems: "subscales.daytime_problems",
  ear_facial: "subscales.ear_facial",
  emotional: "subscales.emotional",
  emotional_distress: "subscales.emotional_distress",
  extranasal: "subscales.extranasal",
  functional: "subscales.functional",
  physical: "subscales.physical",
  physical_suffering: "subscales.physical_suffering",
  psychological: "subscales.psychological",
  rhinologic: "subscales.rhinologic",
  sleep: "subscales.sleep",
  sleep_disturbance: "subscales.sleep_disturbance",
} as const;

const TREATMENT_EVENT_LABEL_KEYS = {
  prescription: "presentation.events.prescription",
  procedure: "presentation.events.procedure",
  post_op: "presentation.events.post_op",
} as const;

type SeverityCode = keyof typeof SEVERITY_LABEL_KEYS;
type SubscaleCode = keyof typeof SUBSCALE_LABEL_KEYS;
type TreatmentEvent = keyof typeof TREATMENT_EVENT_LABEL_KEYS;

export function severityBandLabel(
  t: TQuestionnaires,
  code: string | null | undefined,
): string | null {
  if (!code) {
    return null;
  }
  const key = SEVERITY_LABEL_KEYS[code as SeverityCode];
  if (!key) {
    return code;
  }
  return t(key);
}

export function subscaleLabel(t: TQuestionnaires, code: string): string {
  const key = SUBSCALE_LABEL_KEYS[code as SubscaleCode];
  if (!key) {
    return code;
  }
  return t(key);
}

export function treatmentEventLabel(
  t: TQuestionnaires,
  eventType: string,
): string | null {
  const key = TREATMENT_EVENT_LABEL_KEYS[eventType as TreatmentEvent];
  if (!key) {
    return null;
  }
  return t(key);
}

export function isTreatmentTimelineEvent(eventType: string): boolean {
  return eventType in TREATMENT_EVENT_LABEL_KEYS;
}

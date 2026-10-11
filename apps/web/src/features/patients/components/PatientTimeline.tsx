"use client";

import { useLocale, useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { formControlClass } from "@/components/ui/form-control";
import type { PatientTimelineItemRead } from "@/lib/api/generated";
import { formatDate } from "@/lib/i18n/format";
import { Link, usePathname, useRouter } from "@/lib/i18n/navigation";
import { conceptDisplayText } from "@/features/patients/lib/concept-display";
import { testIdProps, testIds, timelineRowTestId } from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

import { usePatientQuery } from "../hooks/use-patient-queries";
import {
  usePatientTimelineInfinite,
  useTimelinePrint,
  type TimelineFilters,
} from "../hooks/use-patient-timeline";
import { timelineHref } from "../lib/timeline-href";
import {
  timelineEventLabel,
  timelineLateralityLabel,
  timelineStatusLabel,
} from "../lib/timeline-labels";
import { TIMELINE_ROW_HEIGHT, timelineWindow } from "../lib/timeline-window";

const EVENT_TYPES = [
  "consultation",
  "follow_up",
  "procedure",
  "post_op",
  "result_review",
  "teleconsultation",
  "diagnosis",
  "prescription",
  "document",
  "appointment",
  "no_show",
  "attachment",
  "recall",
  "phone_call",
  "recall_sent",
] as const;

const SIDES = ["right", "left", "bilateral", "midline", "na"] as const;

function filtersFrom(params: URLSearchParams): TimelineFilters {
  return {
    type: params.get("type") ?? "",
    laterality: params.get("laterality") ?? "",
    problemId: params.get("problem") ?? "",
  };
}

function rowDetail(item: PatientTimelineItemRead): string {
  const concept = conceptDisplayText(item.concept);
  if (concept) {
    return concept;
  }
  return item.detailText?.trim() ?? "";
}

export function PatientTimeline({ patientId }: { patientId: string }) {
  const t = useTranslations("patients");
  const locale = useLocale();
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const filters = filtersFrom(searchParams);
  const patient = usePatientQuery(patientId);
  const timeline = usePatientTimelineInfinite(patientId, filters);
  const printHistory = useTimelinePrint();
  const scroller = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(480);
  const [printing, setPrinting] = useState(false);
  const [printItems, setPrintItems] = useState<PatientTimelineItemRead[]>([]);

  const items = useMemo(
    () => timeline.data?.pages.flatMap((page) => page.items) ?? [],
    [timeline.data],
  );
  const { hasNextPage, isFetchingNextPage, fetchNextPage } = timeline;
  const range = timelineWindow(scrollTop, viewportHeight, items.length);

  useEffect(() => {
    const node = scroller.current;
    if (!node) {
      return;
    }
    const onScroll = () => setScrollTop(node.scrollTop);
    node.addEventListener("scroll", onScroll, { passive: true });
    const observer = new ResizeObserver(() =>
      setViewportHeight(node.clientHeight),
    );
    observer.observe(node);
    setViewportHeight(node.clientHeight);
    return () => {
      node.removeEventListener("scroll", onScroll);
      observer.disconnect();
    };
  }, [timeline.isLoading]);

  useEffect(() => {
    if (range.end >= items.length - 8 && hasNextPage && !isFetchingNextPage) {
      void fetchNextPage();
    }
  }, [fetchNextPage, hasNextPage, isFetchingNextPage, items.length, range.end]);

  const setFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    const text = params.toString();
    router.replace(text ? `${pathname}?${text}` : pathname);
  };

  return (
    <section className="space-y-4" {...testIdProps(testIds.patients.timeline)}>
      <style>{`@media print { body * { visibility: hidden !important; } .patient-timeline-print, .patient-timeline-print * { visibility: visible !important; } .patient-timeline-print { position: absolute; inset: 0; background: white; } }`}</style>
      <div className="flex flex-wrap items-end gap-3 print:hidden">
        <div>
          <Label>{t("timeline.filters.type")}</Label>
          <Select
            className={cn(formControlClass, "w-52")}
            value={filters.type ?? ""}
            onChange={(event) => setFilter("type", event.target.value)}
            {...testIdProps(testIds.patients.timelineType)}
          >
            <option value="">{t("timeline.filters.allTypes")}</option>
            {EVENT_TYPES.map((eventType) => (
              <option key={eventType} value={eventType}>
                {timelineEventLabel(t, eventType)}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>{t("timeline.filters.laterality")}</Label>
          <Select
            className={cn(formControlClass, "w-44")}
            value={filters.laterality ?? ""}
            onChange={(event) => setFilter("laterality", event.target.value)}
            {...testIdProps(testIds.patients.timelineLaterality)}
          >
            <option value="">{t("timeline.filters.allSides")}</option>
            {SIDES.map((side) => (
              <option key={side} value={side}>
                {timelineLateralityLabel(t, side)}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>{t("timeline.filters.problem")}</Label>
          <Select
            className={cn(formControlClass, "w-64")}
            value={filters.problemId ?? ""}
            onChange={(event) => setFilter("problem", event.target.value)}
            {...testIdProps(testIds.patients.timelineProblem)}
          >
            <option value="">{t("timeline.filters.allProblems")}</option>
            {(patient.data?.problems ?? []).map((problem) => (
              <option key={problem.publicId} value={problem.publicId}>
                {conceptDisplayText(problem.diagnosis)}
              </option>
            ))}
          </Select>
        </div>
        <Button
          type="button"
          variant="secondary"
          disabled={printing}
          onClick={() => {
            setPrinting(true);
            void printHistory(patientId, filters)
              .then((page) => {
                setPrintItems(page?.items ?? []);
                requestAnimationFrame(() => window.print());
              })
              .finally(() => setPrinting(false));
          }}
          {...testIdProps(testIds.patients.timelinePrint)}
        >
          {printing ? t("timeline.printing") : t("timeline.print")}
        </Button>
      </div>
      {timeline.isLoading ? (
        <p className="text-sm text-muted-foreground">{t("timeline.loading")}</p>
      ) : null}
      {timeline.isError ? (
        <p
          className="text-sm text-destructive"
          {...testIdProps(testIds.patients.timelineError)}
        >
          {t("timeline.error")}
        </p>
      ) : null}
      {!timeline.isLoading && !timeline.isError && items.length === 0 ? (
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.patients.timelineEmpty)}
        >
          {t("timeline.empty")}
        </p>
      ) : null}
      <div
        ref={scroller}
        className="max-h-[32rem] overflow-y-auto rounded-xl border border-border print:hidden"
        {...testIdProps(testIds.patients.timelineList)}
      >
        <div style={{ height: range.paddingTop }} />
        <ul>
          {items.slice(range.start, range.end).map((item) => {
            const detail = rowDetail(item);
            const side = item.laterality
              ? timelineLateralityLabel(t, item.laterality)
              : "";
            return (
              <li
                key={`${item.eventType}-${item.publicId}`}
                style={{ height: TIMELINE_ROW_HEIGHT }}
              >
                <Link
                  href={timelineHref(patientId, item)}
                  className="flex h-full items-center justify-between gap-3 px-4 hover:bg-muted"
                  {...testIdProps(timelineRowTestId(item.publicId))}
                >
                  <span className="min-w-0">
                    <span className="block text-sm font-medium">
                      {timelineEventLabel(t, item.eventType)}
                      {detail ? ` · ${detail}` : ""}
                    </span>
                    <span className="block truncate text-xs text-muted-foreground">
                      {timelineStatusLabel(t, item.status)}
                      {side ? ` · ${side}` : ""}
                    </span>
                  </span>
                  <time
                    className="shrink-0 text-xs text-muted-foreground"
                    dateTime={item.occurredAt}
                  >
                    {formatDate(item.occurredAt, locale)}
                  </time>
                </Link>
              </li>
            );
          })}
        </ul>
        <div style={{ height: range.paddingBottom }} />
      </div>
      <article
        className="patient-timeline-print hidden"
        {...testIdProps(testIds.patients.timelinePrintSheet)}
      >
        <h1 className="text-lg font-semibold">{t("timeline.title")}</h1>
        <ol className="mt-4 space-y-2">
          {printItems.map((item) => (
            <li key={`${item.eventType}-${item.publicId}`} className="text-sm">
              {formatDate(item.occurredAt, locale)}
              {" · "}
              {timelineEventLabel(t, item.eventType)}
              {rowDetail(item) ? ` · ${rowDetail(item)}` : ""}
              {" · "}
              {timelineStatusLabel(t, item.status)}
            </li>
          ))}
        </ol>
      </article>
    </section>
  );
}

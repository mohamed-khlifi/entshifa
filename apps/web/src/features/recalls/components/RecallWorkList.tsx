"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useLocale, useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { DataTable } from "@/components/data/DataTable";
import { Button } from "@/components/ui/button";
import type { RecallRead } from "@/lib/api/generated";
import { formatDate } from "@/lib/i18n/format";
import { Link, usePathname, useRouter } from "@/lib/i18n/navigation";
import { Permission } from "@/lib/permissions";
import { recallRowTestId, testIdProps, testIds } from "@/lib/test/test-id";
import { usePermission } from "@/providers/permission-provider";

import { RecallComposer } from "./RecallComposer";
import { RecallRowActions } from "./RecallRowActions";
import {
  useCancelRecallMutation,
  useLogRecallActionMutation,
  useRecallListQuery,
  useRecallSummaryQuery,
} from "../hooks/use-recall-queries";
import { recallBucketLabel, recallStatusLabel } from "../lib/labels";
import { recallReasonLabel } from "../lib/reason-label";

const BUCKETS = ["overdue", "upcoming", "unreachable", "active"] as const;

type Bucket = (typeof BUCKETS)[number];

function isBucket(value: string | null): value is Bucket {
  return (
    value === "overdue" ||
    value === "upcoming" ||
    value === "unreachable" ||
    value === "active"
  );
}

export function RecallWorkList() {
  const t = useTranslations("recalls");
  const locale = useLocale();
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const canWrite = usePermission(Permission.RECALL_WRITE);
  const summary = useRecallSummaryQuery();
  const bucket: Bucket = isBucket(searchParams.get("bucket"))
    ? (searchParams.get("bucket") as Bucket)
    : "overdue";
  const page = Math.max(1, Number(searchParams.get("page") ?? "1") || 1);
  const pageSize = Math.max(
    1,
    Math.min(100, Number(searchParams.get("pageSize") ?? "20") || 20),
  );
  const list = useRecallListQuery({
    bucket,
    limit: pageSize,
    offset: (page - 1) * pageSize,
  });
  const logAction = useLogRecallActionMutation();
  const cancel = useCancelRecallMutation();
  const [creating, setCreating] = useState(false);
  const [booking, setBooking] = useState<RecallRead | null>(null);
  const [cancelTarget, setCancelTarget] = useState<RecallRead | null>(null);
  const [cancelReason, setCancelReason] = useState("");

  const setBucket = (next: Bucket) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("bucket", next);
    params.set("page", "1");
    router.replace(`${pathname}?${params.toString()}`);
  };

  const columns = useMemo<ColumnDef<RecallRead>[]>(
    () => [
      {
        id: "patient",
        header: t("columns.patient"),
        cell: ({ row }) => (
          <Link
            href={`/patients/${row.original.patientId}`}
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            {row.original.patientDisplayName}
          </Link>
        ),
      },
      {
        id: "reason",
        header: t("columns.reason"),
        cell: ({ row }) =>
          recallReasonLabel(t, row.original.reasonKey, row.original.reasonText),
      },
      {
        id: "due",
        header: t("columns.due"),
        cell: ({ row }) => formatDate(row.original.dueOn, locale),
      },
      {
        id: "status",
        header: t("columns.status"),
        cell: ({ row }) => recallStatusLabel(t, row.original.status),
      },
      {
        id: "attempts",
        header: t("columns.attempts"),
        cell: ({ row }) => (
          <span>
            {t("attempts", { count: row.original.attempts })}
            {row.original.overlapCount > 0
              ? ` · ${t("overlap", { count: row.original.overlapCount })}`
              : ""}
          </span>
        ),
      },
      {
        id: "actions",
        header: t("columns.actions"),
        cell: ({ row }) =>
          canWrite ? (
            <RecallRowActions
              recall={row.original}
              disabled={logAction.isPending || cancel.isPending}
              onContact={(recall, action) =>
                logAction.mutate({
                  recallId: recall.publicId,
                  body: { action, version: recall.version },
                })
              }
              onUnreachable={(recall) =>
                logAction.mutate({
                  recallId: recall.publicId,
                  body: {
                    action: "call",
                    outcome: "unreachable",
                    version: recall.version,
                  },
                })
              }
              onBook={setBooking}
              onCancel={setCancelTarget}
            />
          ) : null,
      },
    ],
    [canWrite, cancel.isPending, locale, logAction, t],
  );

  const counts = summary.data;

  return (
    <div className="space-y-4" {...testIdProps(testIds.recalls.list)}>
      <div
        className="grid gap-2 sm:grid-cols-4"
        {...testIdProps(testIds.recalls.counters)}
      >
        {BUCKETS.map((name) => (
          <button
            key={name}
            type="button"
            className="rounded-xl border border-border px-3 py-3 text-start"
            onClick={() => setBucket(name)}
            {...testIdProps(
              name === "overdue"
                ? testIds.recalls.counterOverdue
                : name === "upcoming"
                  ? testIds.recalls.counterUpcoming
                  : name === "unreachable"
                    ? testIds.recalls.counterUnreachable
                    : testIds.recalls.counterActive,
            )}
          >
            <span className="block text-xs text-muted-foreground">
              {name === "overdue"
                ? t("counters.overdue")
                : name === "upcoming"
                  ? t("counters.upcoming")
                  : name === "unreachable"
                    ? t("counters.unreachable")
                    : t("counters.active")}
            </span>
            <span className="text-2xl font-semibold">
              {counts
                ? name === "overdue"
                  ? counts.overdue
                  : name === "upcoming"
                    ? counts.upcoming
                    : name === "unreachable"
                      ? counts.unreachable
                      : counts.active
                : ""}
            </span>
            <span className="sr-only">{recallBucketLabel(t, name)}</span>
          </button>
        ))}
      </div>
      {canWrite ? (
        <Button
          type="button"
          onClick={() => setCreating(true)}
          {...testIdProps(testIds.recalls.create)}
        >
          {t("page.create")}
        </Button>
      ) : null}
      {list.isLoading ? (
        <p className="text-sm text-muted-foreground">{t("state.loading")}</p>
      ) : null}
      <DataTable
        columns={columns}
        data={list.data?.items ?? []}
        totalItems={list.data?.page.total ?? 0}
        getRowId={(row) => row.publicId}
        getRowTestId={recallRowTestId}
        isLoading={list.isLoading}
        isError={list.isError}
        errorMessage={t("state.error")}
        emptyTitle={t("state.empty")}
      />
      {creating ? (
        <RecallComposer
          heading={t("dialog.createTitle")}
          onClose={() => setCreating(false)}
        />
      ) : null}
      {booking ? (
        <RecallComposer
          heading={t("dialog.bookTitle")}
          recall={booking}
          patientId={booking.patientId}
          onClose={() => setBooking(null)}
        />
      ) : null}
      {cancelTarget ? (
        <div className="flex flex-wrap items-center gap-2">
          <input
            className="h-10 rounded-lg border border-input px-3 text-sm"
            value={cancelReason}
            onChange={(event) => setCancelReason(event.target.value)}
            aria-label={t("form.reason")}
          />
          <Button
            type="button"
            variant="destructive"
            disabled={cancelReason.trim().length === 0}
            onClick={() => {
              cancel.mutate(
                {
                  recallId: cancelTarget.publicId,
                  body: {
                    reason: cancelReason.trim(),
                    version: cancelTarget.version,
                  },
                },
                {
                  onSuccess: () => {
                    setCancelTarget(null);
                    setCancelReason("");
                  },
                },
              );
            }}
          >
            {t("actions.cancel")}
          </Button>
        </div>
      ) : null}
    </div>
  );
}

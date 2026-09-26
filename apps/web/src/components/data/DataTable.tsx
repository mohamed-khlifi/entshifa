"use client";

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
  type RowSelectionState,
  type VisibilityState,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { useTranslations } from "next-intl";
import { useMemo, useState, type ReactNode } from "react";

import { EmptyState } from "@/components/data/EmptyState";
import { FilterBar } from "@/components/data/FilterBar";
import { Pagination } from "@/components/data/Pagination";
import {
  useTableUrlState,
  type TableSortDir,
} from "@/components/data/useTableUrlState";
import { Button } from "@/components/ui/button";
import { columnTestId, tableRowTestId } from "@/lib/forms/field-test-id";
import { cn } from "@/lib/utils/cn";
import { testIdProps, testIds } from "@/lib/test/test-id";

export type DataTableColumnMeta = {
  /** Hide from column visibility toggle when false. */
  enableHiding?: boolean;
};

export type DataTableProps<TData> = {
  /** Column defs from TanStack Table; value type is erased at the table shell. */
  columns: ColumnDef<TData>[];
  data: TData[];
  totalItems: number;
  getRowId: (row: TData) => string;
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  enableRowSelection?: boolean;
  toolbar?: ReactNode;
  className?: string;
  defaultSortBy?: string;
  defaultSortDir?: TableSortDir;
  defaultPageSize?: number;
};

function SortIcon({ active, dir }: { active: boolean; dir: TableSortDir }) {
  if (!active) {
    return <ArrowUpDown className="size-3.5 opacity-50" aria-hidden />;
  }
  return dir === "asc" ? (
    <ArrowUp className="size-3.5" aria-hidden />
  ) : (
    <ArrowDown className="size-3.5" aria-hidden />
  );
}

export function DataTable<TData>({
  columns,
  data,
  totalItems,
  getRowId,
  isLoading = false,
  isError = false,
  errorMessage,
  emptyTitle,
  emptyDescription,
  enableRowSelection = false,
  toolbar,
  className,
  defaultSortBy,
  defaultSortDir = "asc",
  defaultPageSize = 20,
}: DataTableProps<TData>) {
  const t = useTranslations("data");
  const { state, setState } = useTableUrlState({
    defaultPageSize,
    defaultSortBy,
    defaultSortDir,
  });
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});

  const columnVisibility = useMemo<VisibilityState>(() => {
    const visibility: VisibilityState = {};
    for (const [id, visible] of Object.entries(state.visibility)) {
      visibility[id] = visible;
    }
    return visibility;
  }, [state.visibility]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getRowId: (row) => getRowId(row),
    manualPagination: true,
    manualSorting: true,
    pageCount: Math.max(1, Math.ceil(totalItems / state.pageSize)),
    state: {
      columnVisibility,
      rowSelection,
      sorting: state.sortBy
        ? [{ id: state.sortBy, desc: state.sortDir === "desc" }]
        : [],
      pagination: {
        pageIndex: state.page - 1,
        pageSize: state.pageSize,
      },
    },
    enableRowSelection,
    onRowSelectionChange: setRowSelection,
    onColumnVisibilityChange: (updater) => {
      const next =
        typeof updater === "function" ? updater(columnVisibility) : updater;
      const visibility: Record<string, boolean> = {};
      for (const [id, visible] of Object.entries(next)) {
        if (visible === false) {
          visibility[id] = false;
        }
      }
      setState({ visibility, page: 1 });
    },
    onSortingChange: (updater) => {
      const current = state.sortBy
        ? [{ id: state.sortBy, desc: state.sortDir === "desc" }]
        : [];
      const next = typeof updater === "function" ? updater(current) : updater;
      const first = next[0];
      if (!first) {
        setState({ sortBy: null, page: 1 });
        return;
      }
      setState({
        sortBy: first.id,
        sortDir: first.desc ? "desc" : "asc",
        page: 1,
      });
    },
  });

  const hideableColumns = table
    .getAllColumns()
    .filter((column) => column.getCanHide() && column.id !== "select");

  return (
    <div
      className={cn("space-y-4", className)}
      {...testIdProps(testIds.data.table)}
    >
      <div className="flex flex-wrap items-end justify-between gap-3">
        <FilterBar value={state.q} onChange={(q) => setState({ q, page: 1 })} />
        <div className="flex flex-wrap items-center gap-2">
          {hideableColumns.length > 0 ? (
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>{t("columns.label")}</span>
              <select
                className="h-9 rounded-lg border border-input bg-card px-2 text-sm"
                value=""
                onChange={(event) => {
                  const id = event.target.value;
                  if (!id) {
                    return;
                  }
                  const column = table.getColumn(id);
                  column?.toggleVisibility(!column.getIsVisible());
                }}
                {...testIdProps(testIds.data.columnVisibility)}
              >
                <option value="" disabled>
                  {t("columns.toggle")}
                </option>
                {hideableColumns.map((column) => (
                  <option key={column.id} value={column.id}>
                    {column.getIsVisible()
                      ? t("columns.hide", { id: column.id })
                      : t("columns.show", { id: column.id })}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          {toolbar}
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-[var(--shadow-soft)]">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[40rem] border-collapse text-sm">
            <thead className="sticky top-0 z-10 border-b border-border bg-muted/80 backdrop-blur">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    const canSort = header.column.getCanSort();
                    const sorted = header.column.getIsSorted();
                    return (
                      <th
                        key={header.id}
                        className="px-4 py-3 text-start text-xs font-semibold uppercase tracking-wide text-muted-foreground"
                        {...testIdProps(columnTestId(header.column.id))}
                      >
                        {header.isPlaceholder ? null : canSort ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="-ms-2 h-8 gap-1.5 px-2 font-semibold uppercase"
                            onClick={header.column.getToggleSortingHandler()}
                          >
                            {flexRender(
                              header.column.columnDef.header,
                              header.getContext(),
                            )}
                            <SortIcon
                              active={Boolean(sorted)}
                              dir={sorted === "desc" ? "desc" : "asc"}
                            />
                          </Button>
                        ) : (
                          flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )
                        )}
                      </th>
                    );
                  })}
                </tr>
              ))}
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, index) => (
                  <tr
                    key={`skeleton-${index}`}
                    className="border-b border-border"
                  >
                    {columns.map((_, colIndex) => (
                      <td key={colIndex} className="px-4 py-3">
                        <div className="h-4 animate-pulse rounded bg-muted" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : isError ? (
                <tr>
                  <td colSpan={columns.length} className="p-0">
                    <EmptyState
                      title={t("error.title")}
                      description={errorMessage ?? t("error.description")}
                    />
                  </td>
                </tr>
              ) : table.getRowModel().rows.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="p-0">
                    <EmptyState
                      title={emptyTitle ?? t("empty.title")}
                      description={emptyDescription ?? t("empty.description")}
                    />
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b border-border last:border-b-0 hover:bg-accent/30"
                    {...testIdProps(tableRowTestId(row.id))}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-4 py-3 text-foreground">
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <Pagination
        page={state.page}
        pageSize={state.pageSize}
        totalItems={totalItems}
        onPageChange={(page) => setState({ page })}
        onPageSizeChange={(pageSize) => setState({ pageSize, page: 1 })}
      />
    </div>
  );
}

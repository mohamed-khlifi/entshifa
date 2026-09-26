"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { DataTable } from "@/components/data/DataTable";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  useInviteUserMutation,
  useRolesQuery,
  useUsersQuery,
} from "@/features/users/hooks/use-users-queries";
import type { UserRead } from "@/lib/api/generated";
import { testIdProps, testIds } from "@/lib/test/test-id";

export function UsersAdminPanel() {
  const t = useTranslations("users");
  const searchParams = useSearchParams();
  const page = Math.max(1, Number(searchParams.get("page") ?? "1") || 1);
  const pageSize = Math.max(
    1,
    Math.min(100, Number(searchParams.get("pageSize") ?? "20") || 20),
  );
  const search = (searchParams.get("q") ?? "").trim();
  const { data, isLoading, isError } = useUsersQuery({
    limit: pageSize,
    offset: (page - 1) * pageSize,
    search: search || undefined,
  });
  const { data: roles } = useRolesQuery();
  const invite = useInviteUserMutation();
  const [showInvite, setShowInvite] = useState(false);
  const [email, setEmail] = useState("");
  const [rolePublicId, setRolePublicId] = useState("");

  const columns = useMemo<ColumnDef<UserRead>[]>(
    () => [
      {
        id: "name",
        header: t("list.name"),
        cell: ({ row }) =>
          `${row.original.firstName} ${row.original.lastName}`.trim(),
      },
      { accessorKey: "email", header: t("list.email") },
      {
        id: "roles",
        header: t("list.roles"),
        cell: ({ row }) => row.original.roleCodes.join(", "),
      },
      {
        id: "mfa",
        header: t("list.mfa"),
        cell: ({ row }) =>
          row.original.mfaEnabled ? t("list.mfaOn") : t("list.mfaOff"),
      },
      {
        id: "status",
        header: t("list.status"),
        cell: ({ row }) =>
          row.original.isActive ? t("list.active") : t("list.inactive"),
      },
    ],
    [t],
  );

  const onInvite = async () => {
    if (!rolePublicId) return;
    await invite.mutateAsync({ email, rolePublicId });
    setEmail("");
    setShowInvite(false);
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <Card className="border-border/80 shadow-sm">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-4">
          <div>
            <CardTitle>{t("list.title")}</CardTitle>
            <CardDescription>{t("list.description")}</CardDescription>
          </div>
          <Button
            type="button"
            onClick={() => setShowInvite((v) => !v)}
            {...testIdProps(testIds.users.inviteOpen)}
          >
            {t("invite.action")}
          </Button>
        </CardHeader>
        <CardContent className="space-y-6">
          {showInvite ? (
            <div className="grid gap-4 rounded-lg border border-border bg-muted/20 p-4 sm:grid-cols-2">
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="invite-email">{t("invite.email")}</Label>
                <Input
                  id="invite-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  {...testIdProps(testIds.users.inviteEmail)}
                />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="invite-role">{t("invite.role")}</Label>
                <select
                  id="invite-role"
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={rolePublicId}
                  onChange={(e) => setRolePublicId(e.target.value)}
                  {...testIdProps(testIds.users.inviteRole)}
                >
                  <option value="" />
                  {(roles ?? []).map((role) => (
                    <option key={role.publicId} value={role.publicId}>
                      {role.code}
                    </option>
                  ))}
                </select>
              </div>
              <div className="sm:col-span-2">
                <Button
                  type="button"
                  onClick={() => void onInvite()}
                  disabled={!email || !rolePublicId || invite.isPending}
                  {...testIdProps(testIds.users.inviteSubmit)}
                >
                  {t("invite.submit")}
                </Button>
              </div>
            </div>
          ) : null}
          <div {...testIdProps(testIds.users.table)}>
            <DataTable
              columns={columns}
              data={data?.items ?? []}
              totalItems={data?.page.total ?? data?.items.length ?? 0}
              getRowId={(row) => row.publicId}
              isLoading={isLoading}
              isError={isError}
              emptyTitle={t("list.emptyTitle")}
              emptyDescription={t("list.emptyDescription")}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

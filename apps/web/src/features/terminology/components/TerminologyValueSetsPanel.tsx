"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

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
import { Link } from "@/lib/i18n/navigation";
import { queryKeys } from "@/lib/api/query-keys";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

import {
  addValueSetMember,
  fetchValueSet,
  fetchValueSets,
} from "../api/terminology-admin.api";

export function TerminologyValueSetsPanel() {
  const t = useTranslations("terminology");
  const locale = useLocale();
  const { session } = useSession();
  const queryClient = useQueryClient();
  const [code, setCode] = useState("tm.findings");
  const [conceptPublicId, setConceptPublicId] = useState("");

  const sets = useQuery({
    queryKey: queryKeys.terminology.valueSets(),
    queryFn: () => fetchValueSets(locale, session!.clinicPublicId),
    enabled: Boolean(session?.clinicPublicId),
  });
  const members = useQuery({
    queryKey: queryKeys.terminology.valueSet(code),
    queryFn: () => fetchValueSet(code, locale, session!.clinicPublicId),
    enabled: Boolean(session?.clinicPublicId && code),
  });
  const add = useMutation({
    mutationFn: () =>
      addValueSetMember(
        code,
        { conceptPublicId, sortOrder: 0, isDefault: false },
        locale,
        session!.clinicPublicId,
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.terminology.valueSet(code),
      });
      toast.success(t("valueSets.added"));
      setConceptPublicId("");
    },
  });

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link
        href="/admin/terminology"
        className="text-sm text-primary hover:underline"
      >
        {t("nav.concepts")}
      </Link>
      <Card
        className="border-border/80 shadow-sm"
        {...testIdProps(testIds.terminology.valueSets.root)}
      >
        <CardHeader>
          <CardTitle>{t("valueSets.title")}</CardTitle>
          <CardDescription>{t("valueSets.description")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="value-set">{t("valueSets.select")}</Label>
            <select
              id="value-set"
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={code}
              onChange={(event) => setCode(event.target.value)}
              {...testIdProps(testIds.terminology.valueSets.select)}
            >
              {(sets.data ?? []).map((item) => (
                <option key={item.code} value={item.code}>
                  {item.code}
                </option>
              ))}
            </select>
          </div>
          <ul className="space-y-2 text-sm">
            {(members.data?.members ?? []).map((member) => (
              <li
                key={member.publicId}
                className="rounded-md border border-border px-3 py-2"
              >
                {member.code} — {member.display}
              </li>
            ))}
          </ul>
          <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
            <Input
              value={conceptPublicId}
              onChange={(event) => setConceptPublicId(event.target.value)}
              aria-label={t("valueSets.conceptId")}
              {...testIdProps(testIds.terminology.valueSets.conceptId)}
            />
            <Button
              type="button"
              disabled={conceptPublicId.length !== 26 || add.isPending}
              onClick={() => void add.mutateAsync()}
              {...testIdProps(testIds.terminology.valueSets.add)}
            >
              {t("valueSets.add")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

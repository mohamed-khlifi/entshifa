"use client";

import { useQuery } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { searchAnatomyConcepts } from "../api/attachments.api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { queryKeys } from "@/lib/api/query-keys";
import { publicIdTestId, testIdProps, testIds } from "@/lib/test/test-id";
import { useSession } from "@/providers/session-provider";

const SEARCH_DEBOUNCE_MS = 300;

type BodySiteFieldProps = {
  selectedId: string;
  selectedDisplay: string;
  onSelect: (concept: { publicId: string; display: string }) => void;
  onClear: () => void;
};

export function BodySiteField({
  selectedId,
  selectedDisplay,
  onSelect,
  onClear,
}: BodySiteFieldProps) {
  const t = useTranslations("attachments");
  const locale = useLocale();
  const { session } = useSession();
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setDebounced(query.trim());
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(handle);
  }, [query]);

  const search = useQuery({
    queryKey: queryKeys.terminology.search({
      q: debounced,
      locale,
      kind: "anatomy",
    }),
    queryFn: () =>
      searchAnatomyConcepts(
        { locale, clinicPublicId: session!.clinicPublicId },
        debounced,
      ),
    enabled: Boolean(session?.clinicPublicId) && debounced.length >= 1,
    staleTime: 120_000,
  });

  return (
    <div className="space-y-1.5">
      <Label htmlFor={testIds.attachments.bodySite}>
        {t("upload.bodySite")}
      </Label>
      {selectedId ? (
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-muted/40 px-3 py-2">
          <span className="text-sm font-medium">{selectedDisplay}</span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onClear}
            {...testIdProps(testIds.attachments.bodySiteClear)}
          >
            {t("upload.clearBodySite")}
          </Button>
        </div>
      ) : (
        <Input
          id={testIds.attachments.bodySite}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          {...testIdProps(testIds.attachments.bodySite)}
        />
      )}
      {debounced.length >= 1 && !selectedId ? (
        <ul
          className="max-h-40 space-y-1 overflow-auto rounded-lg border border-border bg-card p-1"
          {...testIdProps(testIds.attachments.bodySiteResults)}
        >
          {(search.data?.items ?? []).map((item) => (
            <li key={item.publicId}>
              <button
                type="button"
                className="w-full rounded-md px-2 py-1.5 text-start text-sm hover:bg-muted"
                {...testIdProps(
                  publicIdTestId("attachments.body-site.option", item.publicId),
                )}
                onClick={() => {
                  onSelect({ publicId: item.publicId, display: item.display });
                  setQuery("");
                  setDebounced("");
                }}
              >
                {item.display}
              </button>
            </li>
          ))}
          {search.isFetched && (search.data?.items.length ?? 0) === 0 ? (
            <li className="px-2 py-1.5 text-sm text-muted-foreground">
              {t("upload.bodySiteEmpty")}
            </li>
          ) : null}
        </ul>
      ) : null}
    </div>
  );
}

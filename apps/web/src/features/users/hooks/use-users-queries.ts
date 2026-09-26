"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import {
  createInvitation,
  fetchRoles,
  fetchUsers,
} from "@/features/users/api/users.api";
import { queryKeys } from "@/lib/api/query-keys";
import type { InvitationCreate } from "@/lib/api/generated";
import { useSession } from "@/providers/session-provider";

export function useUsersQuery(params?: {
  limit?: number;
  offset?: number;
  search?: string;
}) {
  const locale = useLocale();
  const { session } = useSession();

  return useQuery({
    queryKey: queryKeys.users.list(params),
    queryFn: () => fetchUsers(locale, session!.clinicPublicId, params),
    enabled: Boolean(session?.clinicPublicId),
  });
}

export function useRolesQuery() {
  const locale = useLocale();
  const { session } = useSession();

  return useQuery({
    queryKey: queryKeys.users.roles(),
    queryFn: () => fetchRoles(locale, session!.clinicPublicId),
    enabled: Boolean(session?.clinicPublicId),
    staleTime: 60_000,
  });
}

export function useInviteUserMutation() {
  const locale = useLocale();
  const { session } = useSession();
  const queryClient = useQueryClient();
  const t = useTranslations("users");

  return useMutation({
    mutationFn: (body: InvitationCreate) =>
      createInvitation(body, locale, session!.clinicPublicId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
      toast.success(t("invite.success"));
    },
  });
}

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import { fetchSites } from "@/features/clinics";
import { fetchPatients } from "@/features/patients";
import {
  arriveAppointment,
  cancelAppointment,
  completeAppointment,
  createAppointment,
  fetchAppointmentTypes,
  fetchAppointments,
  fetchSchedulableDoctors,
  fetchWaitingRoom,
  inRoomAppointment,
  noShowAppointment,
} from "@/features/scheduling/api/scheduling.api";
import { queryKeys } from "@/lib/api/query-keys";
import type { AppointmentCreate } from "@/lib/api/generated";
import { useSession } from "@/providers/session-provider";

function scope(locale: string, clinicPublicId: string) {
  return { locale, clinicPublicId };
}

export function useAppointmentTypesQuery() {
  const locale = useLocale();
  const { session } = useSession();
  return useQuery({
    queryKey: queryKeys.scheduling.types(),
    queryFn: () =>
      fetchAppointmentTypes(scope(locale, session!.clinicPublicId)),
    enabled: Boolean(session?.clinicPublicId),
    staleTime: 3_600_000,
  });
}

export function useSchedulableDoctorsQuery() {
  const locale = useLocale();
  const { session } = useSession();
  return useQuery({
    queryKey: queryKeys.scheduling.doctors(),
    queryFn: () =>
      fetchSchedulableDoctors(scope(locale, session!.clinicPublicId)),
    enabled: Boolean(session?.clinicPublicId),
    staleTime: 300_000,
  });
}

export function useAppointmentsQuery(filters: {
  startsAfter: string;
  startsBefore: string;
  doctorUserId?: string;
  room?: string;
}) {
  const locale = useLocale();
  const { session } = useSession();
  return useQuery({
    queryKey: queryKeys.scheduling.appointments(filters),
    queryFn: () =>
      fetchAppointments(scope(locale, session!.clinicPublicId), filters),
    enabled: Boolean(session?.clinicPublicId && filters.startsAfter),
    staleTime: 15_000,
  });
}

export function useWaitingRoomQuery(on: string) {
  const locale = useLocale();
  const { session } = useSession();
  return useQuery({
    queryKey: queryKeys.scheduling.waitingRoom({ on }),
    queryFn: () =>
      fetchWaitingRoom(scope(locale, session!.clinicPublicId), { on }),
    enabled: Boolean(session?.clinicPublicId && on),
    staleTime: 10_000,
  });
}

export function useSchedulingSitesQuery() {
  const locale = useLocale();
  const { session } = useSession();
  return useQuery({
    queryKey: queryKeys.clinics.sites({ limit: 20 }),
    queryFn: () =>
      fetchSites(locale, session!.clinicPublicId, { limit: 20 }),
    enabled: Boolean(session?.clinicPublicId),
    staleTime: 300_000,
  });
}

export function usePatientSearchQuery(search: string) {
  const locale = useLocale();
  const { session } = useSession();
  return useQuery({
    queryKey: queryKeys.patients.list({ search, limit: 10 }),
    queryFn: () =>
      fetchPatients(scope(locale, session!.clinicPublicId), {
        search,
        limit: 10,
      }),
    enabled: Boolean(session?.clinicPublicId && search.length >= 2),
    staleTime: 30_000,
  });
}

export function useCreateAppointmentMutation() {
  const locale = useLocale();
  const { session } = useSession();
  const queryClient = useQueryClient();
  const t = useTranslations("scheduling");

  return useMutation({
    mutationFn: (body: AppointmentCreate) =>
      createAppointment(scope(locale, session!.clinicPublicId), body),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.scheduling.all,
      });
      if (data.overlapWarnings?.length) {
        toast.message(t("calendar.overlapWarning"));
      } else {
        toast.success(t("toast.created"));
      }
    },
  });
}

function useStatusMutation(
  fn: (
    scopeArg: ReturnType<typeof scope>,
    id: string,
  ) => Promise<unknown>,
) {
  const locale = useLocale();
  const { session } = useSession();
  const queryClient = useQueryClient();
  const t = useTranslations("scheduling");

  return useMutation({
    mutationFn: (appointmentId: string) =>
      fn(scope(locale, session!.clinicPublicId), appointmentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.scheduling.all,
      });
      toast.success(t("toast.statusUpdated"));
    },
  });
}

export function useArriveMutation() {
  return useStatusMutation(arriveAppointment);
}

export function useInRoomMutation() {
  return useStatusMutation(inRoomAppointment);
}

export function useCompleteMutation() {
  return useStatusMutation(completeAppointment);
}

export function useNoShowMutation() {
  return useStatusMutation(noShowAppointment);
}

export function useCancelMutation() {
  const locale = useLocale();
  const { session } = useSession();
  const queryClient = useQueryClient();
  const t = useTranslations("scheduling");

  return useMutation({
    mutationFn: (params: { appointmentId: string; reason: string }) =>
      cancelAppointment(
        scope(locale, session!.clinicPublicId),
        params.appointmentId,
        params.reason,
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.scheduling.all,
      });
      toast.success(t("toast.statusUpdated"));
    },
  });
}

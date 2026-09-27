import { apiFetch } from "@/lib/api/client";
import type {
  AppointmentCreate,
  AppointmentRead,
  AppointmentTypeRead,
  PageSchemaAppointmentRead,
  PageSchemaAppointmentTypeRead,
  PageSchemaSchedulableDoctorRead,
  PageSchemaWaitingRoomEntryRead,
} from "@/lib/api/generated";

type Scope = { locale: string; clinicPublicId: string };

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export function fetchAppointmentTypes(
  scope: Scope,
): Promise<PageSchemaAppointmentTypeRead> {
  return apiFetch<PageSchemaAppointmentTypeRead>(
    "/api/v1/appointment-types?limit=50",
    scope,
  );
}

export function fetchSchedulableDoctors(
  scope: Scope,
): Promise<PageSchemaSchedulableDoctorRead> {
  return apiFetch<PageSchemaSchedulableDoctorRead>(
    "/api/v1/scheduling/doctors?limit=50",
    scope,
  );
}

export function fetchAppointments(
  scope: Scope,
  params: {
    startsAfter: string;
    startsBefore: string;
    doctorUserId?: string;
    room?: string;
  },
): Promise<PageSchemaAppointmentRead> {
  return apiFetch<PageSchemaAppointmentRead>(
    `/api/v1/appointments${query({
      startsAfter: params.startsAfter,
      startsBefore: params.startsBefore,
      doctorUserId: params.doctorUserId,
      room: params.room,
      limit: 200,
    })}`,
    scope,
  );
}

export function fetchWaitingRoom(
  scope: Scope,
  params: { on: string },
): Promise<PageSchemaWaitingRoomEntryRead> {
  return apiFetch<PageSchemaWaitingRoomEntryRead>(
    `/api/v1/appointments/waiting-room${query({ on: params.on, limit: 50 })}`,
    scope,
  );
}

export function createAppointment(
  scope: Scope,
  body: AppointmentCreate,
): Promise<AppointmentRead> {
  return apiFetch<AppointmentRead>("/api/v1/appointments", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function arriveAppointment(
  scope: Scope,
  appointmentId: string,
): Promise<AppointmentRead> {
  return apiFetch<AppointmentRead>(
    `/api/v1/appointments/${appointmentId}/arrive`,
    { ...scope, method: "POST" },
  );
}

export function inRoomAppointment(
  scope: Scope,
  appointmentId: string,
): Promise<AppointmentRead> {
  return apiFetch<AppointmentRead>(
    `/api/v1/appointments/${appointmentId}/in-room`,
    { ...scope, method: "POST" },
  );
}

export function completeAppointment(
  scope: Scope,
  appointmentId: string,
): Promise<AppointmentRead> {
  return apiFetch<AppointmentRead>(
    `/api/v1/appointments/${appointmentId}/complete`,
    { ...scope, method: "POST" },
  );
}

export function noShowAppointment(
  scope: Scope,
  appointmentId: string,
): Promise<AppointmentRead> {
  return apiFetch<AppointmentRead>(
    `/api/v1/appointments/${appointmentId}/no-show`,
    { ...scope, method: "POST" },
  );
}

export function cancelAppointment(
  scope: Scope,
  appointmentId: string,
  cancellationReason: string,
): Promise<AppointmentRead> {
  return apiFetch<AppointmentRead>(
    `/api/v1/appointments/${appointmentId}/cancel`,
    {
      ...scope,
      method: "POST",
      body: JSON.stringify({ cancellationReason }),
    },
  );
}

export type { AppointmentTypeRead };

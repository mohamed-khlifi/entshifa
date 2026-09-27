"use client";

import { useMemo, useState } from "react";
import { useLocale, useTranslations } from "next-intl";

import { useCurrentClinicQuery } from "@/features/clinics";
import {
  useAppointmentsQuery,
  useAppointmentTypesQuery,
  useArriveMutation,
  useCancelMutation,
  useCompleteMutation,
  useCreateAppointmentMutation,
  useInRoomMutation,
  useNoShowMutation,
  usePatientSearchQuery,
  useSchedulableDoctorsQuery,
  useSchedulingSitesQuery,
  useWaitingRoomQuery,
} from "@/features/scheduling/hooks/use-scheduling-queries";
import {
  clinicLocalTimeToUtcIso,
  rangeForCalendarView,
  type CalendarView,
} from "@/features/scheduling/utils/clinic-range";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formControlClass } from "@/components/ui/form-control";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import type {
  AppointmentRead,
  AppointmentTypeRead,
  PatientSummaryRead,
  SchedulableDoctorRead,
  WaitingRoomEntryRead,
} from "@/lib/api/generated";
import { formatDateTimeInTimeZone } from "@/lib/i18n/format";
import { cn } from "@/lib/utils/cn";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { Permission } from "@/lib/permissions";
import { usePermission } from "@/providers/permission-provider";

function typeLabel(
  t: ReturnType<typeof useTranslations>,
  nameKey: string,
): string {
  const key = nameKey.startsWith("scheduling.")
    ? nameKey.slice("scheduling.".length)
    : nameKey;
  return t(key as "appointment_type.follow_up");
}

export function SchedulePanel() {
  const t = useTranslations("scheduling");
  const locale = useLocale();
  const canWrite = usePermission(Permission.APPOINTMENT_WRITE);
  const { data: clinic } = useCurrentClinicQuery();
  const timeZone = clinic?.timezone ?? "UTC";

  const [view, setView] = useState<CalendarView>("day");
  const [anchor, setAnchor] = useState(() => new Date());
  const [doctorId, setDoctorId] = useState<string>("");
  const [room, setRoom] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showBook, setShowBook] = useState(false);
  const [patientSearch, setPatientSearch] = useState("");
  const [bookPatientId, setBookPatientId] = useState("");
  const [bookDoctorId, setBookDoctorId] = useState("");
  const [bookTypeId, setBookTypeId] = useState("");
  const [bookSiteId, setBookSiteId] = useState("");
  const [bookStart, setBookStart] = useState("09:00");
  const [bookDuration, setBookDuration] = useState("30");
  const [bookRoom, setBookRoom] = useState("");

  const range = useMemo(
    () => rangeForCalendarView(anchor, view, timeZone),
    [anchor, view, timeZone],
  );

  const { data: types } = useAppointmentTypesQuery();
  const { data: doctors } = useSchedulableDoctorsQuery();
  const { data: sites } = useSchedulingSitesQuery();
  const { data: appointments, isLoading } = useAppointmentsQuery({
    startsAfter: range.startsAfter,
    startsBefore: range.startsBefore,
    doctorUserId: doctorId || undefined,
    room: room || undefined,
  });
  const { data: waiting } = useWaitingRoomQuery(range.on);
  const { data: patientHits } = usePatientSearchQuery(patientSearch);

  const createMutation = useCreateAppointmentMutation();
  const arriveMutation = useArriveMutation();
  const inRoomMutation = useInRoomMutation();
  const completeMutation = useCompleteMutation();
  const noShowMutation = useNoShowMutation();
  const cancelMutation = useCancelMutation();

  const selected = appointments?.items.find(
    (a: AppointmentRead) => a.publicId === selectedId,
  );

  function shiftAnchor(days: number) {
    setAnchor((prev) => {
      const next = new Date(prev);
      next.setDate(next.getDate() + days);
      return next;
    });
  }

  async function submitBooking() {
    if (!bookPatientId || !bookDoctorId || !bookTypeId || !bookSiteId) {
      return;
    }
    const startsAt = clinicLocalTimeToUtcIso(range.on, bookStart, timeZone);
    const durationMin = Number(bookDuration);
    const endsAt = new Date(
      Date.parse(startsAt) + durationMin * 60_000,
    ).toISOString();
    await createMutation.mutateAsync({
      siteId: bookSiteId,
      patientId: bookPatientId,
      userId: bookDoctorId,
      appointmentTypeId: bookTypeId,
      startsAt,
      endsAt,
      room: bookRoom || undefined,
    });
    setShowBook(false);
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            {...testIdProps(testIds.scheduling.prev)}
            onClick={() => shiftAnchor(view === "week" ? -7 : -1)}
          >
            {t("actions.prev")}
          </Button>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            {...testIdProps(testIds.scheduling.today)}
            onClick={() => setAnchor(new Date())}
          >
            {t("actions.today")}
          </Button>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            {...testIdProps(testIds.scheduling.next)}
            onClick={() => shiftAnchor(view === "week" ? 7 : 1)}
          >
            {t("actions.next")}
          </Button>
          <div className="ms-auto flex gap-2">
            <Button
              type="button"
              variant={view === "day" ? "default" : "secondary"}
              size="sm"
              {...testIdProps(testIds.scheduling.viewDay)}
              onClick={() => setView("day")}
            >
              {t("views.day")}
            </Button>
            <Button
              type="button"
              variant={view === "week" ? "default" : "secondary"}
              size="sm"
              {...testIdProps(testIds.scheduling.viewWeek)}
              onClick={() => setView("week")}
            >
              {t("views.week")}
            </Button>
          </div>
        </div>

        <div className="flex flex-wrap gap-4">
          <div className="min-w-[200px]">
            <Label>{t("filters.doctor")}</Label>
            <Select
              className={cn(formControlClass, "w-full")}
              value={doctorId || ""}
              onChange={(event) => setDoctorId(event.target.value)}
              {...testIdProps(testIds.scheduling.doctorFilter)}
            >
              <option value="">{t("filters.allDoctors")}</option>
              {doctors?.items.map((doc: SchedulableDoctorRead) => (
                <option key={doc.publicId} value={doc.publicId}>
                  {doc.firstName} {doc.lastName}
                </option>
              ))}
            </Select>
          </div>
          <div className="min-w-[160px]">
            <Label>{t("filters.room")}</Label>
            <Input
              value={room}
              onChange={(event) => setRoom(event.target.value)}
              {...testIdProps(testIds.scheduling.roomFilter)}
            />
          </div>
          {canWrite ? (
            <div className="flex items-end">
              <Button
                type="button"
                {...testIdProps(testIds.scheduling.bookOpen)}
                onClick={() => setShowBook(true)}
              >
                {t("actions.newAppointment")}
              </Button>
            </div>
          ) : null}
        </div>

        <Card {...testIdProps(testIds.scheduling.calendar)}>
          <CardHeader>
            <CardTitle className="text-base">{t("page.title")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {isLoading ? (
              <p
                className="text-sm text-muted-foreground"
                {...testIdProps(testIds.scheduling.calendarLoading)}
              >
                {t("loading")}
              </p>
            ) : null}
            {!isLoading && !appointments?.items.length ? (
              <p
                className="text-sm text-muted-foreground"
                {...testIdProps(testIds.scheduling.calendarEmpty)}
              >
                {t("calendar.empty")}
              </p>
            ) : null}
            {appointments?.items.map((appt: AppointmentRead) => (
              <button
                key={appt.publicId}
                type="button"
                className={cn(
                  "flex w-full flex-col rounded-lg border border-border px-3 py-2 text-start transition-colors",
                  selectedId === appt.publicId
                    ? "border-primary bg-primary/5"
                    : "hover:bg-muted/60",
                )}
                {...testIdProps(
                  testIds.scheduling.appointmentRow(appt.publicId),
                )}
                onClick={() => setSelectedId(appt.publicId)}
              >
                <span className="text-sm font-medium">
                  {formatDateTimeInTimeZone(appt.startsAt, timeZone, locale)} —{" "}
                  {t(`status.${appt.status}` as "status.scheduled")}
                </span>
                <span className="text-xs text-muted-foreground">
                  {appt.room ?? t("filters.anyRoom")}
                </span>
              </button>
            ))}
          </CardContent>
        </Card>

        {selected && canWrite ? (
          <Card {...testIdProps(testIds.scheduling.selectedActions)}>
            <CardContent className="flex flex-wrap gap-2 pt-4">
              {selected.status === "scheduled" ? (
                <Button
                  type="button"
                  size="sm"
                  {...testIdProps(testIds.scheduling.arrive)}
                  onClick={() => arriveMutation.mutate(selected.publicId)}
                >
                  {t("actions.arrive")}
                </Button>
              ) : null}
              {selected.status === "arrived" ? (
                <Button
                  type="button"
                  size="sm"
                  {...testIdProps(testIds.scheduling.inRoom)}
                  onClick={() => inRoomMutation.mutate(selected.publicId)}
                >
                  {t("actions.inRoom")}
                </Button>
              ) : null}
              {selected.status === "in_room" ? (
                <Button
                  type="button"
                  size="sm"
                  {...testIdProps(testIds.scheduling.complete)}
                  onClick={() => completeMutation.mutate(selected.publicId)}
                >
                  {t("actions.complete")}
                </Button>
              ) : null}
              {selected.status === "scheduled" ? (
                <>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    {...testIdProps(testIds.scheduling.noShow)}
                    onClick={() => noShowMutation.mutate(selected.publicId)}
                  >
                    {t("actions.noShow")}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="destructive"
                    {...testIdProps(testIds.scheduling.cancel)}
                    onClick={() =>
                      cancelMutation.mutate({
                        appointmentId: selected.publicId,
                        reason: "cancelled_at_desk",
                      })
                    }
                  >
                    {t("actions.cancel")}
                  </Button>
                </>
              ) : null}
            </CardContent>
          </Card>
        ) : null}
      </div>

      <Card {...testIdProps(testIds.scheduling.waitingRoom)}>
        <CardHeader>
          <CardTitle className="text-base">{t("waitingRoom.title")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {!waiting?.items.length ? (
            <p
              className="text-sm text-muted-foreground"
              {...testIdProps(testIds.scheduling.waitingEmpty)}
            >
              {t("waitingRoom.empty")}
            </p>
          ) : null}
          {waiting?.items.map((entry: WaitingRoomEntryRead) => (
            <div
              key={entry.appointment.publicId}
              className="rounded-lg border border-border px-3 py-2"
              {...testIdProps(
                testIds.scheduling.waitingRow(entry.appointment.publicId),
              )}
            >
              <p className="text-sm font-medium">{entry.patientDisplayName}</p>
              <p className="text-xs text-muted-foreground">
                {entry.doctorDisplayName}
              </p>
              {entry.appointment.arrivedAt ? (
                <p className="text-xs text-muted-foreground">
                  {t("waitingRoom.arrivedAt", {
                    time: formatDateTimeInTimeZone(
                      entry.appointment.arrivedAt,
                      timeZone,
                      locale,
                      { hour: "2-digit", minute: "2-digit" },
                    ),
                  })}
                </p>
              ) : null}
              <p className="text-xs text-muted-foreground">
                {t(
                  `questionnaire.${entry.appointment.questionnaireStatus.status}` as "questionnaire.not_applicable",
                )}
              </p>
            </div>
          ))}
        </CardContent>
      </Card>

      {showBook && canWrite ? (
        <Card
          className="lg:col-span-2"
          {...testIdProps(testIds.scheduling.bookForm)}
        >
          <CardHeader>
            <CardTitle className="text-base">
              {t("actions.newAppointment")}
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <Label>{t("form.patient")}</Label>
              <Input
                value={patientSearch}
                onChange={(event) => setPatientSearch(event.target.value)}
                {...testIdProps(testIds.scheduling.bookPatientSearch)}
              />
              {patientHits?.items.length ? (
                <ul className="mt-2 space-y-1">
                  {patientHits.items.map((p: PatientSummaryRead) => (
                    <li key={p.publicId}>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-auto w-full justify-start px-2"
                        onClick={() => {
                          setBookPatientId(p.publicId);
                          setPatientSearch(`${p.firstName} ${p.lastName}`);
                        }}
                      >
                        {p.firstName} {p.lastName}
                      </Button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
            <div>
              <Label>{t("form.doctor")}</Label>
              <Select
                className={cn(formControlClass, "w-full")}
                value={bookDoctorId}
                onChange={(event) => setBookDoctorId(event.target.value)}
                {...testIdProps(testIds.scheduling.bookDoctor)}
              >
                <option value="" />
                {doctors?.items.map((doc: SchedulableDoctorRead) => (
                  <option key={doc.publicId} value={doc.publicId}>
                    {doc.firstName} {doc.lastName}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t("form.type")}</Label>
              <Select
                className={cn(formControlClass, "w-full")}
                value={bookTypeId}
                onChange={(event) => setBookTypeId(event.target.value)}
                {...testIdProps(testIds.scheduling.bookType)}
              >
                <option value="" />
                {types?.items.map((type: AppointmentTypeRead) => (
                  <option key={type.publicId} value={type.publicId}>
                    {typeLabel(t, type.nameKey)}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t("form.site")}</Label>
              <Select
                className={cn(formControlClass, "w-full")}
                value={bookSiteId}
                onChange={(event) => setBookSiteId(event.target.value)}
                {...testIdProps(testIds.scheduling.bookSite)}
              >
                <option value="" />
                {sites?.items.map((site) => (
                  <option key={site.publicId} value={site.publicId}>
                    {site.name}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t("form.startsAt")}</Label>
              <Input
                type="time"
                value={bookStart}
                onChange={(event) => setBookStart(event.target.value)}
                {...testIdProps(testIds.scheduling.bookStart)}
              />
            </div>
            <div>
              <Label>{t("form.duration")}</Label>
              <Input
                type="number"
                min={5}
                max={480}
                value={bookDuration}
                onChange={(event) => setBookDuration(event.target.value)}
                {...testIdProps(testIds.scheduling.bookDuration)}
              />
            </div>
            <div>
              <Label>{t("form.room")}</Label>
              <Input
                value={bookRoom}
                onChange={(event) => setBookRoom(event.target.value)}
                {...testIdProps(testIds.scheduling.bookRoom)}
              />
            </div>
            <div className="flex gap-2 sm:col-span-2">
              <Button
                type="button"
                {...testIdProps(testIds.scheduling.bookSubmit)}
                onClick={() => void submitBooking()}
                disabled={createMutation.isPending}
              >
                {t("form.submit")}
              </Button>
              <Button
                type="button"
                variant="secondary"
                {...testIdProps(testIds.scheduling.bookCancel)}
                onClick={() => setShowBook(false)}
              >
                {t("actions.cancel")}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

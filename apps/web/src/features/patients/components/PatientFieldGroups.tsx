"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { Controller, useFormContext, type FieldPath } from "react-hook-form";

import { SEX_VALUES } from "../constants";
import { sexLabel } from "../lib/labels";
import type { PatientFormValues } from "../schemas/patient-form.schema";
import { DateField } from "@/components/forms/DateField";
import { SelectField } from "@/components/forms/SelectField";
import { TextField } from "@/components/forms/TextField";
import { LOCALES } from "@/lib/i18n/config";
import { fieldTestId } from "@/lib/forms/field-test-id";
import { testIdProps } from "@/lib/test/test-id";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-4">
      <h3 className="text-sm font-semibold">{title}</h3>
      <div className="grid gap-4 sm:grid-cols-2">{children}</div>
    </section>
  );
}

function BoolField({
  name,
  label,
}: {
  name: FieldPath<PatientFormValues>;
  label: string;
}) {
  const { control } = useFormContext<PatientFormValues>();
  const inputId = fieldTestId(name);
  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <label htmlFor={inputId} className="flex items-center gap-2 text-sm">
          <input
            id={inputId}
            type="checkbox"
            checked={Boolean(field.value)}
            onBlur={field.onBlur}
            ref={field.ref}
            onChange={(event) => field.onChange(event.target.checked)}
            {...testIdProps(inputId)}
          />
          {label}
        </label>
      )}
    />
  );
}

export function PatientFieldGroups({ mode }: { mode: "create" | "edit" }) {
  const t = useTranslations("patients");
  const tCommon = useTranslations("common");
  const sexOptions = SEX_VALUES.map((value) => ({
    value,
    label: sexLabel(t, value),
  }));
  const localeOptions = LOCALES.map((code) => ({
    value: code,
    label: tCommon(`locale.options.${code}`),
  }));

  return (
    <div className="space-y-8">
      <Section title={t("form.sections.identity")}>
        <TextField<PatientFormValues>
          name="firstName"
          label={t("form.fields.firstName")}
          required
        />
        <TextField<PatientFormValues>
          name="lastName"
          label={t("form.fields.lastName")}
          required
        />
        <TextField<PatientFormValues>
          name="firstNameAlt"
          label={t("form.fields.firstNameAlt")}
        />
        <TextField<PatientFormValues>
          name="lastNameAlt"
          label={t("form.fields.lastNameAlt")}
        />
        <DateField<PatientFormValues>
          name="birthDate"
          label={t("form.fields.birthDate")}
          required
        />
        <BoolField
          name="birthDateIsEstimated"
          label={t("form.fields.birthDateEstimated")}
        />
        <SelectField<PatientFormValues>
          name="sex"
          label={t("form.fields.sex")}
          options={sexOptions}
          required
        />
        <SelectField<PatientFormValues>
          name="preferredLocale"
          label={t("form.fields.preferredLocale")}
          options={localeOptions}
          required
        />
        {mode === "create" ? (
          <TextField<PatientFormValues>
            name="mrn"
            label={t("form.fields.mrn")}
          />
        ) : null}
      </Section>
      <Section title={t("form.sections.contact")}>
        <TextField<PatientFormValues>
          name="phonePrimary"
          label={t("form.fields.phonePrimary")}
          type="tel"
        />
        <TextField<PatientFormValues>
          name="phoneSecondary"
          label={t("form.fields.phoneSecondary")}
          type="tel"
        />
        <TextField<PatientFormValues>
          name="email"
          label={t("form.fields.email")}
          type="email"
        />
        <TextField<PatientFormValues>
          name="addressLine1"
          label={t("form.fields.addressLine1")}
        />
        <TextField<PatientFormValues>
          name="addressLine2"
          label={t("form.fields.addressLine2")}
        />
        <TextField<PatientFormValues>
          name="city"
          label={t("form.fields.city")}
        />
        <TextField<PatientFormValues>
          name="postalCode"
          label={t("form.fields.postalCode")}
        />
        <TextField<PatientFormValues>
          name="countryCode"
          label={t("form.fields.countryCode")}
        />
      </Section>
      <Section title={t("form.sections.background")}>
        <TextField<PatientFormValues>
          name="occupation"
          label={t("form.fields.occupation")}
        />
        <TextField<PatientFormValues>
          name="noiseExposure"
          label={t("form.fields.noiseExposure")}
        />
        <TextField<PatientFormValues>
          name="smokingStatus"
          label={t("form.fields.smokingStatus")}
        />
        <TextField<PatientFormValues>
          name="alcoholStatus"
          label={t("form.fields.alcoholStatus")}
        />
        <TextField<PatientFormValues>
          name="insuranceNumber"
          label={t("form.fields.insuranceNumber")}
        />
      </Section>
      <Section title={t("form.sections.referring")}>
        <TextField<PatientFormValues>
          name="referringDoctorName"
          label={t("form.fields.referringDoctorName")}
        />
        <TextField<PatientFormValues>
          name="referringDoctorPhone"
          label={t("form.fields.referringDoctorPhone")}
          type="tel"
        />
        <TextField<PatientFormValues>
          name="referringDoctorEmail"
          label={t("form.fields.referringDoctorEmail")}
          type="email"
        />
        <TextField<PatientFormValues>
          name="referringDoctorLocale"
          label={t("form.fields.referringDoctorLocale")}
        />
      </Section>
      <Section title={t("form.sections.guardian")}>
        <TextField<PatientFormValues>
          name="guardianName"
          label={t("form.fields.guardianName")}
        />
        <TextField<PatientFormValues>
          name="guardianRelation"
          label={t("form.fields.guardianRelation")}
        />
        <TextField<PatientFormValues>
          name="emergencyContactName"
          label={t("form.fields.emergencyContactName")}
        />
        <TextField<PatientFormValues>
          name="emergencyContactPhone"
          label={t("form.fields.emergencyContactPhone")}
          type="tel"
        />
      </Section>
      <Section title={t("form.sections.consent")}>
        <BoolField name="consentSms" label={t("form.fields.consentSms")} />
        <BoolField name="consentEmail" label={t("form.fields.consentEmail")} />
        <BoolField
          name="consentTeaching"
          label={t("form.fields.consentTeaching")}
        />
        <BoolField name="isDeceased" label={t("form.fields.isDeceased")} />
        <DateField<PatientFormValues>
          name="deceasedDate"
          label={t("form.fields.deceasedDate")}
        />
      </Section>
    </div>
  );
}

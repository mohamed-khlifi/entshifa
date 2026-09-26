'use client';

import { useTranslations } from 'next-intl';
import { useCallback, useMemo, useState } from 'react';
import { toast } from 'sonner';

import {
  AutosaveIndicator,
  ConceptField,
  DateField,
  DirtyGuard,
  Form,
  LateralityField,
  NumberField,
  ScaleField,
  SelectField,
  TextField,
} from '@/components/forms';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useClinicalForm } from '@/lib/forms/createForm';
import { MEDICAL_UNITS } from '@/lib/i18n/format';
import { testIdProps, testIds } from '@/lib/test/test-id';

import { createUiKitDemoSchema } from '../schemas/demo.schema';

export function UiKitFormDemo() {
  const t = useTranslations('uiKit');
  const [version, setVersion] = useState(1);

  const schema = useMemo(
    () =>
      createUiKitDemoSchema({
        lastNameRequired: t('form.validation.lastNameRequired'),
        weightRequired: t('form.validation.weightRequired'),
        sexRequired: t('form.validation.sexRequired'),
        birthDateRequired: t('form.validation.birthDateRequired'),
        sideRequired: t('form.validation.sideRequired'),
        diagnosisRequired: t('form.validation.diagnosisRequired'),
        painRequired: t('form.validation.painRequired'),
      }),
    [t],
  );

  const onSave = useCallback(
    async ({ version: current }: { version: number }) => {
      await new Promise((resolve) => setTimeout(resolve, 400));
      const next = current + 1;
      setVersion(next);
      return { version: next };
    },
    [],
  );

  const onSubmit = useCallback(async () => {
    toast.success(t('form.submit'));
  }, [t]);

  const { form, handleSubmit, autosaveStatus } = useClinicalForm({
    schema,
    defaultValues: {
      lastName: '',
      weightKg: undefined,
      sex: '',
      birthDate: '',
      side: undefined,
      diagnosis: '',
      painScore: undefined,
    },
    autosave: {
      key: 'ui-kit-demo-form',
      version,
      delayMs: 2000,
      onSave,
    },
    onSubmit,
  });

  const sexOptions = [
    { value: 'female', label: t('form.sexFemale') },
    { value: 'male', label: t('form.sexMale') },
    { value: 'other', label: t('form.sexOther') },
  ];

  const conceptOptions = [
    { value: 'concept-otitis', label: t('form.concepts.otitis') },
    { value: 'concept-rhinitis', label: t('form.concepts.rhinitis') },
    { value: 'concept-vertigo', label: t('form.concepts.vertigo') },
  ];

  return (
    <Card {...testIdProps(testIds.uiKit.form)}>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div className="space-y-1.5">
          <CardTitle>{t('form.title')}</CardTitle>
          <CardDescription>{t('form.description')}</CardDescription>
        </div>
        <AutosaveIndicator status={autosaveStatus} />
      </CardHeader>
      <CardContent>
        <Form form={form} onSubmit={handleSubmit}>
          <DirtyGuard>
            <div className="grid gap-5 sm:grid-cols-2">
              <TextField
                name="lastName"
                label={t('form.lastName')}
                description={t('form.lastNameDescription')}
                required
              />
              <NumberField
                name="weightKg"
                label={t('form.weightKg')}
                unit={MEDICAL_UNITS.kg}
                min={0.5}
                max={300}
                step={0.1}
                required
              />
              <SelectField
                name="sex"
                label={t('form.sex')}
                options={sexOptions}
                placeholder={t('form.sexPlaceholder')}
                required
              />
              <DateField name="birthDate" label={t('form.birthDate')} required />
              <LateralityField name="side" label={t('form.side')} required />
              <ConceptField
                name="diagnosis"
                label={t('form.diagnosis')}
                options={conceptOptions}
                valueSet="ent-demo-findings"
                placeholder={t('form.diagnosisPlaceholder')}
                required
              />
              <div className="sm:col-span-2">
                <ScaleField name="painScore" label={t('form.painScore')} min={0} max={10} required />
              </div>
            </div>
            <Button type="submit" className="mt-6" {...testIdProps(testIds.uiKit.formSubmit)}>
              {t('form.submit')}
            </Button>
          </DirtyGuard>
        </Form>
      </CardContent>
    </Card>
  );
}

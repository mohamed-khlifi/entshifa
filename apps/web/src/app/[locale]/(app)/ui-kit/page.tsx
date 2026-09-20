import { Suspense } from 'react';
import { getTranslations } from 'next-intl/server';

import { PageHeader } from '@/components/layout/PageHeader';
import { UiKitFormDemo, UiKitTableDemo } from '@/features/ui-kit';
import { testIdProps, testIds } from '@/lib/test/test-id';

export default async function UiKitPage() {
  const t = await getTranslations('uiKit');

  return (
    <div className="space-y-8" {...testIdProps(testIds.uiKit.root)}>
      <PageHeader title={t('nav.title')} />
      <UiKitFormDemo />
      <Suspense fallback={null}>
        <UiKitTableDemo />
      </Suspense>
    </div>
  );
}

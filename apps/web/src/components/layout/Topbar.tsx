'use client';

import { useTranslations } from 'next-intl';

import { LogoutButton } from '@/features/auth/components/LogoutButton';
import { testIdProps, testIds } from '@/lib/test/test-id';

export function Topbar() {
  const t = useTranslations('common');

  return (
    <header
      className="flex h-14 items-center justify-between border-b border-border px-4"
      {...testIdProps(testIds.layout.topbar)}
    >
      <span className="text-sm font-semibold">{t('app.name')}</span>
      <LogoutButton />
    </header>
  );
}

'use client';

import { useTranslations } from 'next-intl';

import { LogoutButton } from '@/features/auth/components/LogoutButton';
import { LocaleSwitcher } from '@/components/layout/LocaleSwitcher';
import { testIdProps, testIds } from '@/lib/test/test-id';

export function Topbar() {
  const t = useTranslations('common');

  return (
    <header
      className="flex h-14 items-center justify-between gap-4 border-b border-border bg-card px-4 shadow-sm"
      {...testIdProps(testIds.layout.topbar)}
    >
      <span className="text-sm font-semibold">{t('app.name')}</span>
      <div className="flex items-center gap-2 sm:gap-3">
        <LocaleSwitcher />
        <LogoutButton />
      </div>
    </header>
  );
}

'use client';

import { useTranslations } from 'next-intl';

import { Link, usePathname } from '@/i18n/navigation';
import { cn } from '@/lib/utils/cn';
import { testIdProps, testIds } from '@/lib/test/test-id';

function navClass(active: boolean): string {
  return cn(
    'rounded-md px-3 py-2 text-sm font-medium transition-colors',
    active
      ? 'bg-accent text-accent-foreground'
      : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
  );
}

export function Sidebar() {
  const t = useTranslations('common');
  const pathname = usePathname();

  const homeActive = pathname === '/home' || pathname.startsWith('/home/');
  const uiKitActive = pathname === '/ui-kit' || pathname.startsWith('/ui-kit/');

  return (
    <aside
      className="hidden h-full w-56 shrink-0 overflow-y-auto border-e border-border bg-card shadow-sm md:block"
      {...testIdProps(testIds.layout.sidebar)}
    >
      <nav className="flex flex-col gap-1 p-4">
        <Link href="/home" className={navClass(homeActive)}>
          {t('nav.home')}
        </Link>
        <Link href="/ui-kit" className={navClass(uiKitActive)}>
          {t('nav.uiKit')}
        </Link>
      </nav>
    </aside>
  );
}

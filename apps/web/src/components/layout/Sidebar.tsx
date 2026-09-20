'use client';

import { useTranslations } from 'next-intl';

import { Link, usePathname } from '@/i18n/navigation';
import { cn } from '@/lib/utils/cn';
import { testIdProps, testIds } from '@/lib/test/test-id';

export function Sidebar() {
  const t = useTranslations('common');
  const pathname = usePathname();

  const homeActive = pathname === '/home' || pathname.startsWith('/home/');

  return (
    <aside
      className="hidden w-56 shrink-0 border-e border-border bg-card md:block"
      {...testIdProps(testIds.layout.sidebar)}
    >
      <nav className="flex flex-col gap-1 p-4">
        <Link
          href="/home"
          className={cn(
            'rounded-md px-3 py-2 text-sm font-medium transition-colors',
            homeActive
              ? 'bg-accent text-accent-foreground'
              : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
          )}
        >
          {t('nav.home')}
        </Link>
      </nav>
    </aside>
  );
}

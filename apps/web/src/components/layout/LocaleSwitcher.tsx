'use client';

import { ChevronDown, Globe } from 'lucide-react';
import { useLocale, useTranslations } from 'next-intl';
import { useTransition } from 'react';

import { usePathname, useRouter } from '@/i18n/navigation';
import { routing, type AppLocale } from '@/i18n/routing';
import { cn } from '@/lib/utils/cn';
import { testIdProps, testIds } from '@/lib/test/test-id';

type LocaleSwitcherProps = {
  className?: string;
};

export function LocaleSwitcher({ className }: LocaleSwitcherProps) {
  const locale = useLocale() as AppLocale;
  const pathname = usePathname();
  const router = useRouter();
  const t = useTranslations('common');
  const [isPending, startTransition] = useTransition();

  const handleChange = (nextLocale: string) => {
    if (nextLocale === locale) {
      return;
    }
    startTransition(() => {
      router.replace(pathname, { locale: nextLocale as AppLocale });
    });
  };

  return (
    <div
      className={cn('relative inline-flex items-center', className)}
      {...testIdProps(testIds.layout.localeSwitcher)}
    >
      <Globe
        className="pointer-events-none absolute start-2.5 size-4 text-muted-foreground"
        aria-hidden
      />
      <label htmlFor="locale-switcher" className="sr-only">
        {t('locale.label')}
      </label>
      <select
        id="locale-switcher"
        value={locale}
        disabled={isPending}
        onChange={(event) => handleChange(event.target.value)}
        className={cn(
          'h-9 min-w-[9.5rem] cursor-pointer appearance-none rounded-lg border border-input bg-card py-1.5 ps-9 pe-8 text-sm font-medium text-foreground shadow-sm transition-[color,box-shadow,opacity] hover:border-primary/30 hover:bg-accent/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-60',
        )}
        {...testIdProps(testIds.layout.localeSwitcherSelect)}
      >
        {routing.locales.map((code) => (
          <option key={code} value={code}>
            {t(`locale.options.${code}`)}
          </option>
        ))}
      </select>
      <ChevronDown
        className="pointer-events-none absolute end-2.5 size-4 text-muted-foreground"
        aria-hidden
      />
    </div>
  );
}

'use client';

import { useTranslations } from 'next-intl';
import type { ReactNode } from 'react';

import { cn } from '@/lib/utils/cn';
import { testIdProps, testIds } from '@/lib/test/test-id';

export type EmptyStateProps = {
  title: string;
  description?: string;
  className?: string;
  action?: ReactNode;
};

export function EmptyState({ title, description, className, action }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-card/50 px-6 py-12 text-center',
        className,
      )}
      {...testIdProps(testIds.data.empty)}
    >
      <p className="text-sm font-medium text-foreground">{title}</p>
      {description ? (
        <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
      ) : null}
      {action}
    </div>
  );
}

export function DefaultEmptyState() {
  const t = useTranslations('data');
  return <EmptyState title={t('empty.title')} description={t('empty.description')} />;
}

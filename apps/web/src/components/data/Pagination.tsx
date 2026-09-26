'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useTranslations } from 'next-intl';

import { Button } from '@/components/ui/button';
import { directionalIconClass } from '@/lib/i18n/directional-icon';
import { cn } from '@/lib/utils/cn';
import { testIdProps, testIds } from '@/lib/test/test-id';

export type PaginationProps = {
  page: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: readonly number[];
  className?: string;
};

export function Pagination({
  page,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 20, 50],
  className,
}: PaginationProps) {
  const t = useTranslations('data');
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const from = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(totalItems, page * pageSize);

  return (
    <div
      className={cn(
        'flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4 text-sm',
        className,
      )}
      {...testIdProps(testIds.data.pagination)}
    >
      <p className="text-muted-foreground">
        {t('pagination.summary', { from, to, total: totalItems })}
      </p>
      <div className="flex items-center gap-2">
        {onPageSizeChange ? (
          <label className="flex items-center gap-2 text-muted-foreground">
            <span className="sr-only">{t('pagination.pageSize')}</span>
            <select
              className="h-9 rounded-lg border border-input bg-card px-2 text-sm"
              value={pageSize}
              onChange={(event) => onPageSizeChange(Number(event.target.value))}
              {...testIdProps(testIds.data.pageSize)}
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          {...testIdProps(testIds.data.pagePrev)}
        >
          <ChevronLeft className={directionalIconClass('size-4')} aria-hidden />
          <span className="sr-only">{t('pagination.prev')}</span>
        </Button>
        <span className="min-w-[4rem] text-center tabular-nums text-muted-foreground">
          {t('pagination.pageOf', { page, totalPages })}
        </span>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          {...testIdProps(testIds.data.pageNext)}
        >
          <ChevronRight className={directionalIconClass('size-4')} aria-hidden />
          <span className="sr-only">{t('pagination.next')}</span>
        </Button>
      </div>
    </div>
  );
}

'use client';

import { createColumnHelper, type ColumnDef } from '@tanstack/react-table';
import { useTranslations } from 'next-intl';
import { useMemo } from 'react';
import { useSearchParams } from 'next/navigation';

import { DataTable } from '@/components/data';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { testIdProps, testIds } from '@/lib/test/test-id';

type DemoRow = {
  id: string;
  name: string;
  role: string;
  site: string;
};

const DEMO_ROWS: DemoRow[] = [
  { id: 'row-amina', name: 'Amina Admin', role: 'clinic_admin', site: 'Site principal' },
  { id: 'row-sophie', name: 'Sophie Bernard', role: 'doctor', site: 'Site principal' },
  { id: 'row-karim', name: 'Karim Dupont', role: 'doctor', site: 'Annexe' },
  { id: 'row-leila', name: 'Leila Moreau', role: 'doctor', site: 'Site principal' },
  { id: 'row-marc', name: 'Marc Audio', role: 'audiology_technician', site: 'Annexe' },
  { id: 'row-yasmine', name: 'Yasmine Audi', role: 'audiology_technician', site: 'Site principal' },
  { id: 'row-asst1', name: 'Assistant 01', role: 'assistant', site: 'Site principal' },
  { id: 'row-asst2', name: 'Assistant 02', role: 'assistant', site: 'Annexe' },
  { id: 'row-read1', name: 'Lecture Seule1', role: 'read_only', site: 'Site principal' },
  { id: 'row-read2', name: 'Lecture Seule2', role: 'read_only', site: 'Annexe' },
  { id: 'row-thomas', name: 'Thomas Petit', role: 'doctor', site: 'Annexe' },
  { id: 'row-nadia', name: 'Nadia Rousseau', role: 'doctor', site: 'Site principal' },
];

const columnHelper = createColumnHelper<DemoRow>();

export function UiKitTableDemo() {
  const t = useTranslations('uiKit');
  const searchParams = useSearchParams();

  const page = Math.max(1, Number(searchParams.get('page') ?? '1') || 1);
  const pageSize = Math.max(1, Math.min(100, Number(searchParams.get('pageSize') ?? '5') || 5));
  const sortBy = searchParams.get('sortBy') ?? 'name';
  const sortDir = searchParams.get('sortDir') === 'desc' ? 'desc' : 'asc';
  const q = (searchParams.get('q') ?? '').trim().toLowerCase();

  const filtered = useMemo(() => {
    let rows = DEMO_ROWS;
    if (q) {
      rows = rows.filter(
        (row) =>
          row.name.toLowerCase().includes(q) ||
          row.role.toLowerCase().includes(q) ||
          row.site.toLowerCase().includes(q),
      );
    }
    const sorted = [...rows].sort((a, b) => {
      const key = (sortBy as keyof DemoRow) in a ? (sortBy as keyof DemoRow) : 'name';
      const left = String(a[key]);
      const right = String(b[key]);
      const cmp = left.localeCompare(right);
      return sortDir === 'desc' ? -cmp : cmp;
    });
    return sorted;
  }, [q, sortBy, sortDir]);

  const pageRows = filtered.slice((page - 1) * pageSize, page * pageSize);

  const columns = useMemo(
    () =>
      [
        columnHelper.accessor('name', {
          id: 'name',
          header: t('table.columns.name'),
          enableSorting: true,
        }),
        columnHelper.accessor('role', {
          id: 'role',
          header: t('table.columns.role'),
          enableSorting: true,
        }),
        columnHelper.accessor('site', {
          id: 'site',
          header: t('table.columns.site'),
          enableSorting: true,
        }),
      ] as ColumnDef<DemoRow>[],
    [t],
  );

  return (
    <Card {...testIdProps(testIds.uiKit.table)}>
      <CardHeader>
        <CardTitle>{t('table.title')}</CardTitle>
        <CardDescription>{t('table.description')}</CardDescription>
      </CardHeader>
      <CardContent>
        <DataTable
          columns={columns}
          data={pageRows}
          totalItems={filtered.length}
          getRowId={(row) => row.id}
          defaultSortBy="name"
          defaultPageSize={5}
          emptyTitle={t('table.emptyTitle')}
          emptyDescription={t('table.emptyDescription')}
        />
      </CardContent>
    </Card>
  );
}

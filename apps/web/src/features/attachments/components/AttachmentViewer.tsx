'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useCallback, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  fetchAttachment,
  fetchAttachmentDownloadUrl,
} from '@/features/attachments/api/attachments.api';
import type { AttachmentRead } from '@/lib/api/generated';
import { cn } from '@/lib/utils/cn';
import { testIdProps, testIds } from '@/lib/test/test-id';
import { useSession } from '@/providers/session-provider';

const STATUS_KEYS = {
  pending: 'viewer.statusValues.pending',
  processing: 'viewer.statusValues.processing',
  ready: 'viewer.statusValues.ready',
  failed: 'viewer.statusValues.failed',
} as const;

const ERROR_KEYS = {
  unauthenticated: 'viewer.errors.unauthenticated',
  load_failed: 'viewer.errors.load_failed',
} as const;

type AttachmentViewerProps = {
  attachmentPublicId: string;
  className?: string;
};

export function AttachmentViewer({ attachmentPublicId, className }: AttachmentViewerProps) {
  const t = useTranslations('attachments');
  const locale = useLocale();
  const { session } = useSession();
  const [attachment, setAttachment] = useState<AttachmentRead | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<keyof typeof ERROR_KEYS | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    if (!session?.clinicPublicId) {
      setErrorCode('unauthenticated');
      return;
    }
    setIsLoading(true);
    setErrorCode(null);
    try {
      const meta = await fetchAttachment(attachmentPublicId, locale, session.clinicPublicId);
      setAttachment(meta);
      const preferredVariant =
        meta.variants.find((item) => item.variant === 'preview')?.variant ??
        meta.variants.find((item) => item.variant === 'thumb')?.variant ??
        undefined;
      const download = await fetchAttachmentDownloadUrl(
        attachmentPublicId,
        locale,
        session.clinicPublicId,
        preferredVariant,
      );
      setImageUrl(download.download.url);
    } catch {
      setErrorCode('load_failed');
      setAttachment(null);
      setImageUrl(null);
    } finally {
      setIsLoading(false);
    }
  }, [attachmentPublicId, locale, session?.clinicPublicId]);

  return (
    <Card className={cn('overflow-hidden', className)} {...testIdProps(testIds.attachments.viewer)}>
      <CardHeader>
        <CardTitle>{t('viewer.title')}</CardTitle>
        <CardDescription>{t('viewer.description')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button
          type="button"
          onClick={() => void load()}
          disabled={isLoading}
          {...testIdProps(testIds.attachments.viewerLoad)}
        >
          {isLoading ? t('viewer.loading') : t('viewer.load')}
        </Button>
        {errorCode ? (
          <p
            className="text-sm text-destructive"
            role="alert"
            {...testIdProps(testIds.attachments.viewerError)}
          >
            {t(ERROR_KEYS[errorCode])}
          </p>
        ) : null}
        {attachment ? (
          <dl
            className="grid gap-1 text-sm text-muted-foreground"
            {...testIdProps(testIds.attachments.viewerMeta)}
          >
            <div>
              <dt className="inline font-medium text-foreground">{t('viewer.filename')}: </dt>
              <dd className="inline">{attachment.filename}</dd>
            </div>
            <div>
              <dt className="inline font-medium text-foreground">{t('viewer.status')}: </dt>
              <dd className="inline">
                {t(
                  STATUS_KEYS[
                    attachment.processingStatus as keyof typeof STATUS_KEYS
                  ] ?? STATUS_KEYS.pending,
                )}
              </dd>
            </div>
          </dl>
        ) : null}
        {imageUrl ? (
          // Pre-signed object URL; clinical photos must not mirror in RTL.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imageUrl}
            alt={attachment?.filename ?? t('viewer.imageAlt')}
            className="max-h-96 w-full rounded-lg border border-border object-contain bg-muted/40"
            {...testIdProps(testIds.attachments.viewerImage)}
          />
        ) : null}
      </CardContent>
    </Card>
  );
}

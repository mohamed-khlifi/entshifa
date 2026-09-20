import type { useTranslations } from 'next-intl';
import { z } from 'zod';

export function createLoginSchema(t: ReturnType<typeof useTranslations<'auth'>>) {
  return z.object({
    email: z
      .string()
      .min(1, { message: t('validation.emailRequired') })
      .email({ message: t('validation.emailRequired') }),
    password: z
      .string()
      .min(1, { message: t('validation.passwordRequired') })
      .min(8, { message: t('validation.passwordMin') }),
  });
}

export type LoginFormValues = z.infer<ReturnType<typeof createLoginSchema>>;

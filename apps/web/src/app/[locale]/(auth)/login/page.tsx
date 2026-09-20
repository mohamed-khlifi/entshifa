import { getTranslations } from 'next-intl/server';

import { LoginForm } from '@/features/auth/components/LoginForm';
import { testIdProps, testIds } from '@/lib/test/test-id';

export default async function LoginPage() {
  const t = await getTranslations('auth');

  return (
    <main
      className="flex min-h-screen flex-col items-center justify-center px-4"
      {...testIdProps(testIds.auth.login.root)}
    >
      <div className="w-full max-w-sm space-y-6">
        <header className="space-y-1 text-center">
          <h1 className="text-2xl font-semibold tracking-tight">{t('login.title')}</h1>
        </header>
        <LoginForm />
      </div>
    </main>
  );
}

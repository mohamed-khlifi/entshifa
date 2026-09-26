import createMiddleware from 'next-intl/middleware';
import { type NextRequest, NextResponse } from 'next/server';

import { SESSION_INDICATOR_COOKIE } from '@/lib/auth/session-token';
import { getEnabledLocales } from '@/lib/i18n/config';

import { routing } from './i18n/routing';

const intlMiddleware = createMiddleware(routing);

const localePathPattern = new RegExp(
  `^\\/(${getEnabledLocales().map((locale) => locale.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})(?=\\/|$)`,
);

function pathWithoutLocale(pathname: string): string {
  return pathname.replace(localePathPattern, '') || '/';
}

function isPublicPath(pathname: string): boolean {
  const path = pathWithoutLocale(pathname);
  return path === '/login' || path.startsWith('/login/');
}

export default function middleware(request: NextRequest): NextResponse {
  const pathname = request.nextUrl.pathname;
  const response = intlMiddleware(request);
  const hasSession = request.cookies.get(SESSION_INDICATOR_COOKIE)?.value === '1';
  const locale = pathname.split('/')[1] ?? routing.defaultLocale;

  if (!isPublicPath(pathname) && pathWithoutLocale(pathname) !== '/') {
    if (!hasSession) {
      const loginUrl = new URL(`/${locale}/login`, request.url);
      loginUrl.searchParams.set('next', pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  if (pathname.endsWith('/login') && hasSession) {
    return NextResponse.redirect(new URL(`/${locale}/home`, request.url));
  }

  return response;
}

export const config = {
  matcher: ['/', '/(en|fr|ar|en-XA)/:path*'],
};

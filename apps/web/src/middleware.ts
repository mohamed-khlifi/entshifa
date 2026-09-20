import createMiddleware from 'next-intl/middleware';
import { type NextRequest, NextResponse } from 'next/server';

import { SESSION_INDICATOR_COOKIE } from '@/lib/auth/session-token';

import { routing } from './i18n/routing';

const intlMiddleware = createMiddleware(routing);

const protectedMatchers = ['/home'];

function isProtectedPath(pathname: string): boolean {
  const withoutLocale = pathname.replace(/^\/(en|fr)(?=\/|$)/, '') || '/';
  return protectedMatchers.some(
    (segment) =>
      withoutLocale === segment || withoutLocale.startsWith(`${segment}/`),
  );
}

export default function middleware(request: NextRequest): NextResponse {
  const pathname = request.nextUrl.pathname;
  const response = intlMiddleware(request);

  if (isProtectedPath(pathname)) {
    const hasSession = request.cookies.get(SESSION_INDICATOR_COOKIE)?.value === '1';
    if (!hasSession) {
      const locale = pathname.split('/')[1] ?? routing.defaultLocale;
      const loginUrl = new URL(`/${locale}/login`, request.url);
      loginUrl.searchParams.set('next', pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  if (pathname.endsWith('/login')) {
    const hasSession = request.cookies.get(SESSION_INDICATOR_COOKIE)?.value === '1';
    if (hasSession) {
      const locale = pathname.split('/')[1] ?? routing.defaultLocale;
      return NextResponse.redirect(new URL(`/${locale}/home`, request.url));
    }
  }

  return response;
}

export const config = {
  matcher: ['/', '/(en|fr)/:path*'],
};

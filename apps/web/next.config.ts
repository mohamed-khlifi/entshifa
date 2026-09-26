import type { NextConfig } from 'next';
import createNextIntlPlugin from 'next-intl/plugin';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const withNextIntl = createNextIntlPlugin('./src/lib/i18n/request.ts');

const apiOrigin = process.env.API_URL ?? 'http://127.0.0.1:8000';
const monorepoRoot = path.join(path.dirname(fileURLToPath(import.meta.url)), '../..');

const nextConfig: NextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: monorepoRoot,
  // Catalogs live in packages/i18n-messages (outside apps/web).
  experimental: {
    externalDir: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${apiOrigin}/api/:path*`,
      },
    ];
  },
};

export default withNextIntl(nextConfig);

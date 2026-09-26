import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { FlatCompat } from '@eslint/eslintrc';

const baseDirectory = dirname(fileURLToPath(import.meta.url));

const compat = new FlatCompat({ baseDirectory });

export default [
  {
    ignores: ['**/.next/**', '**/node_modules/**', '**/playwright-report/**'],
  },
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  {
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['@/features/*/*', '@/features/*/*/**'],
              message:
                'Import from the feature barrel (@/features/<domain>) only.',
            },
          ],
        },
      ],
      'no-restricted-syntax': [
        'error',
        {
          selector:
            'JSXAttribute[name.name="data-testid"] Literal[value.type="Literal"]',
          message:
            'Use testIdProps() and testIds from lib/test/test-id.ts instead of inline data-testid literals.',
        },
      ],
    },
  },
  {
    files: ['src/lib/test/**/*.ts', 'src/lib/test/**/*.tsx'],
    rules: {
      'no-restricted-syntax': 'off',
    },
  },
];

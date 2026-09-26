import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { FlatCompat } from "@eslint/eslintrc";

const baseDirectory = dirname(fileURLToPath(import.meta.url));

const compat = new FlatCompat({ baseDirectory });

/** Pages and other features import `@/features/<domain>` only. Same-feature files may import their own internals. */
const featureImportBoundary = {
  meta: {
    type: "problem",
    schema: [],
    messages: {
      deep: "Import from the feature barrel (@/features/{{domain}}) only.",
    },
  },
  create(context) {
    return {
      ImportDeclaration(node) {
        const source = node.source && node.source.value;
        if (typeof source !== "string" || !source.startsWith("@/features/")) {
          return;
        }
        const rest = source.slice("@/features/".length);
        const slash = rest.indexOf("/");
        if (slash === -1) {
          return;
        }
        const domain = rest.slice(0, slash);
        const filename = String(context.filename ?? "").replaceAll("\\", "/");
        if (filename.includes(`/src/features/${domain}/`)) {
          return;
        }
        context.report({
          node: node.source,
          messageId: "deep",
          data: { domain },
        });
      },
    };
  },
};

export default [
  {
    ignores: ["**/.next/**", "**/node_modules/**", "**/playwright-report/**"],
  },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    plugins: {
      "ent-boundaries": {
        rules: {
          "feature-imports": featureImportBoundary,
        },
      },
    },
    rules: {
      "ent-boundaries/feature-imports": "error",
      "no-restricted-syntax": [
        "error",
        {
          selector:
            'JSXAttribute[name.name="data-testid"] Literal[value.type="Literal"]',
          message:
            "Use testIdProps() and testIds from lib/test/test-id.ts instead of inline data-testid literals.",
        },
      ],
    },
  },
  {
    files: ["src/lib/test/**/*.ts", "src/lib/test/**/*.tsx"],
    rules: {
      "no-restricted-syntax": "off",
    },
  },
];

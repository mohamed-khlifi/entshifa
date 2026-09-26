import { test, expect } from "@playwright/test";

import { testIds } from "../src/lib/test/test-id";

const locales = ["en", "fr", "ar"] as const;

for (const locale of locales) {
  test(`login shell renders (${locale})`, async ({ page }) => {
    await page.goto(`/${locale}/login`);
    await expect(page.getByTestId(testIds.auth.login.root)).toBeVisible();
    await expect(page.getByTestId(testIds.auth.login.email)).toBeVisible();
    await expect(page.getByTestId(testIds.auth.login.submit)).toBeVisible();
  });
}

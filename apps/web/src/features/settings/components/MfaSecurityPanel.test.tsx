import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { testIds } from "@/lib/test/test-id";
import settings from "../../../../../../packages/i18n-messages/en/settings.json";

import { MfaSecurityPanel } from "./MfaSecurityPanel";

const provisioningUri =
  "otpauth://totp/EntShifa:doctor1%40demo.entshifa.local?secret=SECRET&issuer=EntShifa";

vi.mock("qrcode", () => ({
  default: {
    toDataURL: vi.fn(async (value: string) => `data:image/png;base64,${value}`),
  },
}));

vi.mock("@/providers/session-provider", () => ({
  useSession: () => ({
    session: { clinicPublicId: "01CLINIC000000000000000000" },
  }),
}));

vi.mock("@/features/auth", () => ({
  useMeQuery: () => ({ data: { mfaEnabled: false } }),
  enrollMfa: vi.fn(async () => ({
    secret: "SECRET",
    provisioningUri,
  })),
  confirmMfa: vi.fn(),
  disableMfa: vi.fn(),
}));

afterEach(() => {
  cleanup();
});

describe("MfaSecurityPanel", () => {
  it("draws the authenticator setup link as a QR image", async () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <NextIntlClientProvider locale="en" messages={{ settings }}>
          <MfaSecurityPanel />
        </NextIntlClientProvider>
      </QueryClientProvider>,
    );

    fireEvent.click(screen.getByTestId(testIds.settings.mfaEnroll));

    const image = await screen.findByTestId(testIds.settings.mfaQr);
    await waitFor(() => {
      expect(image.getAttribute("src")).toContain("data:image/png;base64,");
      expect(image.getAttribute("alt")).toBe(settings.security.qrAlt);
    });
    expect(screen.getByText("SECRET")).toBeTruthy();
    expect(screen.queryByText(provisioningUri)).toBeNull();
  });
});

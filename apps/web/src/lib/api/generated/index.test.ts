import { describe, expect, it } from "vitest";

import type { LoginRequest, LoginResponse, MeResponse } from "./index";

describe("generated API types", () => {
  it("exposes camelCase auth wire shapes", () => {
    const loginRequest: LoginRequest = {
      email: "admin@demo.entshifa.local",
      password: "LocalDevSeed1!",
    };
    const loginResponse: LoginResponse = {
      accessToken: "token",
      tokenType: "bearer",
      expiresInMinutes: 15,
      session: {
        userPublicId: "01USER",
        clinicPublicId: "01CLINIC",
        sessionPublicId: "01SESSION",
      },
    };
    const me: MeResponse = {
      userPublicId: loginResponse.session.userPublicId,
      clinicPublicId: loginResponse.session.clinicPublicId,
      permissions: ["auth.session.read"],
    };

    expect(loginRequest.email).toContain("@");
    expect(me.permissions).toHaveLength(1);
  });
});

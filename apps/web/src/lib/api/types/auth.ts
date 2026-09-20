/** Temporary auth wire types until P0-12 generated contracts land. */

export type SessionPayload = {
  userPublicId: string;
  clinicPublicId: string;
  sessionPublicId: string;
};

export type LoginResponse = {
  accessToken: string;
  tokenType: string;
  expiresInMinutes: number;
  session: SessionPayload;
};

export type MeResponse = {
  userPublicId: string;
  clinicPublicId: string;
  permissions: string[];
};

export type LoginRequest = {
  email: string;
  password: string;
};

/** RFC 7807 problem details from the API. */

export type AppError = {
  code: string;
  status: number;
  context: Record<string, unknown>;
  requestId?: string;
};

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly context: Record<string, unknown>;
  readonly requestId?: string;

  constructor(payload: AppError) {
    super(payload.code);
    this.name = "ApiError";
    this.code = payload.code;
    this.status = payload.status;
    this.context = payload.context;
    this.requestId = payload.requestId;
  }
}

export async function parseApiError(response: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    return new ApiError({
      code: "internal_error",
      status: response.status,
      context: {},
    });
  }
  if (typeof body === "object" && body !== null && "code" in body) {
    const record = body as Record<string, unknown>;
    return new ApiError({
      code: String(record.code),
      status: Number(record.status ?? response.status),
      context: (record.context as Record<string, unknown>) ?? {},
      requestId: record.requestId ? String(record.requestId) : undefined,
    });
  }
  return new ApiError({
    code: "internal_error",
    status: response.status,
    context: {},
  });
}

type ErrorTranslator = (messageKey: string) => string;

/**
 * Maps an API error `code` (e.g. `auth.invalid_credentials`) to a next-intl key
 * under the `errors` namespace. Dotted API codes use nested message objects, not
 * flat keys containing ".".
 */
export function apiErrorCodeToMessageKey(code: string): string {
  const dotIndex = code.indexOf(".");
  if (dotIndex === -1) {
    return code;
  }
  const namespace = code.slice(0, dotIndex);
  const leaf = code.slice(dotIndex + 1);
  return `${namespace}.${leaf}`;
}

export function resolveErrorMessage(
  error: ApiError,
  translate: ErrorTranslator,
  hasMessageKey: (messageKey: string) => boolean = () => true,
): string {
  const messageKey = apiErrorCodeToMessageKey(error.code);
  if (hasMessageKey(messageKey)) {
    const localized = translate(messageKey);
    if (localized !== messageKey) {
      return localized;
    }
  }
  if (hasMessageKey("generic")) {
    return translate("generic");
  }
  return error.code;
}

import { describe, expect, it } from "vitest";

import {
  insertAtSelection,
  placeholderToken,
} from "@/features/documents/lib/insert-placeholder";

describe("insertAtSelection", () => {
  it("inserts a placeholder at the caret", () => {
    const token = placeholderToken("patient.fullName");
    const result = insertAtSelection("<p></p>", 3, 3, token);
    expect(result.value).toBe("<p>{{ patient.fullName }}</p>");
    expect(result.cursor).toBe(3 + token.length);
  });
});

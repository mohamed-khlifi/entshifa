import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

import { larynxMap } from "./larynx.map";

describe("larynx map", () => {
  it("binds every region to an svg path", () => {
    const svg = readFileSync(
      path.join(process.cwd(), "public/anatomy/larynx.svg"),
      "utf8",
    );
    for (const region of larynxMap.regions) {
      expect(svg).toContain(`id="${region.pathId}"`);
    }
    expect(larynxMap.regions).toHaveLength(17);
  });
});

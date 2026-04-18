import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  describe,
  expect,
  it,
} from "vitest";

describe("phi layout scale contract", () => {
  it("3.9 defines phi-derived spacing and module rhythm tokens with explicit usage", () => {
    const stylesSourcePath = resolve(process.cwd(), "src/app/styles.css");
    expect(existsSync(stylesSourcePath)).toBe(true);
    if (!existsSync(stylesSourcePath)) {
      return;
    }

    const stylesSource = readFileSync(stylesSourcePath, "utf8");

    const requiredPhiTokens = [
      "--phi-ratio: 1.613",
      "--space-1: 8px",
      "--space-2: 13px",
      "--space-3: 21px",
      "--space-4: 34px",
      "--space-5: 55px",
      "--module-height-compact: 233px",
      "--module-height-standard: 377px",
      "--module-height-expanded: 610px",
    ];

    for (const requiredPhiToken of requiredPhiTokens) {
      expect(stylesSource.includes(requiredPhiToken)).toBe(true);
    }

    expect(stylesSource.includes("min-height: var(--module-height-standard);")).toBe(true);
    expect(stylesSource.includes("min-height: var(--module-height-compact);")).toBe(true);
  });
});

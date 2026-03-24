import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import {
  describe,
  expect,
  it,
} from "vitest";

const stylesPath = fileURLToPath(new URL("./styles.css", import.meta.url));
const stylesContent = readFileSync(stylesPath, "utf8");

describe("reduced-motion CSS contract", () => {
  it("does not load primary typography through runtime stylesheet imports", () => {
    expect(stylesContent).not.toMatch(/@import\s+url\(/);
  });

  it("disables animations and transitions under prefers-reduced-motion", () => {
    const reducedMotionBlockRegex =
      /@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{[\s\S]*animation:\s*none\s*!important;[\s\S]*transition:\s*none\s*!important;[\s\S]*\}/m;

    expect(stylesContent).toMatch(reducedMotionBlockRegex);
  });
});

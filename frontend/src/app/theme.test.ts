import {
  describe,
  expect,
  it,
} from "vitest";

import { resolvePreferredTheme } from "./theme";

describe("resolvePreferredTheme", () => {
  it("prefers a stored theme when present", () => {
    expect(
      resolvePreferredTheme({
        storedTheme: "dark",
        prefersDark: false,
      }),
    ).toBe("dark");
  });

  it("falls back to system preference when no stored theme exists", () => {
    expect(
      resolvePreferredTheme({
        storedTheme: null,
        prefersDark: true,
      }),
    ).toBe("dark");
  });

  it("falls back to light when stored theme is invalid and system preference is light", () => {
    expect(
      resolvePreferredTheme({
        storedTheme: "sepia",
        prefersDark: false,
      }),
    ).toBe("light");
  });
});

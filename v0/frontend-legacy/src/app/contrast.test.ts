import {
  describe,
  expect,
  it,
} from "vitest";

type ThemeTokens = {
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  accent: string;
  warning: string;
  surface: string;
  accentSoft: string;
  warningSoft: string;
};

const lightThemeTokens: ThemeTokens = {
  textPrimary: "#102033",
  textSecondary: "#476074",
  textMuted: "#5b758a",
  accent: "#114fcf",
  warning: "#8a5c00",
  surface: "#ffffff",
  accentSoft: "#dbe7fc",
  warningSoft: "#f4e8d0",
};

const darkThemeTokens: ThemeTokens = {
  textPrimary: "#edf4fb",
  textSecondary: "#b6c8d9",
  textMuted: "#89a2b8",
  accent: "#6fa8ff",
  warning: "#f6be5f",
  surface: "#0e1f2f",
  accentSoft: "#203752",
  warningSoft: "#463b29",
};

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const normalized = hex.replace("#", "");
  const value = Number.parseInt(normalized, 16);
  return {
    r: (value >> 16) & 0xff,
    g: (value >> 8) & 0xff,
    b: value & 0xff,
  };
}

function toRelativeChannel(channel: number): number {
  const normalized = channel / 255;
  return normalized <= 0.03928
    ? normalized / 12.92
    : ((normalized + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(hex: string): number {
  const { r, g, b } = hexToRgb(hex);
  return (
    0.2126 * toRelativeChannel(r) +
    0.7152 * toRelativeChannel(g) +
    0.0722 * toRelativeChannel(b)
  );
}

function contrastRatio(foreground: string, background: string): number {
  const foregroundLuminance = relativeLuminance(foreground);
  const backgroundLuminance = relativeLuminance(background);
  const lighter = Math.max(foregroundLuminance, backgroundLuminance);
  const darker = Math.min(foregroundLuminance, backgroundLuminance);
  return (lighter + 0.05) / (darker + 0.05);
}

function expectMinContrast(
  foreground: string,
  background: string,
  minRatio = 4.5,
): void {
  expect(contrastRatio(foreground, background)).toBeGreaterThanOrEqual(minRatio);
}

describe("theme token contrast", () => {
  it("keeps AA-oriented text and badge contrast in the light theme", () => {
    expectMinContrast(lightThemeTokens.textPrimary, lightThemeTokens.surface);
    expectMinContrast(lightThemeTokens.textSecondary, lightThemeTokens.surface);
    expectMinContrast(lightThemeTokens.textMuted, lightThemeTokens.surface);
    expectMinContrast(lightThemeTokens.accent, lightThemeTokens.accentSoft);
    expectMinContrast(lightThemeTokens.warning, lightThemeTokens.warningSoft);
  });

  it("keeps AA-oriented text and badge contrast in the dark theme", () => {
    expectMinContrast(darkThemeTokens.textPrimary, darkThemeTokens.surface);
    expectMinContrast(darkThemeTokens.textSecondary, darkThemeTokens.surface);
    expectMinContrast(darkThemeTokens.textMuted, darkThemeTokens.surface);
    expectMinContrast(darkThemeTokens.accent, darkThemeTokens.accentSoft);
    expectMinContrast(darkThemeTokens.warning, darkThemeTokens.warningSoft);
  });
});

/* @vitest-environment jsdom */

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("dashboard visual system fail-first contract", () => {
  it("1.1 defines lens-aware tokens for accent, surface, border, and semantic status usage", () => {
    const stylesPath = resolve(process.cwd(), "src/app/styles.css");
    expect(
      existsSync(stylesPath),
      "Fail-first baseline: missing frontend style token source for dashboard visual system.",
    ).toBe(true);

    const stylesSource = readFileSync(stylesPath, "utf8");
    const requiredTokens = [
      "--lens-overview-accent",
      "--lens-overview-surface",
      "--lens-overview-border",
      "--lens-holdings-accent",
      "--lens-performance-accent",
      "--lens-cash-transactions-accent",
      "--status-semantic-favorable",
      "--status-semantic-caution",
      "--status-semantic-unfavorable",
    ];

    for (const token of requiredTokens) {
      expect(
        stylesSource.includes(token),
        `Fail-first baseline: missing dashboard visual-system token ${token}.`,
      ).toBe(true);
    }
  });

  it("1.2 defines reusable hero/standard/utility panel hierarchy semantics", () => {
    const chartPanelPath = resolve(
      process.cwd(),
      "src/components/charts/WorkspaceChartPanel.tsx",
    );
    const primaryJobPath = resolve(
      process.cwd(),
      "src/components/workspace-layout/WorkspacePrimaryJobPanel.tsx",
    );

    expect(existsSync(chartPanelPath)).toBe(true);
    expect(existsSync(primaryJobPath)).toBe(true);

    const chartPanelSource = readFileSync(chartPanelPath, "utf8");
    const primaryJobSource = readFileSync(primaryJobPath, "utf8");

    expect(chartPanelSource.includes("data-panel-hierarchy")).toBe(true);
    expect(chartPanelSource.includes('"hero" | "standard" | "utility"')).toBe(true);
    expect(primaryJobSource.includes('hierarchy = "hero"')).toBe(true);
    expect(primaryJobSource.includes("data-panel-hierarchy")).toBe(true);
  });

  it("1.3 defines typography roles for narrative, ui, and tabular numeric rhythm", () => {
    const stylesPath = resolve(process.cwd(), "src/app/styles.css");
    const stylesSource = readFileSync(stylesPath, "utf8");

    expect(stylesSource.includes("--font-role-narrative")).toBe(true);
    expect(stylesSource.includes("--font-role-ui")).toBe(true);
    expect(stylesSource.includes("--font-role-numeric")).toBe(true);
    expect(stylesSource.includes("font-variant-numeric: tabular-nums")).toBe(true);
  });

  it("1.2 includes lifecycle-state surfaces for loading, empty, stale, unavailable, and error", () => {
    const lifecycleCopyPath = resolve(
      process.cwd(),
      "src/features/portfolio-workspace/state-copy.ts",
    );
    const stateBannerPath = resolve(
      process.cwd(),
      "src/components/workspace-layout/WorkspaceStateBanner.tsx",
    );

    expect(existsSync(lifecycleCopyPath)).toBe(true);
    expect(existsSync(stateBannerPath)).toBe(true);

    const lifecycleCopySource = readFileSync(lifecycleCopyPath, "utf8");
    const stateBannerSource = readFileSync(stateBannerPath, "utf8");

    for (const state of ["loading", "empty", "stale", "unavailable", "error"] as const) {
      expect(
        lifecycleCopySource.includes(`${state}:`),
        `Fail-first baseline: missing lifecycle state copy for ${state}.`,
      ).toBe(true);
    }

    expect(stateBannerSource.includes("data-lifecycle-state")).toBe(true);
  });
});

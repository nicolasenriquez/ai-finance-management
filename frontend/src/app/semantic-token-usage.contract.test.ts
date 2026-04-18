import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  describe,
  expect,
  it,
} from "vitest";

describe("semantic token usage contract", () => {
  it("4.15 keeps route-level components free of raw hex/rgb styling values", () => {
    const routeFiles = [
      "src/pages/portfolio-home-page/PortfolioHomePage.tsx",
      "src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.tsx",
      "src/pages/portfolio-risk-page/PortfolioRiskPage.tsx",
      "src/pages/portfolio-signals-page/components/PortfolioSignalsRouteView.tsx",
      "src/pages/portfolio-asset-detail-page/components/PortfolioAssetDetailRouteView.tsx",
      "src/components/shell/CompactDashboardShell.tsx",
    ];

    const rawColorPattern = /#[0-9a-fA-F]{3,8}|rgb\(|rgba\(/;

    for (const routeFile of routeFiles) {
      const routeSource = readFileSync(resolve(process.cwd(), routeFile), "utf8");
      expect(rawColorPattern.test(routeSource)).toBe(false);
      expect(routeSource.includes("purple")).toBe(false);
      expect(routeSource.includes("indigo")).toBe(false);
    }
  });

  it("4.15 defines semantic route token aliases and removes hardcoded route hex styling from stylesheet", () => {
    const stylesSource = readFileSync(
      resolve(process.cwd(), "src/app/styles.css"),
      "utf8",
    );

    expect(stylesSource.includes("--color-surface-base")).toBe(true);
    expect(stylesSource.includes("--color-border-default")).toBe(true);
    expect(stylesSource.includes("--space-route-gutter")).toBe(true);
    expect(stylesSource.includes("--radius-route-card")).toBe(true);
    expect(stylesSource.includes("--font-route-body")).toBe(true);
    expect(stylesSource.includes("#6d28d9")).toBe(false);
    expect(stylesSource.includes("#7c3aed")).toBe(false);
  });
});

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  describe,
  expect,
  it,
} from "vitest";

describe("route performance orchestration contract (fail-first)", () => {
  it("1.2/2.* keeps first-surface route orchestration in dedicated query hooks with TanStack ownership", () => {
    const homeHookPath = resolve(
      process.cwd(),
      "src/pages/portfolio-home-page/hooks/usePortfolioHomeRouteData.ts",
    );
    const analyticsHookPath = resolve(
      process.cwd(),
      "src/pages/portfolio-analytics-page/hooks/usePortfolioAnalyticsRouteData.ts",
    );
    const signalsHookPath = resolve(
      process.cwd(),
      "src/pages/portfolio-signals-page/hooks/usePortfolioSignalsRouteState.ts",
    );
    const riskHookPath = resolve(
      process.cwd(),
      "src/pages/portfolio-risk-page/hooks/usePortfolioRiskRouteData.ts",
    );

    expect(existsSync(homeHookPath)).toBe(true);
    expect(existsSync(analyticsHookPath)).toBe(true);
    expect(existsSync(signalsHookPath)).toBe(true);
    expect(existsSync(riskHookPath)).toBe(true);

    const homeHookSource = readFileSync(homeHookPath, "utf8");
    const analyticsHookSource = readFileSync(analyticsHookPath, "utf8");
    const signalsHookSource = readFileSync(signalsHookPath, "utf8");
    const riskHookSource = readFileSync(riskHookPath, "utf8");

    expect(homeHookSource.includes("useQueries")).toBe(true);
    expect(homeHookSource.includes("fetchPortfolioTimeSeriesResponse")).toBe(true);

    expect(analyticsHookSource.includes("useQueries")).toBe(true);
    expect(signalsHookSource.includes("useQueries")).toBe(true);
    expect(riskHookSource.includes("useQueries")).toBe(true);
  });

  it("1.3 preserves Opportunities label mapped to canonical /portfolio/signals slug", () => {
    const shellSourcePath = resolve(
      process.cwd(),
      "src/components/shell/CompactDashboardShell.tsx",
    );
    const signalsViewSourcePath = resolve(
      process.cwd(),
      "src/pages/portfolio-signals-page/components/PortfolioSignalsRouteView.tsx",
    );
    const shellSource = readFileSync(shellSourcePath, "utf8");
    const signalsViewSource = readFileSync(signalsViewSourcePath, "utf8");

    expect(shellSource.includes('label: "Opportunities"')).toBe(true);
    expect(shellSource.includes('pathPattern: "/portfolio/signals"')).toBe(true);
    expect(shellSource.includes('href: "/portfolio/signals"')).toBe(true);
    expect(signalsViewSource.includes("Secondary tactical overlay")).toBe(true);
  });
});

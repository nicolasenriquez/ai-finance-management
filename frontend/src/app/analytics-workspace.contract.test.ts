/* @vitest-environment jsdom */

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { appRouter } from "./router";

type WorkspaceRouteContract = {
  routeName: string;
  path: string;
  pageFile: string;
  testFile: string;
};

const workspaceContracts: WorkspaceRouteContract[] = [
  {
    routeName: "Home",
    path: "/portfolio/home",
    pageFile: "src/pages/portfolio-home-page/PortfolioHomePage.tsx",
    testFile: "src/pages/portfolio-home-page/PortfolioHomePage.test.tsx",
  },
  {
    routeName: "Analytics",
    path: "/portfolio/analytics",
    pageFile: "src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.tsx",
    testFile: "src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.test.tsx",
  },
  {
    routeName: "Risk",
    path: "/portfolio/risk",
    pageFile: "src/pages/portfolio-risk-page/PortfolioRiskPage.tsx",
    testFile: "src/pages/portfolio-risk-page/PortfolioRiskPage.test.tsx",
  },
  {
    routeName: "Quant/Reports",
    path: "/portfolio/reports",
    pageFile: "src/pages/portfolio-reports-page/PortfolioReportsPage.tsx",
    testFile: "src/pages/portfolio-reports-page/PortfolioReportsPage.test.tsx",
  },
  {
    routeName: "Transactions",
    path: "/portfolio/transactions",
    pageFile: "src/pages/portfolio-transactions-page/PortfolioTransactionsPage.tsx",
    testFile: "src/pages/portfolio-transactions-page/PortfolioTransactionsPage.test.tsx",
  },
];

function getRegisteredRouterPaths(): Set<string> {
  return new Set(
    appRouter.routes
      .map((route) => route.path)
      .filter((pathValue): pathValue is string => typeof pathValue === "string"),
  );
}

describe("analytics workspace route contract", () => {
  it("registers canonical workspace paths while preserving existing portfolio routes", () => {
    const registeredPaths = getRegisteredRouterPaths();
    const missingPaths = workspaceContracts
      .map((contract) => contract.path)
      .filter((pathValue) => !registeredPaths.has(pathValue));

    expect(
      missingPaths,
      "Fail-first baseline: add Home/Analytics/Risk/Transactions routes in app router.",
    ).toEqual([]);
  });

  it.each(workspaceContracts)(
    "defines explicit loading/empty/error state coverage artifacts for $routeName",
    ({ routeName, pageFile, testFile }) => {
      const absolutePagePath = resolve(process.cwd(), pageFile);
      const absoluteTestPath = resolve(process.cwd(), testFile);

      expect(
        existsSync(absolutePagePath),
        `Fail-first baseline: missing ${routeName} page module at ${pageFile}.`,
      ).toBe(true);
      expect(
        existsSync(absoluteTestPath),
        `Fail-first baseline: missing ${routeName} route-state test at ${testFile}.`,
      ).toBe(true);

      const pageSource = readFileSync(absolutePagePath, "utf8");
      expect(
        pageSource.includes("ErrorBanner"),
        `Fail-first baseline: ${routeName} page must render explicit error state.`,
      ).toBe(true);
      expect(
        pageSource.includes("EmptyState"),
        `Fail-first baseline: ${routeName} page must render explicit empty state.`,
      ).toBe(true);
      expect(
        pageSource.includes("isLoading"),
        `Fail-first baseline: ${routeName} page must render explicit loading state.`,
      ).toBe(true);

      const testSource = readFileSync(absoluteTestPath, "utf8").toLowerCase();
      expect(
        testSource.includes("loading"),
        `Fail-first baseline: ${routeName} tests must cover loading behavior.`,
      ).toBe(true);
      expect(
        testSource.includes("empty"),
        `Fail-first baseline: ${routeName} tests must cover empty behavior.`,
      ).toBe(true);
      expect(
        testSource.includes("error"),
        `Fail-first baseline: ${routeName} tests must cover error behavior.`,
      ).toBe(true);
    },
  );
});

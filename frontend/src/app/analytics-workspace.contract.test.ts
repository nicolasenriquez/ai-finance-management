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
  requiresPrimaryJob: boolean;
};

const workspaceContracts: WorkspaceRouteContract[] = [
  {
    routeName: "Home",
    path: "/portfolio/home",
    pageFile: "src/pages/portfolio-home-page/PortfolioHomePage.tsx",
    testFile: "src/pages/portfolio-home-page/PortfolioHomePage.test.tsx",
    requiresPrimaryJob: true,
  },
  {
    routeName: "Analytics",
    path: "/portfolio/analytics",
    pageFile: "src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.tsx",
    testFile: "src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.test.tsx",
    requiresPrimaryJob: true,
  },
  {
    routeName: "Risk",
    path: "/portfolio/risk",
    pageFile: "src/pages/portfolio-risk-page/PortfolioRiskPage.tsx",
    testFile: "src/pages/portfolio-risk-page/PortfolioRiskPage.test.tsx",
    requiresPrimaryJob: true,
  },
  {
    routeName: "Quant/Reports",
    path: "/portfolio/reports",
    pageFile: "src/pages/portfolio-reports-page/PortfolioReportsPage.tsx",
    testFile: "src/pages/portfolio-reports-page/PortfolioReportsPage.test.tsx",
    requiresPrimaryJob: true,
  },
  {
    routeName: "Transactions",
    path: "/portfolio/transactions",
    pageFile: "src/pages/portfolio-transactions-page/PortfolioTransactionsPage.tsx",
    testFile: "src/pages/portfolio-transactions-page/PortfolioTransactionsPage.test.tsx",
    requiresPrimaryJob: false,
  },
];

type RouterLikeRoute = {
  path?: string;
  children?: RouterLikeRoute[];
  index?: boolean;
};

function collectRouterPaths(
  routes: RouterLikeRoute[],
  basePath = "",
): Set<string> {
  const paths = new Set<string>();

  for (const route of routes) {
    const routePath = route.path;
    const normalizedRoutePath =
      typeof routePath === "string" ? routePath.trim() : "";
    const nextBasePath = normalizedRoutePath.startsWith("/")
      ? normalizedRoutePath
      : normalizedRoutePath.length > 0
        ? `${basePath.replace(/\/$/, "")}/${normalizedRoutePath}`
        : basePath;

    if (normalizedRoutePath.length > 0) {
      paths.add(nextBasePath);
    }

    if (Array.isArray(route.children) && route.children.length > 0) {
      const childPaths = collectRouterPaths(route.children, nextBasePath);
      for (const childPath of childPaths) {
        paths.add(childPath);
      }
    }
  }

  return paths;
}

function getRegisteredRouterPaths(): Set<string> {
  return collectRouterPaths(appRouter.routes as RouterLikeRoute[]);
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
    ({ routeName, pageFile, testFile, requiresPrimaryJob }) => {
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
      if (requiresPrimaryJob) {
        expect(
          pageSource.includes("WorkspacePrimaryJobPanel"),
          `Fail-first baseline: ${routeName} page must expose one primary first-viewport analytical action panel.`,
        ).toBe(true);
      }

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

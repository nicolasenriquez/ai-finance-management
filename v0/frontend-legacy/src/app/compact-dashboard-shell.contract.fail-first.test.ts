/* @vitest-environment jsdom */

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import {
  DASHBOARD_ROUTE_GOVERNANCE,
  resolveFirstViewportTemplate,
} from "../features/portfolio-workspace/dashboard-governance";
import { appRouter } from "./router";

type RouterLikeRoute = {
  path?: string;
  children?: RouterLikeRoute[];
};

const COMPACT_PRIMARY_ROUTE_PATHS = [
  "/portfolio/home",
  "/portfolio/analytics",
  "/portfolio/risk",
  "/portfolio/signals",
  "/portfolio/asset-detail/:ticker",
] as const;

function collectRouterPaths(
  routes: RouterLikeRoute[],
  basePath = "",
): Set<string> {
  const paths = new Set<string>();

  for (const route of routes) {
    const routePath = typeof route.path === "string" ? route.path.trim() : "";
    const nextBasePath = routePath.startsWith("/")
      ? routePath
      : routePath.length > 0
        ? `${basePath.replace(/\/$/, "")}/${routePath}`
        : basePath;

    if (routePath.length > 0) {
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

describe("compact dashboard shell fail-first contract", () => {
  it("1.2 routes root traffic to /portfolio/home and registers the five-route compact shell", () => {
    const routerSourcePath = resolve(process.cwd(), "src/app/router.tsx");
    expect(
      existsSync(routerSourcePath),
      "Fail-first baseline: missing router source for compact-shell route contract checks.",
    ).toBe(true);

    const routerSource = readFileSync(routerSourcePath, "utf8");
    expect(
      routerSource.includes('to="/portfolio/home"'),
      "Fail-first baseline: root navigation must default to `/portfolio/home`.",
    ).toBe(true);

    const registeredPaths = collectRouterPaths(appRouter.routes as RouterLikeRoute[]);
    const missingPaths = COMPACT_PRIMARY_ROUTE_PATHS.filter(
      (routePath) => !registeredPaths.has(routePath),
    );
    expect(
      missingPaths,
      "Fail-first baseline: compact shell must expose `/portfolio/home|analytics|risk|signals|asset-detail/:ticker` routes.",
    ).toEqual([]);
  });

  it("1.2 keeps non-home routes behind progressive disclosure with first-viewport contracts", () => {
    const routeByPath = new Map(
      DASHBOARD_ROUTE_GOVERNANCE.map((routeGovernance) => [
        routeGovernance.path,
        routeGovernance,
      ]),
    );

    for (const routePath of COMPACT_PRIMARY_ROUTE_PATHS) {
      const routeGovernance = routeByPath.get(routePath);
      expect(
        routeGovernance,
        `Fail-first baseline: missing governance entry for ${routePath}.`,
      ).toBeDefined();
      if (!routeGovernance) {
        continue;
      }

      const firstViewportTemplate = resolveFirstViewportTemplate(routeGovernance);
      expect(
        firstViewportTemplate,
        `Fail-first baseline: ${routePath} must define a first-viewport decision template.`,
      ).not.toBeNull();
      if (!firstViewportTemplate) {
        continue;
      }

      expect(firstViewportTemplate.sequence).toEqual([
        "overview",
        "drill-down",
        "evidence",
      ]);
      expect(firstViewportTemplate.supportingModuleBudgetMax <= 4).toBe(true);

      if (routePath !== "/portfolio/home") {
        expect(
          routeGovernance.progressiveDisclosureRequired,
          `Fail-first baseline: ${routePath} must enable route-specific progressive disclosure for dense research modules.`,
        ).toBe(true);
      }
    }
  });

  it("1.2 encodes bounded first-viewport and non-scroll-first decision visibility metadata", () => {
    const governancePath = resolve(
      process.cwd(),
      "src/features/portfolio-workspace/dashboard-governance.ts",
    );

    expect(
      existsSync(governancePath),
      "Fail-first baseline: missing dashboard governance source.",
    ).toBe(true);

    const governanceSource = readFileSync(governancePath, "utf8");
    expect(
      governanceSource.includes("firstViewportHeightBudgetPx"),
      "Fail-first baseline: add explicit first viewport height budget metadata per compact route.",
    ).toBe(true);
    expect(
      governanceSource.includes("nonScrollFirstDecisionVisible"),
      "Fail-first baseline: add explicit non-scroll-first decision visibility metadata per compact route.",
    ).toBe(true);
  });
});

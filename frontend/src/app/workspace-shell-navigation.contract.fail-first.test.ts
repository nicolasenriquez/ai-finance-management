/* @vitest-environment jsdom */

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { appRouter } from "./router";

type RouterLikeNode = {
  path?: string;
  children?: RouterLikeNode[];
};

function findTopLevelPortfolioShellRoute():
  | (RouterLikeNode & { children: RouterLikeNode[] })
  | undefined {
  return appRouter.routes.find((route) => {
    const typedRoute = route as RouterLikeNode;
    return typedRoute.path === "/portfolio" && Array.isArray(typedRoute.children);
  }) as (RouterLikeNode & { children: RouterLikeNode[] }) | undefined;
}

describe("workspace shell navigation fail-first contract", () => {
  it("2.1 nests primary workspace routes under one persistent /portfolio shell route", () => {
    const shellRoute = findTopLevelPortfolioShellRoute();
    expect(
      shellRoute,
      "Fail-first baseline: router must expose one `/portfolio` parent route with children so shell framing persists across route transitions.",
    ).toBeDefined();

    const childPaths = new Set(
      (shellRoute?.children || [])
        .map((childRoute) => childRoute.path)
        .filter((pathValue): pathValue is string => typeof pathValue === "string"),
    );

    expect(
      Array.from(childPaths),
      "Fail-first baseline: `/portfolio` shell route must include child paths for home/analytics/risk/reports/copilot/transactions.",
    ).toEqual(
      expect.arrayContaining([
        "home",
        "analytics",
        "risk",
        "reports",
        "copilot",
        "transactions",
      ]),
    );
  });

  it("2.1 keeps a dedicated shell contract test artifact for stable framing behavior", () => {
    const shellContractPath = resolve(
      process.cwd(),
      "src/components/workspace-layout/PortfolioWorkspaceShell.test.tsx",
    );

    expect(
      existsSync(shellContractPath),
      "Fail-first baseline: add dedicated shell tests proving persistent framing + active-route behavior across workspace routes.",
    ).toBe(true);
  });

  it("2.2 exposes command palette + symbol lookup entry points from workspace shell", () => {
    const layoutPath = resolve(
      process.cwd(),
      "src/components/workspace-layout/PortfolioWorkspaceLayout.tsx",
    );
    expect(
      existsSync(layoutPath),
      "Fail-first baseline: missing PortfolioWorkspaceLayout route shell module.",
    ).toBe(true);

    const layoutSource = readFileSync(layoutPath, "utf8").toLowerCase();
    expect(
      layoutSource.includes("command palette"),
      "Fail-first baseline: workspace shell must expose one command-palette trigger.",
    ).toBe(true);
    expect(
      layoutSource.includes("symbol lookup") || layoutSource.includes("instrument lookup"),
      "Fail-first baseline: command palette must include one symbol/instrument lookup entry point.",
    ).toBe(true);
  });

  it("2.2 defines command destination registry + compatible context carryover utility", () => {
    const commandRegistryPath = resolve(
      process.cwd(),
      "src/features/portfolio-workspace/command-palette.ts",
    );
    const contextCarryoverPath = resolve(
      process.cwd(),
      "src/features/portfolio-workspace/context-carryover.ts",
    );

    expect(
      existsSync(commandRegistryPath),
      "Fail-first baseline: add command destination registry for route jump/symbol lookup actions.",
    ).toBe(true);
    expect(
      existsSync(contextCarryoverPath),
      "Fail-first baseline: add shared context carryover utility for compatible route transitions.",
    ).toBe(true);
  });

  it("2.3 enforces explicit incompatible-context reset semantics instead of silent submission", () => {
    const contextCarryoverPath = resolve(
      process.cwd(),
      "src/features/portfolio-workspace/context-carryover.ts",
    );
    expect(
      existsSync(contextCarryoverPath),
      "Fail-first baseline: add incompatible-context reset policy module before shell refactors.",
    ).toBe(true);

    if (!existsSync(contextCarryoverPath)) {
      return;
    }

    const contextSource = readFileSync(contextCarryoverPath, "utf8").toLowerCase();
    expect(
      contextSource.includes("incompatible_context_reset") ||
        contextSource.includes("context reset"),
      "Fail-first baseline: context carryover module must define explicit reset reason/copy contract.",
    ).toBe(true);
  });
});

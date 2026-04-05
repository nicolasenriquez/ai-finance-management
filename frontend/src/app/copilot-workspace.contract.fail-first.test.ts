/* @vitest-environment jsdom */

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { appRouter } from "./router";

const COPILOT_ROUTE_PATH = "/portfolio/copilot";
const COPILOT_PAGE_FILE = "src/pages/portfolio-copilot-page/PortfolioCopilotPage.tsx";
const COPILOT_COMPOSER_FILE =
  "src/components/workspace-layout/WorkspaceCopilotLauncher.tsx";
const COPILOT_PRESENTATION_FILE =
  "src/features/portfolio-copilot/presentation.ts";
const COPILOT_PAGE_TEST_FILE = "src/pages/portfolio-copilot-page/PortfolioCopilotPage.test.tsx";

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

describe("portfolio copilot workspace fail-first contract", () => {
  it("registers the canonical copilot workspace route", () => {
    const registeredPaths = getRegisteredRouterPaths();
    expect(
      registeredPaths.has(COPILOT_ROUTE_PATH),
      "Fail-first baseline: add /portfolio/copilot route in app router (task 2.4).",
    ).toBe(true);
  });

  it("includes copilot page and route-state test artifacts", () => {
    const absolutePagePath = resolve(process.cwd(), COPILOT_PAGE_FILE);
    const absoluteTestPath = resolve(process.cwd(), COPILOT_PAGE_TEST_FILE);

    expect(
      existsSync(absolutePagePath),
      `Fail-first baseline: missing Copilot page module at ${COPILOT_PAGE_FILE}.`,
    ).toBe(true);
    expect(
      existsSync(absoluteTestPath),
      `Fail-first baseline: missing Copilot route-state test at ${COPILOT_PAGE_TEST_FILE}.`,
    ).toBe(true);
  });

  it("renders explicit idle/loading/error/blocked/ready states and evidence panels", () => {
    const absolutePagePath = resolve(process.cwd(), COPILOT_PAGE_FILE);
    const absoluteComposerPath = resolve(process.cwd(), COPILOT_COMPOSER_FILE);
    expect(
      existsSync(absolutePagePath),
      `Fail-first baseline: missing Copilot page module at ${COPILOT_PAGE_FILE}.`,
    ).toBe(true);
    expect(
      existsSync(absoluteComposerPath),
      `Fail-first baseline: missing Copilot composer module at ${COPILOT_COMPOSER_FILE}.`,
    ).toBe(true);

    const pageSource = readFileSync(absolutePagePath, "utf8");
    const composerSource = readFileSync(absoluteComposerPath, "utf8");
    const combinedSource = `${pageSource}\n${composerSource}`;
    expect(
      combinedSource.includes("idle"),
      "Fail-first baseline: Copilot page must render explicit idle state.",
    ).toBe(true);
    expect(
      combinedSource.includes("loading"),
      "Fail-first baseline: Copilot page must render explicit loading state.",
    ).toBe(true);
    expect(
      combinedSource.includes("blocked"),
      "Fail-first baseline: Copilot page must render explicit blocked state.",
    ).toBe(true);
    expect(
      combinedSource.includes("error"),
      "Fail-first baseline: Copilot page must render explicit error state.",
    ).toBe(true);
    expect(
      combinedSource.includes("ready"),
      "Fail-first baseline: Copilot page must render explicit ready state.",
    ).toBe(true);
    expect(
      combinedSource.toLowerCase().includes("evidence"),
      "Fail-first baseline: Copilot page must include one evidence rendering surface.",
    ).toBe(true);
    expect(
      combinedSource.toLowerCase().includes("limitation"),
      "Fail-first baseline: Copilot page must include explicit limitation messaging.",
    ).toBe(true);
  });

  it("separates deterministic opportunity candidates from AI narration", () => {
    const absolutePagePath = resolve(process.cwd(), COPILOT_PAGE_FILE);
    expect(
      existsSync(absolutePagePath),
      `Fail-first baseline: missing Copilot page module at ${COPILOT_PAGE_FILE}.`,
    ).toBe(true);

    const pageSource = readFileSync(absolutePagePath, "utf8").toLowerCase();
    expect(
      pageSource.includes("opportunity"),
      "Fail-first baseline: Copilot page must render opportunity scan section.",
    ).toBe(true);
    expect(
      pageSource.includes("candidate"),
      "Fail-first baseline: Copilot page must render deterministic candidate list.",
    ).toBe(true);
    expect(
      pageSource.includes("narration"),
      "Fail-first baseline: Copilot page must render AI narration separately from candidate data.",
    ).toBe(true);
  });

  it("includes stable provider failure reason handling for blocked/error states", () => {
    const absolutePagePath = resolve(process.cwd(), COPILOT_PAGE_FILE);
    const absolutePresentationPath = resolve(
      process.cwd(),
      COPILOT_PRESENTATION_FILE,
    );
    expect(
      existsSync(absolutePagePath),
      `Fail-first baseline: missing Copilot page module at ${COPILOT_PAGE_FILE}.`,
    ).toBe(true);
    expect(
      existsSync(absolutePresentationPath),
      `Fail-first baseline: missing Copilot presentation map at ${COPILOT_PRESENTATION_FILE}.`,
    ).toBe(true);

    const pageSource = readFileSync(absolutePagePath, "utf8");
    const presentationSource = readFileSync(absolutePresentationPath, "utf8");
    const combinedSource = `${pageSource}\n${presentationSource}`;
    expect(
      combinedSource.includes("rate_limited"),
      "Fail-first baseline: Copilot page must map rate_limited reason code.",
    ).toBe(true);
    expect(
      combinedSource.includes("provider_blocked_policy"),
      "Fail-first baseline: Copilot page must map provider_blocked_policy reason code.",
    ).toBe(true);
    expect(
      combinedSource.includes("provider_misconfigured"),
      "Fail-first baseline: Copilot page must map provider_misconfigured reason code.",
    ).toBe(true);
    expect(
      combinedSource.includes("provider_unavailable"),
      "Fail-first baseline: Copilot page must map provider_unavailable reason code.",
    ).toBe(true);
  });
});

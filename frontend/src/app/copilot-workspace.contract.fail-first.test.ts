/* @vitest-environment jsdom */

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { appRouter } from "./router";

const COPILOT_ROUTE_PATH = "/portfolio/copilot";
const COPILOT_PAGE_FILE = "src/pages/portfolio-copilot-page/PortfolioCopilotPage.tsx";
const COPILOT_PAGE_TEST_FILE = "src/pages/portfolio-copilot-page/PortfolioCopilotPage.test.tsx";

function getRegisteredRouterPaths(): Set<string> {
  return new Set(
    appRouter.routes
      .map((route) => route.path)
      .filter((pathValue): pathValue is string => typeof pathValue === "string"),
  );
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
    expect(
      existsSync(absolutePagePath),
      `Fail-first baseline: missing Copilot page module at ${COPILOT_PAGE_FILE}.`,
    ).toBe(true);

    const pageSource = readFileSync(absolutePagePath, "utf8");
    expect(
      pageSource.includes("idle"),
      "Fail-first baseline: Copilot page must render explicit idle state.",
    ).toBe(true);
    expect(
      pageSource.includes("loading"),
      "Fail-first baseline: Copilot page must render explicit loading state.",
    ).toBe(true);
    expect(
      pageSource.includes("blocked"),
      "Fail-first baseline: Copilot page must render explicit blocked state.",
    ).toBe(true);
    expect(
      pageSource.includes("error"),
      "Fail-first baseline: Copilot page must render explicit error state.",
    ).toBe(true);
    expect(
      pageSource.includes("ready"),
      "Fail-first baseline: Copilot page must render explicit ready state.",
    ).toBe(true);
    expect(
      pageSource.toLowerCase().includes("evidence"),
      "Fail-first baseline: Copilot page must include one evidence rendering surface.",
    ).toBe(true);
    expect(
      pageSource.toLowerCase().includes("limitation"),
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
    expect(
      existsSync(absolutePagePath),
      `Fail-first baseline: missing Copilot page module at ${COPILOT_PAGE_FILE}.`,
    ).toBe(true);

    const pageSource = readFileSync(absolutePagePath, "utf8");
    expect(
      pageSource.includes("rate_limited"),
      "Fail-first baseline: Copilot page must map rate_limited reason code.",
    ).toBe(true);
    expect(
      pageSource.includes("provider_blocked_policy"),
      "Fail-first baseline: Copilot page must map provider_blocked_policy reason code.",
    ).toBe(true);
    expect(
      pageSource.includes("provider_misconfigured"),
      "Fail-first baseline: Copilot page must map provider_misconfigured reason code.",
    ).toBe(true);
    expect(
      pageSource.includes("provider_unavailable"),
      "Fail-first baseline: Copilot page must map provider_unavailable reason code.",
    ).toBe(true);
  });
});

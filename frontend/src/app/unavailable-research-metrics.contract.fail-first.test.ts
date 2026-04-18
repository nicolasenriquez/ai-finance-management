/* @vitest-environment jsdom */

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("unsupported research metrics unavailable-state fail-first contract", () => {
  it("1.3 defines an explicit metric availability registry for fundamental and technical contracts", () => {
    const availabilityRegistryPath = resolve(
      process.cwd(),
      "src/features/portfolio-workspace/research-metric-availability.ts",
    );

    expect(
      existsSync(availabilityRegistryPath),
      "Fail-first baseline: missing research metric availability registry.",
    ).toBe(true);

    if (!existsSync(availabilityRegistryPath)) {
      return;
    }

    const availabilitySource = readFileSync(availabilityRegistryPath, "utf8");
    const requiredUnsupportedMetricIds = [
      "pe_ratio",
      "rule_of_40",
      "j5",
      "jr4",
      "volume_profile",
      "iv_percentile",
    ];

    for (const metricId of requiredUnsupportedMetricIds) {
      expect(
        availabilitySource.includes(`"${metricId}"`),
        `Fail-first baseline: missing ${metricId} availability entry.`,
      ).toBe(true);
    }

    expect(
      availabilitySource.includes('availability: "unavailable"'),
      "Fail-first baseline: unsupported metrics must resolve explicitly to `unavailable`.",
    ).toBe(true);
  });

  it("1.3 includes unavailable reason-code copy for missing fundamental and technical contracts", () => {
    const lifecycleCopyPath = resolve(
      process.cwd(),
      "src/features/portfolio-workspace/state-copy.ts",
    );

    expect(
      existsSync(lifecycleCopyPath),
      "Fail-first baseline: missing lifecycle copy source.",
    ).toBe(true);

    const lifecycleCopySource = readFileSync(lifecycleCopyPath, "utf8");
    expect(
      lifecycleCopySource.includes("fundamental_contract_missing"),
      "Fail-first baseline: add unavailable reason-code copy for missing fundamental contracts.",
    ).toBe(true);
    expect(
      lifecycleCopySource.includes("technical_contract_missing"),
      "Fail-first baseline: add unavailable reason-code copy for missing technical contracts.",
    ).toBe(true);
  });

  it("1.3 renders /portfolio/signals unavailable cards without placeholder numbers when contracts are missing", () => {
    const routerSourcePath = resolve(process.cwd(), "src/app/router.tsx");
    const signalsPagePath = resolve(
      process.cwd(),
      "src/pages/portfolio-signals-page/PortfolioSignalsPage.tsx",
    );
    const signalsContainerPath = resolve(
      process.cwd(),
      "src/pages/portfolio-signals-page/components/PortfolioSignalsRouteContainer.tsx",
    );
    const signalsViewPath = resolve(
      process.cwd(),
      "src/pages/portfolio-signals-page/components/PortfolioSignalsRouteView.tsx",
    );
    const signalsHookPath = resolve(
      process.cwd(),
      "src/pages/portfolio-signals-page/hooks/usePortfolioSignalsRouteState.ts",
    );
    const signalsPageTestPath = resolve(
      process.cwd(),
      "src/pages/portfolio-signals-page/PortfolioSignalsPage.test.tsx",
    );

    expect(existsSync(routerSourcePath)).toBe(true);
    expect(
      existsSync(signalsPagePath),
      "Fail-first baseline: missing /portfolio/signals page module.",
    ).toBe(true);
    expect(
      existsSync(signalsPageTestPath),
      "Fail-first baseline: missing /portfolio/signals page contract tests.",
    ).toBe(true);
    expect(existsSync(signalsContainerPath)).toBe(true);
    expect(existsSync(signalsViewPath)).toBe(true);
    expect(existsSync(signalsHookPath)).toBe(true);

    const routerSource = readFileSync(routerSourcePath, "utf8");
    expect(
      routerSource.includes('path: "signals"'),
      "Fail-first baseline: router must expose `/portfolio/signals` route.",
    ).toBe(true);

    if (!existsSync(signalsPagePath)) {
      return;
    }

    const signalsPageSource = [
      readFileSync(signalsPagePath, "utf8"),
      existsSync(signalsContainerPath)
        ? readFileSync(signalsContainerPath, "utf8")
        : "",
      existsSync(signalsViewPath)
        ? readFileSync(signalsViewPath, "utf8")
        : "",
      existsSync(signalsHookPath)
        ? readFileSync(signalsHookPath, "utf8")
        : "",
    ].join("\n");
    const hasUnavailableStateBannerContract =
      signalsPageSource.includes('state="unavailable"') ||
      signalsPageSource.includes('"loading" : "unavailable"');
    expect(
      hasUnavailableStateBannerContract,
      "Fail-first baseline: unsupported research metrics must render unavailable state banners.",
    ).toBe(true);
    expect(
      signalsPageSource.includes("research data pending"),
      "Fail-first baseline: unavailable modules must explain missing research contracts.",
    ).toBe(true);
    expect(
      signalsPageSource.includes("signal contract not connected"),
      "Fail-first baseline: unavailable modules must expose explicit non-connected contract copy.",
    ).toBe(true);
  });
});

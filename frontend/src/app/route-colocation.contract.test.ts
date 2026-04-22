import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  describe,
  expect,
  it,
} from "vitest";

describe("route colocation contract", () => {
  it("4.12 keeps non-trivial routes in colocated container/presentation directories", () => {
    const signalsRoutePath = resolve(
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

    const assetRoutePath = resolve(
      process.cwd(),
      "src/pages/portfolio-asset-detail-page/PortfolioAssetDetailPage.tsx",
    );
    const assetContainerPath = resolve(
      process.cwd(),
      "src/pages/portfolio-asset-detail-page/components/PortfolioAssetDetailRouteContainer.tsx",
    );
    const assetViewPath = resolve(
      process.cwd(),
      "src/pages/portfolio-asset-detail-page/components/PortfolioAssetDetailRouteView.tsx",
    );
    const assetHookPath = resolve(
      process.cwd(),
      "src/pages/portfolio-asset-detail-page/hooks/usePortfolioAssetDetailRouteState.ts",
    );

    expect(existsSync(signalsRoutePath)).toBe(true);
    expect(existsSync(signalsContainerPath)).toBe(true);
    expect(existsSync(signalsViewPath)).toBe(true);
    expect(existsSync(signalsHookPath)).toBe(true);

    expect(existsSync(assetRoutePath)).toBe(true);
    expect(existsSync(assetContainerPath)).toBe(true);
    expect(existsSync(assetViewPath)).toBe(true);
    expect(existsSync(assetHookPath)).toBe(true);

    const signalsRouteSource = readFileSync(signalsRoutePath, "utf8");
    const assetRouteSource = readFileSync(assetRoutePath, "utf8");

    expect(signalsRouteSource.includes("PortfolioSignalsRouteContainer")).toBe(true);
    expect(assetRouteSource.includes("PortfolioAssetDetailRouteContainer")).toBe(true);
  });
});

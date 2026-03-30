/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  cleanup,
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type { PortfolioHierarchyGroupRow } from "../../core/api/schemas";
import { PortfolioHierarchyTable } from "./PortfolioHierarchyTable";

const groups: PortfolioHierarchyGroupRow[] = [
  {
    group_key: "Technology",
    group_label: "Technology",
    asset_count: 1,
    total_market_value_usd: "120.00",
    total_profit_loss_usd: "20.00",
    total_change_pct: "20.00",
    assets: [
      {
        instrument_symbol: "AAPL",
        sector_label: "Technology",
        open_quantity: "1.000000000",
        open_cost_basis_usd: "100.00",
        avg_price_usd: "100.00",
        current_price_usd: "120.00",
        market_value_usd: "120.00",
        profit_loss_usd: "20.00",
        change_pct: "20.00",
        lot_count: 1,
        lots: [
          {
            lot_id: 1,
            opened_on: "2026-03-20",
            original_qty: "1.000000000",
            remaining_qty: "1.000000000",
            unit_cost_basis_usd: "100.00",
            total_cost_basis_usd: "100.00",
            market_value_usd: "120.00",
            profit_loss_usd: "20.00",
          },
        ],
      },
    ],
  },
];

describe("PortfolioHierarchyTable", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders deterministic and accessible toolbar control labels (fail-first)", () => {
    render(
      <PortfolioHierarchyTable
        groups={groups}
        groupBy="sector"
        onGroupByChange={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Expand all sector groups" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Collapse all sector groups" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Expand all stock rows" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Collapse all stock rows" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Switch to stock pivot view" }),
    ).toBeInTheDocument();
  });

  it("supports deterministic group and asset toggling by explicit control labels (fail-first)", async () => {
    const user = userEvent.setup();

    render(
      <PortfolioHierarchyTable
        groups={groups}
        groupBy="sector"
        onGroupByChange={vi.fn()}
      />,
    );

    expect(screen.queryByText("AAPL")).toBeNull();

    await user.click(
      screen.getByRole("button", { name: "Toggle group Technology" }),
    );
    expect(screen.getByText("AAPL")).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Toggle asset AAPL lots" }),
    );
    expect(
      screen.getByRole("heading", { name: "Individual Entries (Tax Lots)" }),
    ).toBeInTheDocument();
  });

  it("renders sortable hierarchy headers with explicit sort controls (fail-first)", () => {
    render(
      <PortfolioHierarchyTable
        groups={groups}
        groupBy="sector"
        onGroupByChange={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Sort hierarchy by asset or group" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Sort hierarchy by current value" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Sort hierarchy by profit or loss" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Sort hierarchy by change percent" }),
    ).toBeInTheDocument();
  });
});

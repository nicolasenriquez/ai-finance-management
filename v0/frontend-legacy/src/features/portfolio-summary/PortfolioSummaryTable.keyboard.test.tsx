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
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type { PortfolioSummaryRow } from "../../core/api/schemas";
import { PortfolioSummaryTable } from "./PortfolioSummaryTable";

const navigateMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>(
    "react-router-dom",
  );
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

const summaryRows: PortfolioSummaryRow[] = [
  {
    instrument_symbol: "AAPL",
    open_quantity: "2.000000000",
    open_cost_basis_usd: "1000.00",
    open_lot_count: 2,
    realized_proceeds_usd: "400.00",
    realized_cost_basis_usd: "320.00",
    realized_gain_usd: "80.00",
    dividend_gross_usd: "18.00",
    dividend_taxes_usd: "3.00",
    dividend_net_usd: "15.00",
    latest_close_price_usd: "530.00",
    market_value_usd: "1060.00",
    unrealized_gain_usd: "60.00",
    unrealized_gain_pct: "6.00",
  },
];

describe("PortfolioSummaryTable keyboard navigation", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    navigateMock.mockReset();
  });

  it("keeps interactive rows focusable and opens detail on Enter", async () => {
    const user = userEvent.setup();
    render(<PortfolioSummaryTable rows={summaryRows} />);

    const row = screen.getByRole("link", {
      name: "Open lot detail for AAPL",
    });

    row.focus();
    expect(row).toHaveFocus();
    expect(row).toHaveAttribute("tabindex", "0");
    expect(row).toHaveAttribute("aria-keyshortcuts", "Enter Space");

    await user.keyboard("{Enter}");

    expect(navigateMock).toHaveBeenCalledWith("/portfolio/AAPL");
  });

  it("opens detail on Space key for keyboard-only navigation", async () => {
    const user = userEvent.setup();
    render(<PortfolioSummaryTable rows={summaryRows} />);

    const row = screen.getByRole("link", {
      name: "Open lot detail for AAPL",
    });
    row.focus();

    await user.keyboard(" ");

    expect(navigateMock).toHaveBeenCalledWith("/portfolio/AAPL");
  });
});

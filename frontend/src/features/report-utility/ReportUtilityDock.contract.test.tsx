/* @vitest-environment jsdom */

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
} from "vitest";

import { ReportUtilityDock } from "./ReportUtilityDock";

afterEach(() => {
  cleanup();
});

describe("ReportUtilityDock contract", () => {
  it("4.10 keeps compact report controls for scope and date range", () => {
    render(<ReportUtilityDock />);

    expect(screen.getByRole("heading", { level: 3, name: "Quant report utility" })).not.toBeNull();
    expect(screen.getByLabelText("Scope")).not.toBeNull();
    expect(screen.getByLabelText("Start date")).not.toBeNull();
    expect(screen.getByLabelText("End date")).not.toBeNull();
    expect(screen.getByRole("button", { name: "Generate HTML report" })).not.toBeNull();
    expect(screen.getByRole("button", { name: "Export analyst pack (.md)" })).not.toBeNull();
  });

  it("4.10 preserves explicit lifecycle transitions and validation failures", async () => {
    const user = userEvent.setup();
    render(<ReportUtilityDock />);

    const exportButton = screen.getByRole("button", { name: "Export analyst pack (.md)" });
    await user.click(exportButton);
    expect(screen.getByText("Lifecycle: unavailable")).not.toBeNull();

    const scopeSelect = screen.getByLabelText("Scope");
    await user.selectOptions(scopeSelect, "symbol");

    const symbolInput = screen.getByLabelText("Symbol (optional)");
    await user.clear(symbolInput);

    await user.click(screen.getByRole("button", { name: "Generate HTML report" }));
    expect(screen.getByText("Lifecycle: error")).not.toBeNull();
    expect(screen.getByText(/symbol is required/i)).not.toBeNull();

    await user.type(symbolInput, "msft");
    const startDateInput = screen.getByLabelText("Start date");
    const endDateInput = screen.getByLabelText("End date");
    await user.clear(startDateInput);
    await user.type(startDateInput, "2026-04-18");
    await user.clear(endDateInput);
    await user.type(endDateInput, "2026-04-01");
    await user.click(screen.getByRole("button", { name: "Generate HTML report" }));

    expect(screen.getByText("Lifecycle: error")).not.toBeNull();
    expect(screen.getByText(/start date cannot be after end date/i)).not.toBeNull();

    await user.clear(startDateInput);
    await user.type(startDateInput, "2026-04-01");
    await user.click(screen.getByRole("button", { name: "Generate HTML report" }));

    expect(screen.getByText("Lifecycle: generated")).not.toBeNull();
    await user.click(exportButton);
    expect(screen.getByText("Lifecycle: preview ready")).not.toBeNull();
  });
});

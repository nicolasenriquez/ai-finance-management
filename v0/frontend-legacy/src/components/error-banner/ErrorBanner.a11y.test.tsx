/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
} from "vitest";

import { ErrorBanner } from "./ErrorBanner";

describe("ErrorBanner accessibility semantics", () => {
  it("uses alert semantics for error variant", () => {
    render(<ErrorBanner message="Server failed" title="Summary unavailable" />);

    const banner = screen.getByRole("alert", { name: "Summary unavailable" });
    expect(banner).toHaveAttribute("aria-live", "assertive");
  });

  it("uses status semantics for warning variant", () => {
    render(
      <ErrorBanner
        message="Instrument not found"
        title="Instrument not found"
        variant="warning"
      />,
    );

    const banner = screen.getByRole("status", { name: "Instrument not found" });
    expect(banner).toHaveAttribute("aria-live", "polite");
  });
});

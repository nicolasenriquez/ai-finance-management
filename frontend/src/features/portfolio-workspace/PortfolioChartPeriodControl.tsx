import type { ChangeEvent } from "react";

import type { PortfolioChartPeriod } from "../../core/api/schemas";
import { PORTFOLIO_CHART_PERIOD_OPTIONS } from "./period";

type PortfolioChartPeriodControlProps = {
  value: PortfolioChartPeriod;
  onChange: (nextPeriod: PortfolioChartPeriod) => void;
};

export function PortfolioChartPeriodControl({
  value,
  onChange,
}: PortfolioChartPeriodControlProps) {
  function handleChange(event: ChangeEvent<HTMLSelectElement>): void {
    onChange(event.currentTarget.value as PortfolioChartPeriod);
  }

  return (
    <label className="period-control">
      <span className="period-control__label">Period</span>
      <select
        aria-label="Select analytics period"
        className="period-control__select"
        value={value}
        onChange={handleChange}
      >
        {PORTFOLIO_CHART_PERIOD_OPTIONS.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

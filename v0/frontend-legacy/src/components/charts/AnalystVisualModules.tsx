import type {
  PortfolioContributionRow,
  PortfolioSummaryRow,
  PortfolioTimeSeriesPoint,
} from "../../core/api/schemas";
import { formatUsdMoney } from "../../core/lib/formatters";

type WaterfallStep = {
  label: string;
  value: number;
  kind: "total" | "delta";
  description?: string;
};

type ContributionWaterfallStep = {
  label: string;
  contribution: number;
  cumulative: number;
};

type MonthlyReturnCell = {
  monthKey: string;
  monthLabel: string;
  returnPct: number;
};

function toNumber(value: string | null): number {
  if (value === null) {
    return 0;
  }
  return Number(value);
}

function toSignedMoneyLabel(value: number): string {
  const formatted = formatUsdMoney(value.toFixed(2));
  return value > 0 ? `+${formatted}` : formatted;
}

function toPercentLabel(value: number): string {
  const signPrefix = value > 0 ? "+" : "";
  return `${signPrefix}${value.toFixed(2)}%`;
}

function resolveToneClass(value: number): "positive" | "negative" | "neutral" {
  if (value > 0) {
    return "positive";
  }
  if (value < 0) {
    return "negative";
  }
  return "neutral";
}

function resolveWaterfallSteps(
  summaryRows: PortfolioSummaryRow[],
  points: PortfolioTimeSeriesPoint[],
): WaterfallStep[] {
  const startValue = points.length > 0 ? Number(points[0].portfolio_value_usd) : 0;
  const endValue = points.length > 0 ? Number(points[points.length - 1].portfolio_value_usd) : 0;
  const realizedGain = summaryRows.reduce(
    (accumulator, row) => accumulator + Number(row.realized_gain_usd),
    0,
  );
  const dividendNet = summaryRows.reduce(
    (accumulator, row) => accumulator + Number(row.dividend_net_usd),
    0,
  );
  const unrealizedGain = summaryRows.reduce(
    (accumulator, row) => accumulator + toNumber(row.unrealized_gain_usd),
    0,
  );
  const explainedEnd = startValue + realizedGain + dividendNet + unrealizedGain;
  const reconciliation = endValue - explainedEnd;

  return [
    { label: "Start value", value: startValue, kind: "total" },
    {
      label: "Realized gain",
      value: realizedGain,
      kind: "delta",
      description: "Closed-position P&L realized in period.",
    },
    {
      label: "Dividend net",
      value: dividendNet,
      kind: "delta",
      description: "Dividends after withholding/tax effects.",
    },
    {
      label: "Unrealized gain",
      value: unrealizedGain,
      kind: "delta",
      description: "Open-position mark-to-market movement.",
    },
    {
      label: "Residual adjustment",
      value: reconciliation,
      kind: "delta",
      description: "End minus explained components (timing/rounding/coverage residual).",
    },
    { label: "End value", value: endValue, kind: "total" },
  ];
}

function resolveContributionWaterfallSteps(
  rows: PortfolioContributionRow[],
): ContributionWaterfallStep[] {
  const topRows = [...rows]
    .sort(
      (left, right) =>
        Math.abs(Number(right.contribution_pnl_usd)) -
        Math.abs(Number(left.contribution_pnl_usd)),
    )
    .slice(0, 6);

  let cumulative = 0;
  return topRows.map((row) => {
    const contribution = Number(row.contribution_pnl_usd);
    cumulative += contribution;
    return {
      label: row.instrument_symbol,
      contribution,
      cumulative,
    };
  });
}

function buildMonthlyReturnCells(points: PortfolioTimeSeriesPoint[]): MonthlyReturnCell[] {
  if (points.length < 2) {
    return [];
  }

  const sortedPoints = [...points].sort((left, right) =>
    left.captured_at.localeCompare(right.captured_at),
  );
  const growthByMonth = new Map<string, number>();

  for (let index = 1; index < sortedPoints.length; index += 1) {
    const previousValue = Number(sortedPoints[index - 1].portfolio_value_usd);
    const currentValue = Number(sortedPoints[index].portfolio_value_usd);
    if (previousValue <= 0) {
      continue;
    }
    const dayReturn = (currentValue - previousValue) / previousValue;
    const monthKey = sortedPoints[index].captured_at.slice(0, 7);
    const runningGrowth = growthByMonth.get(monthKey) ?? 1;
    growthByMonth.set(monthKey, runningGrowth * (1 + dayReturn));
  }

  const monthFormatter = new Intl.DateTimeFormat("en-US", {
    month: "short",
    year: "2-digit",
    timeZone: "UTC",
  });

  return [...growthByMonth.entries()]
    .sort(([leftMonth], [rightMonth]) => leftMonth.localeCompare(rightMonth))
    .slice(-12)
    .map(([monthKey, growth]) => {
      const monthDate = new Date(`${monthKey}-01T00:00:00Z`);
      return {
        monthKey,
        monthLabel: monthFormatter.format(monthDate),
        returnPct: (growth - 1) * 100,
      };
    });
}

export function PortfolioPeriodChangeWaterfall({
  summaryRows,
  points,
}: {
  summaryRows: PortfolioSummaryRow[];
  points: PortfolioTimeSeriesPoint[];
}) {
  const steps = resolveWaterfallSteps(summaryRows, points);
  const maxDelta = Math.max(
    1,
    ...steps
      .filter((step) => step.kind === "delta")
      .map((step) => Math.abs(step.value)),
  );
  const maxTotal = Math.max(
    1,
    ...steps
      .filter((step) => step.kind === "total")
      .map((step) => Math.abs(step.value)),
  );

  return (
    <div>
      <ol className="waterfall-module" aria-label="Period change waterfall">
        {steps.map((step) => {
          const widthRatio =
            step.kind === "delta"
              ? Math.abs(step.value) / maxDelta
              : Math.abs(step.value) / maxTotal;
          return (
            <li className="waterfall-module__row" key={step.label}>
              <div className="waterfall-module__label-shell">
                <span className="waterfall-module__label">{step.label}</span>
                {step.description ? (
                  <span className="waterfall-module__description">{step.description}</span>
                ) : null}
              </div>
              <div className="waterfall-module__bar-shell">
                <span
                  className={`waterfall-module__bar waterfall-module__bar--${resolveToneClass(step.value)} waterfall-module__bar--${step.kind}`}
                  style={{ width: `${Math.max(8, Math.round(widthRatio * 100))}%` }}
                />
              </div>
              <strong className={`waterfall-module__value tone-${resolveToneClass(step.value)}`}>
                {step.kind === "delta" ? toSignedMoneyLabel(step.value) : formatUsdMoney(step.value.toFixed(2))}
              </strong>
            </li>
          );
        })}
      </ol>
      <p className="waterfall-module__formula">
        Residual adjustment = End value - (Start value + Realized gain + Dividend net + Unrealized gain)
      </p>
    </div>
  );
}

export function PortfolioContributionWaterfall({ rows }: { rows: PortfolioContributionRow[] }) {
  const steps = resolveContributionWaterfallSteps(rows);
  const maxContribution = Math.max(
    1,
    ...steps.map((step) => Math.abs(step.contribution)),
  );

  return (
    <ol className="waterfall-module" aria-label="Contribution waterfall">
      {steps.map((step) => {
        const widthRatio = Math.abs(step.contribution) / maxContribution;
        return (
          <li className="waterfall-module__row" key={step.label}>
            <span className="waterfall-module__label">{step.label}</span>
            <div className="waterfall-module__bar-shell">
              <span
                className={`waterfall-module__bar waterfall-module__bar--${resolveToneClass(step.contribution)} waterfall-module__bar--delta`}
                style={{ width: `${Math.max(8, Math.round(widthRatio * 100))}%` }}
              />
            </div>
            <div className="waterfall-module__values">
              <strong className={`tone-${resolveToneClass(step.contribution)}`}>
                {toSignedMoneyLabel(step.contribution)}
              </strong>
              <span className="waterfall-module__cumulative">
                cumulative {toSignedMoneyLabel(step.cumulative)}
              </span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

export function PortfolioMonthlyReturnsHeatmap({ points }: { points: PortfolioTimeSeriesPoint[] }) {
  const monthlyCells = buildMonthlyReturnCells(points);

  if (monthlyCells.length === 0) {
    return (
      <p className="heatmap-module__fallback">
        Monthly heatmap is unavailable for the selected scope due to insufficient points.
      </p>
    );
  }

  return (
    <div>
      <div className="heatmap-module" role="img" aria-label="Monthly returns heatmap">
        {monthlyCells.map((cell) => (
          <article
            className={`heatmap-module__cell heatmap-module__cell--${resolveToneClass(cell.returnPct)}`}
            key={cell.monthKey}
          >
            <span className="heatmap-module__month">{cell.monthLabel}</span>
            <strong className="heatmap-module__value">{toPercentLabel(cell.returnPct)}</strong>
          </article>
        ))}
      </div>
      <p className="heatmap-module__caveat">
        Calendar-heatmap style estimate based on available period points; values are indicative and
        not tax-adjusted.
      </p>
    </div>
  );
}

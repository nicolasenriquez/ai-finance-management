import type { PortfolioRiskEstimatorMetric } from "../../core/api/schemas";

type PortfolioRiskChartProps = {
  metrics: PortfolioRiskEstimatorMetric[];
};

type RiskTone = "positive" | "neutral" | "negative";

type RiskMetricDescriptor = {
  label: string;
  domain: [number, number];
  target: number | null;
  lowRiskThreshold: number;
  mediumRiskThreshold: number;
  scaleLabels: [string, string, string];
  formatDisplayValue: (rawValue: number) => string;
  normalizeForTrack: (rawValue: number) => number;
  resolveTone: (rawValue: number, normalizedValue: number) => RiskTone;
};

type RiskChartRow = {
  key: string;
  label: string;
  valueLabel: string;
  tone: RiskTone;
  markerPositionPct: number;
  targetPositionPct: number | null;
  lowWidthPct: number;
  mediumWidthPct: number;
  highWidthPct: number;
  scaleLabels: [string, string, string];
};

function humanizeEstimatorId(estimatorId: string): string {
  return estimatorId
    .split("_")
    .map((chunk) =>
      chunk.length > 0 ? `${chunk[0].toUpperCase()}${chunk.slice(1).toLowerCase()}` : chunk,
    )
    .join(" ");
}

function toSignedPercentLabel(value: number): string {
  const percentValue = value * 100;
  const signPrefix = percentValue > 0 ? "+" : "";
  return `${signPrefix}${percentValue.toFixed(2)}%`;
}

function toNumberLabel(value: number): string {
  return value.toFixed(3);
}

function clamp(value: number, min: number, max: number): number {
  if (value < min) {
    return min;
  }
  if (value > max) {
    return max;
  }
  return value;
}

function toPercentWithinDomain(
  value: number,
  domain: [number, number],
): number {
  const [domainMin, domainMax] = domain;
  const clampedValue = clamp(value, domainMin, domainMax);
  return ((clampedValue - domainMin) / (domainMax - domainMin)) * 100;
}

function resolveDescriptor(estimatorId: string): RiskMetricDescriptor {
  const normalizedEstimatorId = estimatorId.toLowerCase();

  if (normalizedEstimatorId === "beta") {
    return {
      label: "Beta",
      domain: [0, 2],
      target: 1,
      lowRiskThreshold: 0.8,
      mediumRiskThreshold: 1.2,
      scaleLabels: ["0.0", "1.0 target", "2.0"],
      formatDisplayValue: toNumberLabel,
      normalizeForTrack: (rawValue) => rawValue,
      resolveTone: (rawValue) => {
        const distanceFromTarget = Math.abs(rawValue - 1);
        if (distanceFromTarget <= 0.2) {
          return "positive";
        }
        if (distanceFromTarget <= 0.4) {
          return "neutral";
        }
        return "negative";
      },
    };
  }

  if (normalizedEstimatorId.includes("volatility")) {
    return {
      label: humanizeEstimatorId(estimatorId),
      domain: [0, 0.6],
      target: null,
      lowRiskThreshold: 0.15,
      mediumRiskThreshold: 0.25,
      scaleLabels: ["0%", "15% low risk", "60%"],
      formatDisplayValue: toSignedPercentLabel,
      normalizeForTrack: (rawValue) => rawValue,
      resolveTone: (_rawValue, normalizedValue) => {
        if (normalizedValue <= 0.15) {
          return "positive";
        }
        if (normalizedValue <= 0.25) {
          return "neutral";
        }
        return "negative";
      },
    };
  }

  if (normalizedEstimatorId.includes("downside_deviation")) {
    return {
      label: "Downside Deviation (Annualized)",
      domain: [0, 0.6],
      target: null,
      lowRiskThreshold: 0.1,
      mediumRiskThreshold: 0.2,
      scaleLabels: ["0%", "10% mild", "60% severe"],
      formatDisplayValue: toSignedPercentLabel,
      normalizeForTrack: (rawValue) => rawValue,
      resolveTone: (_rawValue, normalizedValue) => {
        if (normalizedValue <= 0.1) {
          return "positive";
        }
        if (normalizedValue <= 0.2) {
          return "neutral";
        }
        return "negative";
      },
    };
  }

  if (normalizedEstimatorId.includes("drawdown")) {
    return {
      label: "Max Drawdown",
      domain: [0, 0.6],
      target: null,
      lowRiskThreshold: 0.1,
      mediumRiskThreshold: 0.2,
      scaleLabels: ["0%", "10% mild", "60% severe"],
      formatDisplayValue: toSignedPercentLabel,
      normalizeForTrack: (rawValue) => Math.abs(rawValue),
      resolveTone: (_rawValue, normalizedValue) => {
        if (normalizedValue <= 0.1) {
          return "positive";
        }
        if (normalizedValue <= 0.2) {
          return "neutral";
        }
        return "negative";
      },
    };
  }

  if (normalizedEstimatorId.includes("value_at_risk_95")) {
    return {
      label: "VaR (95%)",
      domain: [0, 0.2],
      target: null,
      lowRiskThreshold: 0.02,
      mediumRiskThreshold: 0.05,
      scaleLabels: ["0%", "2% low", "20% severe"],
      formatDisplayValue: toSignedPercentLabel,
      normalizeForTrack: (rawValue) => Math.abs(rawValue),
      resolveTone: (_rawValue, normalizedValue) => {
        if (normalizedValue <= 0.02) {
          return "positive";
        }
        if (normalizedValue <= 0.05) {
          return "neutral";
        }
        return "negative";
      },
    };
  }

  if (normalizedEstimatorId.includes("expected_shortfall_95")) {
    return {
      label: "Expected Shortfall (95%)",
      domain: [0, 0.25],
      target: null,
      lowRiskThreshold: 0.03,
      mediumRiskThreshold: 0.06,
      scaleLabels: ["0%", "3% low", "25% severe"],
      formatDisplayValue: toSignedPercentLabel,
      normalizeForTrack: (rawValue) => Math.abs(rawValue),
      resolveTone: (_rawValue, normalizedValue) => {
        if (normalizedValue <= 0.03) {
          return "positive";
        }
        if (normalizedValue <= 0.06) {
          return "neutral";
        }
        return "negative";
      },
    };
  }

  return {
    label: humanizeEstimatorId(estimatorId),
    domain: [0, 1],
    target: null,
    lowRiskThreshold: 0.33,
    mediumRiskThreshold: 0.66,
    scaleLabels: ["Low", "Mid", "High"],
    formatDisplayValue: toNumberLabel,
    normalizeForTrack: (rawValue) => rawValue,
    resolveTone: (_rawValue, normalizedValue) => {
      if (normalizedValue <= 0.33) {
        return "positive";
      }
      if (normalizedValue <= 0.66) {
        return "neutral";
      }
      return "negative";
    },
  };
}

function buildRiskChartRows(
  metrics: PortfolioRiskEstimatorMetric[],
): RiskChartRow[] {
  return metrics.map((metric) => {
    const rawValue = Number(metric.value);
    const descriptor = resolveDescriptor(metric.estimator_id);
    const normalizedValue = descriptor.normalizeForTrack(rawValue);
    const markerPositionPct = toPercentWithinDomain(normalizedValue, descriptor.domain);
    const lowWidthPct = toPercentWithinDomain(descriptor.lowRiskThreshold, descriptor.domain);
    const mediumWidthUpperPct = toPercentWithinDomain(
      descriptor.mediumRiskThreshold,
      descriptor.domain,
    );
    const mediumWidthPct = Math.max(0, mediumWidthUpperPct - lowWidthPct);
    const highWidthPct = Math.max(0, 100 - mediumWidthUpperPct);
    const targetPositionPct =
      descriptor.target === null
        ? null
        : toPercentWithinDomain(descriptor.target, descriptor.domain);

    return {
      key: metric.estimator_id,
      label: descriptor.label,
      valueLabel: descriptor.formatDisplayValue(rawValue),
      tone: descriptor.resolveTone(rawValue, normalizedValue),
      markerPositionPct,
      targetPositionPct,
      lowWidthPct,
      mediumWidthPct,
      highWidthPct,
      scaleLabels: descriptor.scaleLabels,
    };
  });
}

export function PortfolioRiskChart({ metrics }: PortfolioRiskChartProps) {
  const chartRows = buildRiskChartRows(metrics);

  return (
    <div className="chart-surface risk-range-chart" role="img" aria-label="Risk metrics chart">
      <ul className="risk-range-chart__rows">
        {chartRows.map((row) => (
          <li className="risk-range-chart__row" key={row.key}>
            <div className="risk-range-chart__header">
              <span className="risk-range-chart__label">{row.label}</span>
              <strong className={`risk-range-chart__value tone-${row.tone}`}>
                {row.valueLabel}
              </strong>
            </div>

            <div className="risk-range-chart__track" aria-hidden="true">
              <span
                className="risk-range-chart__zone risk-range-chart__zone--low"
                style={{ width: `${row.lowWidthPct}%` }}
              />
              <span
                className="risk-range-chart__zone risk-range-chart__zone--medium"
                style={{ width: `${row.mediumWidthPct}%` }}
              />
              <span
                className="risk-range-chart__zone risk-range-chart__zone--high"
                style={{ width: `${row.highWidthPct}%` }}
              />
              {row.targetPositionPct !== null ? (
                <span
                  className="risk-range-chart__target"
                  style={{ left: `${row.targetPositionPct}%` }}
                />
              ) : null}
              <span
                className="risk-range-chart__marker"
                style={{ left: `${row.markerPositionPct}%` }}
              />
            </div>

            <div className="risk-range-chart__scale">
              <span>{row.scaleLabels[0]}</span>
              <span>{row.scaleLabels[1]}</span>
              <span>{row.scaleLabels[2]}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

import { useState } from "react";
import {
  useInRouterContext,
  useSearchParams,
} from "react-router-dom";

type ReportLifecycleState =
  | "requested"
  | "generated"
  | "preview_ready"
  | "error"
  | "unavailable";

type ReportScope = "portfolio" | "symbol";

const DEFAULT_START_DATE = "2026-01-01";
const DEFAULT_END_DATE = "2026-04-17";
const DEFAULT_SYMBOL = "";

type ReportControls = {
  scope: ReportScope;
  symbol: string;
  startDate: string;
  endDate: string;
};

type ReportControlsBindings = {
  controls: ReportControls;
  setScope: (scope: ReportScope) => void;
  setSymbol: (symbol: string) => void;
  setStartDate: (startDate: string) => void;
  setEndDate: (endDate: string) => void;
  stateSourceLabel: "URL state" | "Local state";
};

function formatLifecycleState(state: ReportLifecycleState): string {
  return state.replaceAll("_", " ");
}

function resolveScope(rawScope: string | null): ReportScope {
  if (rawScope === "symbol") {
    return "symbol";
  }
  return "portfolio";
}

function normalizeSymbol(rawSymbol: string): string {
  return rawSymbol.toUpperCase().replaceAll(" ", "");
}

function resolveDate(rawDate: string | null, fallbackDate: string): string {
  if (rawDate === null) {
    return fallbackDate;
  }
  return rawDate;
}

function resolveUrlControls(searchParams: URLSearchParams): ReportControls {
  return {
    scope: resolveScope(searchParams.get("scope")),
    symbol: normalizeSymbol(searchParams.get("symbol") ?? DEFAULT_SYMBOL),
    startDate: resolveDate(searchParams.get("start"), DEFAULT_START_DATE),
    endDate: resolveDate(searchParams.get("end"), DEFAULT_END_DATE),
  };
}

function useLocalReportControlsBindings(): ReportControlsBindings {
  const [scope, setScope] = useState<ReportScope>("portfolio");
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [startDate, setStartDate] = useState(DEFAULT_START_DATE);
  const [endDate, setEndDate] = useState(DEFAULT_END_DATE);

  return {
    controls: {
      scope,
      symbol,
      startDate,
      endDate,
    },
    setScope,
    setSymbol,
    setStartDate,
    setEndDate,
    stateSourceLabel: "Local state",
  };
}

function useUrlReportControlsBindings(): ReportControlsBindings {
  const [searchParams, setSearchParams] = useSearchParams();
  const controls = resolveUrlControls(searchParams);

  function setUrlControls(nextControls: ReportControls): void {
    const nextSearchParams = new URLSearchParams(searchParams);
    nextSearchParams.set("scope", nextControls.scope);
    if (nextControls.symbol.trim().length === 0) {
      nextSearchParams.delete("symbol");
    } else {
      nextSearchParams.set("symbol", normalizeSymbol(nextControls.symbol));
    }
    nextSearchParams.set("start", nextControls.startDate);
    nextSearchParams.set("end", nextControls.endDate);
    setSearchParams(nextSearchParams, { replace: true });
  }

  return {
    controls,
    setScope: (scope: ReportScope) => {
      setUrlControls({
        ...controls,
        scope,
      });
    },
    setSymbol: (symbol: string) => {
      setUrlControls({
        ...controls,
        symbol: normalizeSymbol(symbol),
      });
    },
    setStartDate: (startDate: string) => {
      setUrlControls({
        ...controls,
        startDate,
      });
    },
    setEndDate: (endDate: string) => {
      setUrlControls({
        ...controls,
        endDate,
      });
    },
    stateSourceLabel: "URL state",
  };
}

function ReportUtilityDockSurface({
  controls,
  setScope,
  setSymbol,
  setStartDate,
  setEndDate,
  stateSourceLabel,
}: ReportControlsBindings) {
  const [lifecycleState, setLifecycleState] = useState<ReportLifecycleState>("requested");
  const [lifecycleMessage, setLifecycleMessage] = useState(
    "Choose report scope and date range, then generate HTML report.",
  );

  function hasInvalidDateRange(): boolean {
    const { startDate, endDate } = controls;
    if (startDate.length === 0 || endDate.length === 0) {
      return true;
    }
    return startDate > endDate;
  }

  function handleGenerateHtmlReport(): void {
    const { scope, symbol } = controls;
    if (scope === "symbol" && symbol.trim().length === 0) {
      setLifecycleState("error");
      setLifecycleMessage("Symbol is required when scope is set to Symbol.");
      return;
    }
    if (hasInvalidDateRange()) {
      setLifecycleState("error");
      setLifecycleMessage("Start date cannot be after end date.");
      return;
    }
    setLifecycleState("generated");
    setLifecycleMessage(
      `HTML report generated for ${scope === "symbol" ? symbol.trim().toUpperCase() : "portfolio"} scope.`,
    );
  }

  function handleExportAnalystPack(): void {
    if (lifecycleState !== "generated" && lifecycleState !== "preview_ready") {
      setLifecycleState("unavailable");
      setLifecycleMessage(
        "Analyst pack export unavailable until HTML report generation succeeds.",
      );
      return;
    }
    setLifecycleState("preview_ready");
    setLifecycleMessage("Analyst pack markdown is ready for export.");
  }

  function handleResetDateRange(): void {
    setStartDate(DEFAULT_START_DATE);
    setEndDate(DEFAULT_END_DATE);
    if (lifecycleState === "error") {
      setLifecycleState("requested");
      setLifecycleMessage("Date range reset. Generate report when ready.");
    }
  }

  return (
    <section className="report-utility-dock" aria-label="Compact report utility">
      <div className="report-utility-dock__header">
        <h3>Quant report utility</h3>
        <span className="report-utility-dock__state">
          Lifecycle: {formatLifecycleState(lifecycleState)}
        </span>
      </div>

      <div className="report-utility-dock__controls">
        <label>
          Scope
          <select
            value={controls.scope}
            onChange={(event) => {
              const nextValue = event.target.value;
              if (nextValue === "portfolio" || nextValue === "symbol") {
                setScope(nextValue);
              }
            }}
          >
            <option value="portfolio">Portfolio</option>
            <option value="symbol">Symbol</option>
          </select>
        </label>
        <label>
          Symbol (optional)
          <input
            type="text"
            value={controls.symbol}
            onChange={(event) => setSymbol(event.target.value)}
            disabled={controls.scope !== "symbol"}
            placeholder="Ticker symbol"
          />
        </label>
        <label>
          Start date
          <input
            type="date"
            value={controls.startDate}
            onChange={(event) => setStartDate(event.target.value)}
          />
        </label>
        <label>
          End date
          <input
            type="date"
            value={controls.endDate}
            onChange={(event) => setEndDate(event.target.value)}
          />
        </label>
        <button
          aria-label="Reset report date range"
          className="report-utility-dock__icon-action"
          onClick={handleResetDateRange}
          title="Reset date range"
          type="button"
        >
          ↺
        </button>
      </div>

      <div className="report-utility-dock__actions">
        <button className="is-primary" type="button" onClick={handleGenerateHtmlReport}>
          Generate HTML report
        </button>
        <button type="button" onClick={handleExportAnalystPack}>
          Export analyst pack (.md)
        </button>
      </div>

      <p className="report-utility-dock__message" role="status" aria-live="polite">
        {lifecycleMessage}
      </p>

      <div className="report-utility-dock__provenance">
        <span>Source posture: deterministic contracts only</span>
        <span>Date range: {controls.startDate} to {controls.endDate}</span>
      </div>
      <div className="report-utility-dock__provenance">
        <span>
          {stateSourceLabel}: scope={controls.scope} | symbol=
          {controls.symbol.length === 0 ? "NONE" : controls.symbol} | start=
          {controls.startDate} | end={controls.endDate}
        </span>
      </div>
    </section>
  );
}

function ReportUtilityDockWithLocalState() {
  const controlBindings = useLocalReportControlsBindings();
  return <ReportUtilityDockSurface {...controlBindings} />;
}

function ReportUtilityDockWithUrlState() {
  const controlBindings = useUrlReportControlsBindings();
  return <ReportUtilityDockSurface {...controlBindings} />;
}

export function ReportUtilityDock() {
  const hasRouterContext = useInRouterContext();
  if (hasRouterContext) {
    return <ReportUtilityDockWithUrlState />;
  }
  return <ReportUtilityDockWithLocalState />;
}

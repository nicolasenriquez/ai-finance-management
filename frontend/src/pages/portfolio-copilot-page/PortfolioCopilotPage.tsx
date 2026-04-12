import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  useLocation,
  useSearchParams,
} from "react-router-dom";

import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import {
  WorkspaceCopilotComposer,
} from "../../components/workspace-layout/WorkspaceCopilotLauncher";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import type {
  PortfolioChartPeriod,
  PortfolioQuantReportScope,
} from "../../core/api/schemas";
import { usePortfolioCopilotWorkspace } from "../../features/portfolio-copilot/workspace-session";
import { fetchPortfolioSummary } from "../../features/portfolio-summary/api";
import { PortfolioChartPeriodControl } from "../../features/portfolio-workspace/PortfolioChartPeriodControl";
import { resolvePortfolioChartPeriod } from "../../features/portfolio-workspace/period";

function resolveScopeFromSearchParams(
  searchParams: URLSearchParams,
): PortfolioQuantReportScope {
  const scope = searchParams.get("scope");
  if (scope === "instrument_symbol") {
    return "instrument_symbol";
  }
  return "portfolio";
}

function resolveInstrumentSymbolFromSearchParams(
  searchParams: URLSearchParams,
): string | null {
  const instrumentSymbol = searchParams.get("instrument_symbol");
  if (!instrumentSymbol) {
    return null;
  }
  const normalizedInstrumentSymbol = instrumentSymbol.trim().toUpperCase();
  return normalizedInstrumentSymbol.length > 0
    ? normalizedInstrumentSymbol
    : null;
}

function resolvePeriodFromSearchParams(
  searchParams: URLSearchParams,
): PortfolioChartPeriod | null {
  const rawPeriod = searchParams.get("period");
  if (!rawPeriod) {
    return null;
  }
  return resolvePortfolioChartPeriod(rawPeriod, "90D");
}

export function PortfolioCopilotPage() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const { state, actions } = usePortfolioCopilotWorkspace();
  const {
    applyLaunchContext,
    setIsLauncherOpen,
    setIsLauncherCollapsed,
  } = actions;
  const [portfolioSymbolSuggestions, setPortfolioSymbolSuggestions] = useState<string[]>(
    [],
  );

  const syncSignature = useMemo(() => searchParams.toString(), [searchParams]);
  useEffect(() => {
    const nextSearchParams = new URLSearchParams(syncSignature);
    applyLaunchContext({
      route: location.pathname,
      period: resolvePeriodFromSearchParams(nextSearchParams),
      scope: resolveScopeFromSearchParams(nextSearchParams),
      instrumentSymbol: resolveInstrumentSymbolFromSearchParams(nextSearchParams),
      source: "expanded_route",
    });
    setIsLauncherOpen(false);
    setIsLauncherCollapsed(false);
  }, [
    applyLaunchContext,
    location.pathname,
    setIsLauncherCollapsed,
    setIsLauncherOpen,
    syncSignature,
  ]);

  useEffect(() => {
    let isActive = true;
    async function hydratePortfolioSymbols(): Promise<void> {
      try {
        const summary = await fetchPortfolioSummary();
        if (!isActive) {
          return;
        }
        const symbols = summary.rows
          .map((row) => row.instrument_symbol.trim().toUpperCase())
          .filter((symbol, index, array) => {
            return symbol.length > 0 && array.indexOf(symbol) === index;
          });
        setPortfolioSymbolSuggestions(symbols);
      } catch {
        if (isActive) {
          setPortfolioSymbolSuggestions([]);
        }
      }
    }
    void hydratePortfolioSymbols();
    return () => {
      isActive = false;
    };
  }, []);

  const activeCandidates = state.latestResponse?.opportunity_candidates || [];
  const activeNarration =
    state.latestResponse?.opportunity_narration ||
    state.latestResponse?.answer_text ||
    "";
  const historyPreview = state.conversationTurns.slice(-8);

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Copilot chat"
      title="Portfolio copilot"
      description="Chat-first read-only copilot with evidence traceability, deterministic candidate scanning, and typed state boundaries."
      layoutVariant="chat"
      showCommandPaletteTools={false}
      showMarketPulse={false}
      showTrustPanel={false}
      actions={
        <>
          <PortfolioChartPeriodControl
            onChange={actions.setPeriod}
            value={state.period}
          />
          <label className="period-control">
            <span className="period-control__label">Operation</span>
            <select
              aria-label="Copilot operation"
              className="period-control__select"
              onChange={(event) =>
                actions.setOperation(event.target.value as typeof state.operation)
              }
              value={state.operation}
            >
              <option value="chat">chat</option>
              <option value="opportunity_scan">opportunity_scan</option>
            </select>
          </label>
        </>
      }
      freshnessTimestamp={state.latestResponse?.evidence[0]?.as_of_ledger_at || undefined}
      scopeLabel="Read-only copilot bounded to allowlisted analytics tools"
      provenanceLabel="Backend /portfolio/copilot/chat contract"
      provenanceTooltip="ready | blocked | error typed state contract"
      periodLabel={state.period}
    >
      {state.uiState === "error" && state.uiErrorMessage ? (
        <ErrorBanner
          title="Copilot error"
          message={state.uiErrorMessage}
          variant="error"
        />
      ) : null}

      <section className="panel copilot-panel copilot-panel--chat">
        <header className="panel__header">
          <h2 className="panel__title">Copilot conversation</h2>
          <p className="panel__subtitle">
            Ask one scoped portfolio question per turn. Input remains bounded to 2000
            characters and 8 prior turns.
          </p>
        </header>
        <div className="panel__body">
          <WorkspaceCopilotComposer
            compact={false}
            symbolSuggestions={portfolioSymbolSuggestions}
          />
        </div>
      </section>

      <section className="copilot-secondary-grid">
        <section className="panel copilot-opportunity-panel">
          <header className="panel__header">
            <h2 className="panel__title">Opportunity candidate scanner</h2>
            <p className="panel__subtitle">
              Opportunity candidate ranking is deterministic; AI narration is rendered
              separately.
            </p>
          </header>
          <div className="panel__body">
            {activeCandidates.length > 0 ? (
              <div className="copilot-opportunity-table-wrapper">
                <table className="copilot-opportunity-table">
                  <caption>Deterministic candidate list</caption>
                  <thead>
                    <tr>
                      <th>Candidate</th>
                      <th>Action state</th>
                      <th>Held</th>
                      <th>Action multiplier</th>
                      <th>Drawdown vs 52W high</th>
                      <th>Opportunity score</th>
                      <th>Discount score</th>
                      <th>Momentum score</th>
                      <th>Stability score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeCandidates.map((candidate) => (
                      <tr key={candidate.symbol}>
                        <td>{candidate.symbol}</td>
                        <td>{candidate.action_state}</td>
                        <td>{candidate.currently_held ? "yes" : "no"}</td>
                        <td>{candidate.action_multiplier}</td>
                        <td>{candidate.drawdown_from_52w_high_pct}</td>
                        <td>{candidate.opportunity_score}</td>
                        <td>{candidate.discount_score}</td>
                        <td>{candidate.momentum_score}</td>
                        <td>{candidate.stability_score}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>No opportunity candidate data available yet.</p>
            )}

            <article className="copilot-opportunity-narration">
              <h3>AI narration</h3>
              <div className="copilot-markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {activeNarration || "Narration pending first successful response."}
                </ReactMarkdown>
              </div>
            </article>
          </div>
        </section>

        <section className="panel copilot-history-panel">
          <header className="panel__header">
            <h2 className="panel__title">Conversation history</h2>
            <p className="panel__subtitle">Bounded to most recent 8 turns.</p>
          </header>
          <div className="panel__body">
            {historyPreview.length > 0 ? (
              <ol className="copilot-history-list">
                {historyPreview.map((turn, index) => (
                  <li key={`${turn.role}-${index}`}>
                    <strong>{turn.role}</strong>
                    <div className="copilot-history-list__content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {turn.content}
                      </ReactMarkdown>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p>No conversation turns captured yet.</p>
            )}
          </div>
        </section>
      </section>
    </PortfolioWorkspaceLayout>
  );
}

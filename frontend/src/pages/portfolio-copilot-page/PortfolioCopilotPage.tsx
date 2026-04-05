import { useEffect, useMemo } from "react";
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

  const syncSignature = useMemo(() => searchParams.toString(), [searchParams]);
  useEffect(() => {
    const nextSearchParams = new URLSearchParams(syncSignature);
    actions.applyLaunchContext({
      route: location.pathname,
      period: resolvePeriodFromSearchParams(nextSearchParams),
      scope: resolveScopeFromSearchParams(nextSearchParams),
      instrumentSymbol: resolveInstrumentSymbolFromSearchParams(nextSearchParams),
      source: "expanded_route",
    });
    actions.setIsLauncherOpen(false);
    actions.setIsLauncherCollapsed(false);
  }, [actions, location.pathname, syncSignature]);

  const activeCandidates = state.latestResponse?.opportunity_candidates || [];
  const activeNarration =
    state.latestResponse?.opportunity_narration ||
    state.latestResponse?.answer_text ||
    "";
  const historyPreview = state.conversationTurns.slice(-8);

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Copilot route"
      title="Read-only portfolio copilot"
      description="Guardrailed chat + deterministic opportunity scanner with explicit state handling, evidence traceability, and non-advice limitations."
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

      <section className="panel copilot-panel">
        <header className="panel__header">
          <h2 className="panel__title">Copilot prompt composer</h2>
          <p className="panel__subtitle">
            Submit one scoped portfolio question. Input is bounded to 2000 chars and
            8 prior turns.
          </p>
        </header>
        <div className="panel__body">
          <WorkspaceCopilotComposer compact={false} />
        </div>
      </section>

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
                  <span>{turn.content}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p>No conversation turns captured yet.</p>
          )}
        </div>
      </section>
    </PortfolioWorkspaceLayout>
  );
}

import { useMemo, useState, type FormEvent } from "react";

import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { AppApiError } from "../../core/api/errors";
import type {
  PortfolioChartPeriod,
  PortfolioCopilotChatResponse,
  PortfolioCopilotConversationMessage,
  PortfolioCopilotOperation,
  PortfolioCopilotReasonCode,
  PortfolioCopilotResponseState,
  PortfolioQuantReportScope,
} from "../../core/api/schemas";
import { PortfolioChartPeriodControl } from "../../features/portfolio-workspace/PortfolioChartPeriodControl";
import { usePortfolioCopilotChatMutation } from "../../features/portfolio-copilot/hooks";

type CopilotUiState = "idle" | "loading" | "blocked" | "error" | "ready";

const REASON_MESSAGE_BY_CODE: Record<PortfolioCopilotReasonCode, string> = {
  boundary_restricted:
    "Request is outside the read-only portfolio copilot boundary.",
  insufficient_context:
    "Required portfolio or market context is insufficient for this request.",
  provider_blocked_policy:
    "Provider policy or permission blocked this request.",
  rate_limited:
    "Provider rate limit reached. Retry after a short cooldown window.",
  provider_misconfigured:
    "Provider configuration is invalid or incomplete.",
  provider_unavailable:
    "Provider is temporarily unavailable or timed out.",
};

function resolveApiErrorMessage(error: unknown): string {
  if (error instanceof AppApiError && error.detail) {
    return error.detail;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "Copilot request failed unexpectedly.";
}

function resolveReasonMessage(reasonCode: PortfolioCopilotReasonCode | null): string {
  if (reasonCode === null) {
    return "No reason code provided.";
  }
  return REASON_MESSAGE_BY_CODE[reasonCode];
}

function mapResponseStateToUiState(
  responseState: PortfolioCopilotResponseState,
): CopilotUiState {
  if (responseState === "ready") {
    return "ready";
  }
  if (responseState === "blocked") {
    return "blocked";
  }
  return "error";
}

export function PortfolioCopilotPage() {
  const [period, setPeriod] = useState<PortfolioChartPeriod>("90D");
  const [operation, setOperation] = useState<PortfolioCopilotOperation>("chat");
  const [scope, setScope] = useState<PortfolioQuantReportScope>("portfolio");
  const [instrumentSymbol, setInstrumentSymbol] = useState("");
  const [draftMessage, setDraftMessage] = useState("");
  const [conversationTurns, setConversationTurns] = useState<
    PortfolioCopilotConversationMessage[]
  >([]);
  const [uiState, setUiState] = useState<CopilotUiState>("idle");
  const [latestResponse, setLatestResponse] = useState<PortfolioCopilotChatResponse | null>(
    null,
  );
  const [uiErrorMessage, setUiErrorMessage] = useState<string | null>(null);
  const copilotMutation = usePortfolioCopilotChatMutation();

  const trimmedMessage = draftMessage.trim();
  const normalizedInstrumentSymbol = instrumentSymbol.trim().toUpperCase();
  const isScopeRequestReady =
    scope === "portfolio" || normalizedInstrumentSymbol.length > 0;
  const isSubmitDisabled =
    trimmedMessage.length === 0 ||
    copilotMutation.isPending ||
    !isScopeRequestReady;
  const effectiveUiState: CopilotUiState = copilotMutation.isPending
    ? "loading"
    : uiState;
  const effectiveReasonCode = latestResponse?.reason_code ?? null;

  const activeLimitations = latestResponse?.limitations ?? [];
  const activeEvidence = latestResponse?.evidence ?? [];
  const activeCandidates = latestResponse?.opportunity_candidates ?? [];
  const activeNarration =
    latestResponse?.opportunity_narration || latestResponse?.answer_text || "";

  const historyPreview = useMemo(
    () => conversationTurns.slice(-8),
    [conversationTurns],
  );

  async function handleCopilotSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (isSubmitDisabled) {
      return;
    }

    const userTurn: PortfolioCopilotConversationMessage = {
      role: "user",
      content: trimmedMessage.slice(0, 2000),
    };
    const boundedTurns = [...conversationTurns, userTurn].slice(-8);

    setConversationTurns(boundedTurns);
    setUiState("loading");
    setUiErrorMessage(null);

    try {
      const response = await copilotMutation.mutateAsync({
        operation,
        messages: boundedTurns,
        period,
        scope,
        instrument_symbol:
          scope === "instrument_symbol" ? normalizedInstrumentSymbol : null,
        max_tool_calls: 6,
      });
      setLatestResponse(response);
      const nextUiState = mapResponseStateToUiState(response.state);
      setUiState(nextUiState);

      if (response.state === "ready" && response.answer_text.trim().length > 0) {
        setConversationTurns((previousTurns) => [
          ...previousTurns.slice(-7),
          {
            role: "assistant",
            content: response.answer_text.trim(),
          },
        ]);
      }
      setDraftMessage("");
    } catch (error) {
      setUiState("error");
      setUiErrorMessage(resolveApiErrorMessage(error));
    }
  }

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Copilot route"
      title="Read-only portfolio copilot"
      description="Guardrailed chat + deterministic opportunity scanner with explicit state handling, evidence traceability, and non-advice limitations."
      actions={
        <>
          <PortfolioChartPeriodControl value={period} onChange={setPeriod} />
          <label className="period-control">
            <span className="period-control__label">Operation</span>
            <select
              aria-label="Copilot operation"
              className="period-control__select"
              value={operation}
              onChange={(event) =>
                setOperation(event.target.value as PortfolioCopilotOperation)
              }
            >
              <option value="chat">chat</option>
              <option value="opportunity_scan">opportunity_scan</option>
            </select>
          </label>
        </>
      }
      freshnessTimestamp={activeEvidence[0]?.as_of_ledger_at || undefined}
      scopeLabel="Read-only copilot bounded to allowlisted analytics tools"
      provenanceLabel="Backend /portfolio/copilot/chat contract"
      provenanceTooltip="ready | blocked | error typed state contract"
      periodLabel={period}
    >
      <section className="panel copilot-panel">
        <header className="panel__header">
          <h2 className="panel__title">Copilot prompt composer</h2>
          <p className="panel__subtitle">
            Submit one scoped portfolio question. Input is bounded to 2000 chars and
            8 prior turns.
          </p>
        </header>
        <div className="panel__body">
          <form className="copilot-composer" onSubmit={(event) => void handleCopilotSubmit(event)}>
            <div className="transactions-filters transactions-filters--compact">
              <label className="transactions-filters__field">
                <span>Scope</span>
                <select
                  aria-label="Copilot scope"
                  className="transactions-filters__select"
                  value={scope}
                  onChange={(event) =>
                    setScope(event.target.value as PortfolioQuantReportScope)
                  }
                >
                  <option value="portfolio">portfolio</option>
                  <option value="instrument_symbol">instrument_symbol</option>
                </select>
              </label>
              {scope === "instrument_symbol" ? (
                <label className="transactions-filters__field">
                  <span>Instrument symbol</span>
                  <input
                    aria-label="Copilot instrument symbol"
                    className="transactions-filters__input"
                    maxLength={16}
                    placeholder="AAPL"
                    value={instrumentSymbol}
                    onChange={(event) => setInstrumentSymbol(event.target.value)}
                  />
                </label>
              ) : null}
            </div>

            <label className="copilot-composer__field" htmlFor="copilot-message-input">
              Question
            </label>
            <textarea
              id="copilot-message-input"
              aria-label="Copilot user message"
              className="copilot-composer__textarea"
              maxLength={2000}
              placeholder="Explain recent portfolio risk posture and concentration changes."
              value={draftMessage}
              onChange={(event) => setDraftMessage(event.target.value)}
            />
            <div className="copilot-composer__footer">
              <span aria-live="polite" className="copilot-composer__counter">
                {draftMessage.length}/2000 characters
              </span>
              <button
                className={copilotMutation.isPending ? "button-primary button-primary--loading" : "button-primary"}
                disabled={isSubmitDisabled}
                type="submit"
              >
                {copilotMutation.isPending ? "Submitting..." : "Submit request"}
              </button>
            </div>
          </form>
        </div>
      </section>

      {effectiveUiState === "error" && uiErrorMessage ? (
        <ErrorBanner
          title="Copilot error"
          message={uiErrorMessage}
          variant="error"
        />
      ) : null}

      <section className="panel copilot-state-panel" aria-live="polite">
        <header className="panel__header">
          <h2 className="panel__title">Copilot state monitor</h2>
          <p className="panel__subtitle">
            Deterministic UI states: idle, loading, blocked, error, ready.
          </p>
        </header>
        <div className="panel__body">
          {effectiveUiState === "idle" ? (
            <p className="copilot-state copilot-state--idle">
              idle: waiting for one bounded read-only request.
            </p>
          ) : null}
          {effectiveUiState === "loading" ? (
            <p className="copilot-state copilot-state--loading">
              loading: request submitted, awaiting backend response.
            </p>
          ) : null}
          {effectiveUiState === "blocked" ? (
            <p className="copilot-state copilot-state--blocked">
              blocked: {resolveReasonMessage(effectiveReasonCode)}
            </p>
          ) : null}
          {effectiveUiState === "error" ? (
            <p className="copilot-state copilot-state--error">
              error: {resolveReasonMessage(effectiveReasonCode)}
            </p>
          ) : null}
          {effectiveUiState === "ready" ? (
            <article className="copilot-ready-response">
              <h3>ready</h3>
              <p>{latestResponse?.answer_text || "No answer text returned."}</p>
            </article>
          ) : null}
        </div>
      </section>

      <section className="panel copilot-evidence-panel">
        <header className="panel__header">
          <h2 className="panel__title">Evidence panel</h2>
          <p className="panel__subtitle">
            Explicit evidence references and limitation messaging for trust review.
          </p>
        </header>
        <div className="panel__body">
          {activeEvidence.length > 0 ? (
            <ul className="copilot-evidence-list">
              {activeEvidence.map((reference, index) => (
                <li key={`${reference.tool_id}-${index}`}>
                  <strong>{reference.tool_id}</strong>
                  <span>{reference.metric_id || "metric unavailable"}</span>
                  <span>{reference.as_of_ledger_at || "timestamp unavailable"}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p>No evidence references yet.</p>
          )}

          <h3>Limitations</h3>
          {activeLimitations.length > 0 ? (
            <ul className="copilot-limitation-list">
              {activeLimitations.map((limitation, index) => (
                <li key={`${limitation}-${index}`}>{limitation}</li>
              ))}
            </ul>
          ) : (
            <p>Limitation messaging will appear after first response.</p>
          )}
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
            <p>{activeNarration || "Narration pending first successful response."}</p>
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

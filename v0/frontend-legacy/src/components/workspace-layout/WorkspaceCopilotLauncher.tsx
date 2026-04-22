import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type DragEvent,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Link,
  useNavigate,
} from "react-router-dom";

import type {
  PortfolioChartPeriod,
  PortfolioCopilotEvidenceReference,
  PortfolioCopilotOperation,
  PortfolioQuantReportScope,
} from "../../core/api/schemas";
import { resolveReasonMessage } from "../../features/portfolio-copilot/presentation";
import { useOptionalPortfolioCopilotWorkspace } from "../../features/portfolio-copilot/workspace-session";
import {
  buildWorkspaceNavigationTarget,
  type WorkspaceNavigationContext,
} from "../../features/portfolio-workspace/context-carryover";

const PERIOD_OPTIONS: PortfolioChartPeriod[] = [
  "30D",
  "90D",
  "6M",
  "252D",
  "YTD",
  "MAX",
];

const INSTRUMENT_SYMBOL_SUGGESTIONS: readonly string[] = [
  "AMD",
  "AAPL",
  "MSFT",
  "NVDA",
  "AMZN",
  "GOOGL",
  "META",
  "TSLA",
  "SPY",
  "QQQ",
  "VOO",
  "BTC",
  "ETH",
];

const OPERATION_OPTIONS: PortfolioCopilotOperation[] = [
  "chat",
  "opportunity_scan",
];

const FINANCIAL_RECOMMENDATION_BUBBLES_CHAT: readonly string[] = [
  "Evaluate whether current concentration risk is aligned with a long-horizon capital preservation mandate and identify the top rebalance pressure points.",
  "Summarize benchmark-adjusted performance drivers by allocation sleeve and explain where active risk is creating or destroying value.",
  "Assess downside resilience by comparing drawdown behavior, recovery pace, and volatility clustering versus the benchmark.",
  "Identify positions with weak risk-adjusted contribution relative to weight and propose priority review candidates for disciplined reallocation.",
  "Review cashflow quality by separating return from contributions, withdrawals, dividends, fees, and price appreciation over the selected period.",
  "Explain whether current sector and single-name exposures are consistent with portfolio policy limits and diversification intent.",
  "Compare rolling-window consistency across 1Y, 3Y, and 5Y lenses and flag dependence on narrow market regimes.",
  "Produce an executive portfolio briefing covering performance, risk posture, concentration, and actionable monitoring priorities for the next quarter.",
];

const FINANCIAL_RECOMMENDATION_BUBBLES_DCA: readonly string[] = [
  "Classify current holdings into double-down, baseline DCA, and hold-off, and quantify post-DCA concentration impact by name and sector.",
  "Assess whether the proposed DCA cadence improves benchmark-relative drawdown resilience without breaching concentration policy limits.",
  "Prioritize DCA allocation across held positions using risk-adjusted contribution, drawdown regime, and volatility budget constraints.",
  "Estimate how a 12-week DCA plan changes portfolio risk posture, max single-name weight, and top-5 concentration.",
  "Compare baseline DCA versus 2x drawdown-trigger DCA and summarize trade-offs in downside capture, recovery participation, and concentration drift.",
  "Flag hold-off candidates where momentum and volatility proxies indicate elevated capital impairment risk despite attractive drawdown.",
  "Build an executive DCA brief with rationale, priority sleeves, risk controls, and monitoring triggers for the next reallocation window.",
  "Evaluate whether DCA additions are reinforcing existing winners or losers and recommend diversification-aware guardrails.",
];

function useDesktopViewport(): boolean {
  const [isDesktopViewport, setIsDesktopViewport] = useState(() => {
    return window.matchMedia("(min-width: 1024px)").matches;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia("(min-width: 1024px)");
    function handleViewportChange(event: MediaQueryListEvent): void {
      setIsDesktopViewport(event.matches);
    }
    setIsDesktopViewport(mediaQuery.matches);
    mediaQuery.addEventListener("change", handleViewportChange);
    return () => {
      mediaQuery.removeEventListener("change", handleViewportChange);
    };
  }, []);

  return isDesktopViewport;
}

function resolveScopeSummaryLabel(
  scope: PortfolioQuantReportScope,
  instrumentSymbol: string | null,
): string {
  if (scope === "instrument_symbol" && instrumentSymbol) {
    return `instrument ${instrumentSymbol}`;
  }
  return "portfolio";
}

type CopilotEvidenceDeepLink = {
  id: string;
  label: string;
  to: string;
  meta: string;
};

function resolveEvidenceDestinationPath(toolId: string): string {
  const normalizedToolId = toolId.toLowerCase();
  if (normalizedToolId.includes("risk")) {
    return "/portfolio/risk";
  }
  if (
    normalizedToolId.includes("quant") ||
    normalizedToolId.includes("report") ||
    normalizedToolId.includes("monte")
  ) {
    return "/portfolio/rebalancing";
  }
  if (
    normalizedToolId.includes("contribution") ||
    normalizedToolId.includes("time_series") ||
    normalizedToolId.includes("summary")
  ) {
    return "/portfolio/performance";
  }
  if (normalizedToolId.includes("transaction")) {
    return "/portfolio/transactions";
  }
  return "/portfolio/dashboard";
}

function buildEvidenceLinkTarget(params: {
  reference: PortfolioCopilotEvidenceReference;
  period: PortfolioChartPeriod;
  scope: PortfolioQuantReportScope;
  instrumentSymbol: string | null;
}): string {
  const destinationPath = resolveEvidenceDestinationPath(params.reference.tool_id);
  const searchParams = new URLSearchParams();
  searchParams.set("period", params.period);
  if (params.scope === "instrument_symbol" && params.instrumentSymbol) {
    searchParams.set("scope", "instrument_symbol");
    searchParams.set("instrument_symbol", params.instrumentSymbol);
  }
  if (params.reference.metric_id) {
    searchParams.set("focus_metric", params.reference.metric_id);
  }
  searchParams.set("evidence_tool", params.reference.tool_id);
  const query = searchParams.toString();
  return query.length > 0 ? `${destinationPath}?${query}` : destinationPath;
}

function buildEvidenceDeepLinks(params: {
  references: PortfolioCopilotEvidenceReference[];
  period: PortfolioChartPeriod;
  scope: PortfolioQuantReportScope;
  instrumentSymbol: string | null;
}): CopilotEvidenceDeepLink[] {
  return params.references.slice(0, 6).map((reference, index) => {
    const destinationPath = resolveEvidenceDestinationPath(reference.tool_id);
    const to = buildEvidenceLinkTarget({
      reference,
      period: params.period,
      scope: params.scope,
      instrumentSymbol: params.instrumentSymbol,
    });
    return {
      id: `${reference.tool_id}-${reference.metric_id ?? "metric"}-${index}`,
      label: reference.metric_id
        ? `${reference.tool_id} · ${reference.metric_id}`
        : reference.tool_id,
      to,
      meta: destinationPath,
    };
  });
}

function resolveAnswerHighlights(answerText: string): string[] {
  const lines = answerText
    .split("\n")
    .map((line) => line.replace(/^[-*]\s+/u, "").trim())
    .filter((line) => line.length > 0 && !line.startsWith("|"));
  const uniqueLines: string[] = [];
  for (const line of lines) {
    if (uniqueLines.includes(line)) {
      continue;
    }
    uniqueLines.push(line);
    if (uniqueLines.length >= 3) {
      break;
    }
  }
  return uniqueLines;
}

type WorkspaceCopilotComposerProps = {
  compact: boolean;
  symbolSuggestions?: string[];
};

type CopilotMarkdownProps = {
  content: string;
};

function CopilotMarkdown({ content }: CopilotMarkdownProps) {
  return (
    <div className="copilot-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}

export function WorkspaceCopilotComposer({
  compact,
  symbolSuggestions = [],
}: WorkspaceCopilotComposerProps) {
  const copilotWorkspace = useOptionalPortfolioCopilotWorkspace();
  const navigate = useNavigate();
  const [documentReferenceDraft, setDocumentReferenceDraft] = useState("");
  const [dropzoneHint, setDropzoneHint] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const dragDepthRef = useRef(0);
  const timelineRef = useRef<HTMLOListElement | null>(null);
  if (copilotWorkspace === null) {
    return null;
  }

  const { state, actions } = copilotWorkspace;
  const normalizedInstrumentSymbol = state.instrumentSymbol.trim().toUpperCase();
  const isScopeRequestReady =
    state.scope === "portfolio" || normalizedInstrumentSymbol.length > 0;
  const isSubmitDisabled =
    state.draftMessage.trim().length === 0 || state.isPending || !isScopeRequestReady;
  const latestResponse = state.latestResponse;
  const suggestions = latestResponse?.prompt_suggestions || [];
  const evidence = latestResponse?.evidence || [];
  const assumptions = latestResponse?.assumptions || [];
  const caveats = latestResponse?.caveats || latestResponse?.limitations || [];
  const suggestedFollowUps =
    latestResponse?.suggested_follow_ups || latestResponse?.prompt_suggestions || [];
  const limitations = latestResponse?.limitations || caveats;
  const currentState = state.uiState;
  const reasonCode = latestResponse?.reason_code || null;
  const launchContext = state.launchContext;
  const evidenceDeepLinks = useMemo(
    () =>
      buildEvidenceDeepLinks({
        references: evidence,
        period: state.period,
        scope: state.scope,
        instrumentSymbol:
          state.scope === "instrument_symbol"
            ? normalizedInstrumentSymbol || null
            : null,
      }),
    [evidence, normalizedInstrumentSymbol, state.period, state.scope],
  );
  const answerHighlights = useMemo(
    () => resolveAnswerHighlights(latestResponse?.answer || latestResponse?.answer_text || ""),
    [latestResponse?.answer, latestResponse?.answer_text],
  );
  const normalizedAnswerText =
    latestResponse?.answer || latestResponse?.answer_text || "";
  const handoffQueryString = useMemo(() => {
    const searchParams = new URLSearchParams();
    searchParams.set("period", state.period);
    if (state.scope === "instrument_symbol" && normalizedInstrumentSymbol.length > 0) {
      searchParams.set("scope", "instrument_symbol");
      searchParams.set("instrument_symbol", normalizedInstrumentSymbol);
    }
    return searchParams.toString();
  }, [normalizedInstrumentSymbol, state.period, state.scope]);
  const conversationTurns = state.conversationTurns;
  const instrumentSymbolSuggestions = useMemo(() => {
    const liveSymbols = symbolSuggestions
      .map((symbol) => symbol.trim().toUpperCase())
      .filter((symbol) => symbol.length > 0);
    const mergedSymbols = [...liveSymbols, ...INSTRUMENT_SYMBOL_SUGGESTIONS];
    return mergedSymbols.filter((symbol, index) => {
      return mergedSymbols.indexOf(symbol) === index;
    });
  }, [symbolSuggestions]);
  const recommendationBubbles = useMemo(() => {
    const recommendationCatalog =
      state.operation === "opportunity_scan"
        ? FINANCIAL_RECOMMENDATION_BUBBLES_DCA
        : FINANCIAL_RECOMMENDATION_BUBBLES_CHAT;
    const mergedSuggestions = [
      ...suggestions,
      ...recommendationCatalog,
    ];
    const uniqueSuggestions: string[] = [];
    for (const suggestion of mergedSuggestions) {
      const normalizedSuggestion = suggestion.trim();
      if (
        normalizedSuggestion.length === 0 ||
        uniqueSuggestions.includes(normalizedSuggestion)
      ) {
        continue;
      }
      uniqueSuggestions.push(normalizedSuggestion);
    }
    return uniqueSuggestions.slice(0, compact ? 4 : 10);
  }, [compact, state.operation, suggestions]);

  useEffect(() => {
    if (!timelineRef.current) {
      return;
    }
    timelineRef.current.scrollTop = timelineRef.current.scrollHeight;
  }, [conversationTurns.length, state.isPending]);

  function handleSuggestionKeydown(
    event: KeyboardEvent<HTMLButtonElement>,
    suggestion: string,
  ): void {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }
    event.preventDefault();
    void actions.submitCopilotRequest({ messageOverride: suggestion });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    void actions.submitCopilotRequest();
  }

  function handleMessageKeyDown(event: KeyboardEvent<HTMLTextAreaElement>): void {
    if (event.key !== "Enter") {
      return;
    }
    if (!event.shiftKey) {
      return;
    }
    event.preventDefault();
    if (!isSubmitDisabled) {
      void actions.submitCopilotRequest();
    }
  }

  function handleDropZoneDragOver(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault();
  }

  function handleChatDragEnter(event: DragEvent<HTMLDivElement>): void {
    if (compact || !event.dataTransfer.types.includes("Files")) {
      return;
    }
    event.preventDefault();
    dragDepthRef.current += 1;
    setIsDragActive(true);
  }

  function handleChatDragLeave(event: DragEvent<HTMLDivElement>): void {
    if (compact || !event.dataTransfer.types.includes("Files")) {
      return;
    }
    event.preventDefault();
    dragDepthRef.current = Math.max(0, dragDepthRef.current - 1);
    if (dragDepthRef.current === 0) {
      setIsDragActive(false);
    }
  }

  function handleDropZoneDrop(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault();
    dragDepthRef.current = 0;
    setIsDragActive(false);
    const droppedFilesCount = event.dataTransfer.files.length;
    if (droppedFilesCount > 0) {
      setDropzoneHint(
        `Detected ${droppedFilesCount} dropped file${droppedFilesCount > 1 ? "s" : ""}. Use ingestion first, then attach by document_id.`,
      );
      return;
    }
    setDropzoneHint("Drop detected. Use ingestion first, then attach by document_id.");
  }

  function handleAddDocumentReference(): void {
    const parsedDocumentId = Number.parseInt(documentReferenceDraft, 10);
    actions.addDocumentReference(parsedDocumentId);
    if (Number.isInteger(parsedDocumentId) && parsedDocumentId > 0) {
      setDocumentReferenceDraft("");
    }
  }

  return (
    <div
      className={
        compact
          ? "workspace-copilot-composer workspace-copilot-composer--compact"
          : "workspace-copilot-composer workspace-copilot-composer--full"
      }
    >
      {launchContext ? (
        compact ? (
        <section className="workspace-copilot-context" aria-live="polite">
          <strong>Launch context</strong>
          <p>
            Route {launchContext.route} · Period {launchContext.period || state.period} · Scope{" "}
            {resolveScopeSummaryLabel(
              launchContext.scope,
              launchContext.instrumentSymbol,
            )}
          </p>
        </section>
        ) : null
      ) : null}

      <section
        className="workspace-copilot-chat"
        aria-label="Copilot chat timeline"
        onDragEnter={handleChatDragEnter}
        onDragLeave={handleChatDragLeave}
        onDragOver={handleDropZoneDragOver}
        onDrop={handleDropZoneDrop}
      >
        <header className="workspace-copilot-chat__header">
          <div className="workspace-copilot-chat__title">
            <span aria-hidden="true" className="workspace-copilot-chat__status-dot" />
            <span className="workspace-copilot-chat__live-badge">Live</span>
          </div>
          <div className="workspace-copilot-chat__header-controls">
            <label className="workspace-copilot-chat__operation">
              <span>Operation</span>
              <select
                aria-label="Copilot operation"
                className="workspace-copilot-chat__operation-select"
                onChange={(event) =>
                  actions.setOperation(event.target.value as PortfolioCopilotOperation)
                }
                value={state.operation}
              >
                {OPERATION_OPTIONS.map((operationOption) => (
                  <option key={operationOption} value={operationOption}>
                    {operationOption}
                  </option>
                ))}
              </select>
            </label>
            <span
              className={`workspace-copilot-chat__state workspace-copilot-chat__state--${currentState}`}
            >
              {currentState}
            </span>
          </div>
        </header>
        {conversationTurns.length > 0 ? (
          <ol className="workspace-copilot-chat__timeline" ref={timelineRef}>
            {conversationTurns.map((turn, index) => (
              <li
                className={
                  turn.role === "user"
                    ? "workspace-copilot-chat__turn workspace-copilot-chat__turn--user"
                    : "workspace-copilot-chat__turn workspace-copilot-chat__turn--assistant"
                }
                key={`${turn.role}-${index}`}
              >
                <div className="workspace-copilot-chat__message">
                  <span
                    aria-hidden="true"
                    className={
                      turn.role === "user"
                        ? "workspace-copilot-chat__avatar workspace-copilot-chat__avatar--user"
                        : "workspace-copilot-chat__avatar workspace-copilot-chat__avatar--assistant"
                    }
                  >
                    {turn.role === "user" ? "You" : "AI"}
                  </span>
                  <div className="workspace-copilot-chat__content">
                    <span className="workspace-copilot-chat__speaker">
                      {turn.role === "user" ? "You" : "Copilot"}
                    </span>
                    <div className="workspace-copilot-chat__bubble">
                      {turn.role === "assistant" ? (
                        <CopilotMarkdown content={turn.content} />
                      ) : (
                        <p>{turn.content}</p>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
            {state.isPending ? (
              <li className="workspace-copilot-chat__turn workspace-copilot-chat__turn--assistant">
                <div className="workspace-copilot-chat__message">
                  <span
                    aria-hidden="true"
                    className="workspace-copilot-chat__avatar workspace-copilot-chat__avatar--assistant"
                  >
                    AI
                  </span>
                  <div className="workspace-copilot-chat__content">
                    <span className="workspace-copilot-chat__speaker">Copilot</span>
                    <div className="workspace-copilot-chat__bubble workspace-copilot-chat__bubble--typing">
                      <span className="workspace-copilot-chat__thinking-pulse" aria-hidden="true" />
                      <span>Thinking...</span>
                    </div>
                  </div>
                </div>
              </li>
            ) : null}
          </ol>
        ) : (
          <div className="workspace-copilot-chat__empty">
            <p>No conversation turns captured yet.</p>
            <small>Ask one portfolio question to start the chat timeline.</small>
          </div>
        )}
        {!compact && isDragActive ? (
          <div className="workspace-copilot-chat__drop-overlay">
            <strong>Drop file to stage reference</strong>
            <p>Ingest first, then chat can reference `document_id`.</p>
          </div>
        ) : null}
      </section>

      <form className="copilot-composer copilot-composer--chat" onSubmit={handleSubmit}>
        <div className="workspace-copilot-composer__controls">
          <label className="transactions-filters__field">
            <span>Period</span>
            <select
              aria-label="Copilot period"
              className="transactions-filters__select"
              onChange={(event) =>
                actions.setPeriod(event.target.value as PortfolioChartPeriod)
              }
              value={state.period}
            >
              {PERIOD_OPTIONS.map((periodOption) => (
                <option key={periodOption} value={periodOption}>
                  {periodOption}
                </option>
              ))}
            </select>
          </label>
          <label className="transactions-filters__field">
            <span>Scope</span>
            <select
              aria-label="Copilot scope"
              className="transactions-filters__select"
              onChange={(event) =>
                actions.setScope(event.target.value as PortfolioQuantReportScope)
              }
              value={state.scope}
            >
              <option value="portfolio">portfolio</option>
              <option value="instrument_symbol">instrument_symbol</option>
            </select>
          </label>
          {state.scope === "instrument_symbol" ? (
            <label className="transactions-filters__field">
              <span>Instrument symbol</span>
              <div className="workspace-copilot-symbol-combobox">
                <input
                  aria-label="Copilot instrument symbol"
                  className="transactions-filters__input"
                  list="workspace-copilot-instrument-symbols"
                  maxLength={16}
                  onChange={(event) => actions.setInstrumentSymbol(event.target.value)}
                  placeholder="Type or select symbol"
                  value={state.instrumentSymbol}
                />
                <datalist id="workspace-copilot-instrument-symbols">
                  {instrumentSymbolSuggestions.map((symbol) => (
                    <option key={symbol} value={symbol} />
                  ))}
                </datalist>
                <button
                  aria-label="Clear instrument symbol"
                  className="workspace-copilot-symbol-combobox__clear"
                  onClick={() => actions.setInstrumentSymbol("")}
                  type="button"
                >
                  ×
                </button>
              </div>
            </label>
          ) : null}
        </div>

        <label className="copilot-composer__field" htmlFor="workspace-copilot-message">
          Message
        </label>
        <div className="copilot-composer__message-shell">
          <textarea
            id="workspace-copilot-message"
            aria-label="Copilot user message"
            className="copilot-composer__textarea"
            maxLength={2000}
            onChange={(event) => actions.setDraftMessage(event.target.value)}
            onKeyDown={handleMessageKeyDown}
            placeholder={
              state.operation === "opportunity_scan"
                ? "Classify held symbols into double-down, baseline DCA, and hold-off with concentration impact context."
                : "Assess concentration, downside capture, and benchmark spread versus a long-term portfolio mandate."
            }
            value={state.draftMessage}
          />
          <button
            aria-label="Submit request"
            className={
              state.isPending
                ? "copilot-composer__submit-icon copilot-composer__submit-icon--loading"
                : "copilot-composer__submit-icon"
            }
            disabled={isSubmitDisabled}
            type="submit"
          >
            {state.isPending ? (
              <span aria-hidden="true" className="copilot-composer__submit-spinner" />
            ) : (
              <span aria-hidden="true" className="copilot-composer__submit-icon-glyph">
                ↗
              </span>
            )}
          </button>
        </div>

        {!compact ? null : (
          <section className="workspace-copilot-attachments">
          <h3>Document references</h3>
          <p>
            Attach by `document_id` only. For new files, use ingestion workflows before chat.
          </p>
          <div className="workspace-copilot-attachments__row">
            <input
              aria-label="Document ID reference"
              className="transactions-filters__input"
              inputMode="numeric"
              onChange={(event) => setDocumentReferenceDraft(event.target.value)}
              placeholder="123"
              value={documentReferenceDraft}
            />
            <button
              className="button-secondary"
              onClick={handleAddDocumentReference}
              type="button"
            >
              Add document reference
            </button>
          </div>
          {state.attachmentError ? (
            <p className="workspace-copilot-attachments__error">{state.attachmentError}</p>
          ) : null}
          {state.documentIds.length > 0 ? (
            <ul className="workspace-copilot-attachments__chips">
              {state.documentIds.map((documentId) => (
                <li key={documentId}>
                  <button
                    aria-label={`Remove document ${documentId}`}
                    className="workspace-copilot-attachments__chip"
                    onClick={() => actions.removeDocumentReference(documentId)}
                    type="button"
                  >
                    document_id:{documentId}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="workspace-copilot-attachments__empty">
              No document references attached.
            </p>
          )}
          </section>
        )}

        {!compact && dropzoneHint ? (
          <p className="workspace-copilot-dropzone__hint">{dropzoneHint}</p>
        ) : null}

        <div className="copilot-composer__footer">
          <span aria-live="polite" className="copilot-composer__counter">
            {state.draftMessage.length}/2000 characters
          </span>
        </div>

        {recommendationBubbles.length > 0 ? (
          <section className="workspace-copilot-suggestions">
            <h3>
              {state.operation === "opportunity_scan"
                ? "Quick DCA prompts"
                : "Quick prompts"}
            </h3>
            <div className="workspace-copilot-suggestions__list workspace-copilot-suggestions__list--dense">
              {recommendationBubbles.map((suggestion) => (
                <button
                  className="workspace-copilot-suggestions__chip"
                  key={suggestion}
                  onClick={() =>
                    void actions.submitCopilotRequest({
                      messageOverride: suggestion,
                    })
                  }
                  onKeyDown={(event) => handleSuggestionKeydown(event, suggestion)}
                  title={suggestion}
                  type="button"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </section>
        ) : null}
      </form>

      <section className="workspace-copilot-surfaces">
        <article
          className="workspace-copilot-surfaces__panel workspace-copilot-surfaces__panel--state"
          aria-live="polite"
        >
          <h3>Copilot state monitor</h3>
          {currentState === "idle" ? (
            <p className="copilot-state copilot-state--idle">
              idle: waiting for one bounded read-only request.
            </p>
          ) : null}
          {currentState === "loading" ? (
            <p className="copilot-state copilot-state--loading">
              loading: request submitted, awaiting backend response.
            </p>
          ) : null}
          {currentState === "blocked" ? (
            <p className="copilot-state copilot-state--blocked">
              blocked: {resolveReasonMessage(reasonCode)}
            </p>
          ) : null}
          {currentState === "error" ? (
            <p className="copilot-state copilot-state--error">
              error: {state.uiErrorMessage || resolveReasonMessage(reasonCode)}
            </p>
          ) : null}
          {currentState === "ready" ? (
            <article className="copilot-ready-response">
              <h3>ready</h3>
              <section className="copilot-structured-response" aria-label="Structured response overview">
                <h4>Answer</h4>
                {answerHighlights.length > 0 ? (
                  <ul className="copilot-structured-response__highlights">
                    {answerHighlights.map((highlight) => (
                      <li key={highlight}>Key point: {highlight}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="copilot-structured-response__empty">
                    Summary highlights appear after the first ready response.
                  </p>
                )}
              </section>
              <CopilotMarkdown
                content={normalizedAnswerText || "No answer text returned."}
              />
            </article>
          ) : null}
        </article>

        <article className="workspace-copilot-surfaces__panel workspace-copilot-surfaces__panel--evidence">
          <h3>Evidence and handoff panel</h3>
          {evidence.length > 0 ? (
            <ul className="copilot-evidence-list">
              {evidence.map((reference, index) => (
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
          {evidenceDeepLinks.length > 0 ? (
            <>
              <h4>Evidence deep links</h4>
              <div className="copilot-structured-response__links">
                {evidenceDeepLinks.map((deepLink) => (
                  <Link
                    className="copilot-structured-response__link"
                    key={deepLink.id}
                    to={deepLink.to}
                    onClick={(event) => {
                      event.preventDefault();
                      navigate(deepLink.to);
                    }}
                  >
                    <strong>{deepLink.label}</strong>
                    <span>{deepLink.meta}</span>
                  </Link>
                ))}
              </div>
            </>
          ) : null}
          <h4>Assumptions</h4>
          {assumptions.length > 0 ? (
            <ul className="copilot-limitation-list">
              {assumptions.map((assumption, index) => (
                <li key={`${assumption}-${index}`}>{assumption}</li>
              ))}
            </ul>
          ) : (
            <p>No explicit assumptions were returned.</p>
          )}
          <h4>Caveats and limitations</h4>
          {caveats.length > 0 ? (
            <ul className="copilot-limitation-list">
              {caveats.map((caveat, index) => (
                <li key={`${caveat}-${index}`}>{caveat}</li>
              ))}
            </ul>
          ) : (
            <p>Limitation messaging will appear after first response.</p>
          )}
          <h4>Suggested follow-ups</h4>
          {suggestedFollowUps.length > 0 ? (
            <div className="workspace-copilot-suggestions__list workspace-copilot-suggestions__list--dense">
              {suggestedFollowUps.map((followUp) => (
                <button
                  className="workspace-copilot-suggestions__chip"
                  key={followUp}
                  onClick={() => actions.applyPromptSuggestion(followUp)}
                  type="button"
                >
                  {followUp}
                </button>
              ))}
            </div>
          ) : (
            <p>No follow-up suggestions were provided.</p>
          )}
          <h4>Handoff destinations</h4>
          <div className="copilot-structured-response__links">
            <Link
              className="copilot-structured-response__link"
              to={
                handoffQueryString.length > 0
                  ? `/portfolio/dashboard?${handoffQueryString}`
                  : "/portfolio/dashboard"
              }
              onClick={(event) => {
                const target =
                  handoffQueryString.length > 0
                    ? `/portfolio/dashboard?${handoffQueryString}`
                    : "/portfolio/dashboard";
                event.preventDefault();
                navigate(target);
              }}
            >
              <strong>Dashboard what changed</strong>
              <span>/portfolio/dashboard</span>
            </Link>
            <Link
              className="copilot-structured-response__link"
              to={
                handoffQueryString.length > 0
                  ? `/portfolio/rebalancing?${handoffQueryString}`
                  : "/portfolio/rebalancing"
              }
              onClick={(event) => {
                const target =
                  handoffQueryString.length > 0
                    ? `/portfolio/rebalancing?${handoffQueryString}`
                    : "/portfolio/rebalancing";
                event.preventDefault();
                navigate(target);
              }}
            >
              <strong>News and rebalancing context</strong>
              <span>/portfolio/rebalancing</span>
            </Link>
            <Link
              className="copilot-structured-response__link"
              to={
                handoffQueryString.length > 0
                  ? `/portfolio/risk?${handoffQueryString}`
                  : "/portfolio/risk"
              }
              onClick={(event) => {
                const target =
                  handoffQueryString.length > 0
                    ? `/portfolio/risk?${handoffQueryString}`
                    : "/portfolio/risk";
                event.preventDefault();
                navigate(target);
              }}
            >
              <strong>Risk diagnostics</strong>
              <span>/portfolio/risk</span>
            </Link>
          </div>
          {limitations.length > 0 ? (
            <p className="workspace-copilot-attachments__empty">
              Legacy limitation field kept for compatibility.
            </p>
          ) : null}
        </article>
      </section>
    </div>
  );
}

type WorkspaceCopilotLauncherProps = {
  routePathname: string;
  currentContext: WorkspaceNavigationContext;
  symbolSuggestions?: string[];
};

export function WorkspaceCopilotLauncher({
  routePathname,
  currentContext,
  symbolSuggestions = [],
}: WorkspaceCopilotLauncherProps) {
  const navigate = useNavigate();
  const copilotWorkspace = useOptionalPortfolioCopilotWorkspace();
  const isDesktopViewport = useDesktopViewport();
  const expandedCopilotTarget = useMemo(() => {
    return buildWorkspaceNavigationTarget({
      destinationPath: "/portfolio/copilot",
      currentContext,
    });
  }, [currentContext]);

  if (copilotWorkspace === null) {
    return null;
  }

  const { state, actions } = copilotWorkspace;
  const launcherTriggerRef = useRef<HTMLButtonElement | null>(null);
  const previousRoutePathnameRef = useRef(routePathname);

  useEffect(() => {
    const previousRoutePathname = previousRoutePathnameRef.current;
    if (
      previousRoutePathname !== routePathname &&
      state.isLauncherOpen
    ) {
      actions.setIsLauncherOpen(false);
      actions.setIsLauncherCollapsed(false);
    }
    previousRoutePathnameRef.current = routePathname;
  }, [
    actions,
    routePathname,
    state.isLauncherOpen,
  ]);

  useEffect(() => {
    if (
      state.isLauncherOpen &&
      state.launchContext !== null &&
      state.launchContext.route !== routePathname
    ) {
      actions.setIsLauncherOpen(false);
      actions.setIsLauncherCollapsed(false);
    }
  }, [
    actions,
    routePathname,
    state.isLauncherCollapsed,
    state.isLauncherOpen,
    state.launchContext,
  ]);

  function handleOpenLauncher(): void {
    actions.applyLaunchContext({
      route: routePathname,
      period: currentContext.period,
      scope:
        currentContext.scope === "instrument_symbol" &&
        currentContext.instrumentSymbol !== null
          ? "instrument_symbol"
          : "portfolio",
      instrumentSymbol:
        currentContext.scope === "instrument_symbol"
          ? currentContext.instrumentSymbol
          : null,
      source: "workspace_shell",
    });
  }

  function closeLauncherAndRestoreFocus(): void {
    actions.setIsLauncherOpen(false);
    window.requestAnimationFrame(() => {
      launcherTriggerRef.current?.focus();
    });
  }

  return (
    <>
      <button
        aria-label="Open workspace copilot"
        className="button-secondary workspace-nav__copilot-trigger workspace-nav__utility-action"
        onClick={handleOpenLauncher}
        ref={launcherTriggerRef}
        type="button"
      >
        Open workspace copilot
      </button>

      {state.isLauncherOpen && isDesktopViewport ? (
        <aside
          aria-label="Workspace copilot docked panel"
          className={
            state.isLauncherCollapsed
              ? "panel workspace-copilot-dock workspace-copilot-dock--collapsed"
              : "panel workspace-copilot-dock"
          }
        >
          <header className="workspace-copilot-dock__header">
            <div className="workspace-copilot-dock__identity">
              <h2>Copilot assistant</h2>
              <p>Read-only portfolio chat</p>
            </div>
            <div className="workspace-copilot-dock__actions">
              <button
                aria-label={
                  state.isLauncherCollapsed
                    ? "Expand copilot panel"
                    : "Collapse copilot panel"
                }
                className="button-secondary"
                onClick={() => actions.setIsLauncherCollapsed(!state.isLauncherCollapsed)}
                type="button"
              >
                <span aria-hidden="true" className="workspace-copilot-dock__action-icon">
                  {state.isLauncherCollapsed ? "▢" : "▥"}
                </span>
                <span className="workspace-copilot-dock__action-label">
                  {state.isLauncherCollapsed ? "Expand" : "Collapse"}
                </span>
              </button>
              <button
                aria-label="Close workspace copilot"
                className="button-secondary"
                onClick={closeLauncherAndRestoreFocus}
                type="button"
              >
                <span aria-hidden="true" className="workspace-copilot-dock__action-icon">
                  ×
                </span>
                <span className="workspace-copilot-dock__action-label">Close</span>
              </button>
            </div>
          </header>
          {!state.isLauncherCollapsed ? (
            <WorkspaceCopilotComposer compact symbolSuggestions={symbolSuggestions} />
          ) : (
            <div className="workspace-copilot-dock__collapsed-copy">
              <p>Panel collapsed. Expand to continue chat, evidence, and limitation review.</p>
            </div>
          )}
        </aside>
      ) : null}

      {state.isLauncherOpen && !isDesktopViewport ? (
        <section
          aria-label="Workspace copilot mobile panel"
          aria-modal="true"
          className="workspace-copilot-mobile"
          role="dialog"
        >
          <header className="workspace-copilot-mobile__header">
            <div className="workspace-copilot-dock__identity">
              <h2>Copilot assistant</h2>
              <p>Read-only portfolio chat</p>
            </div>
            <div className="workspace-copilot-mobile__actions">
              <button
                aria-label="Open expanded copilot surface"
                className="button-secondary workspace-copilot-mobile__expanded-trigger"
                onClick={() => navigate(expandedCopilotTarget.to)}
                type="button"
              >
                Open expanded copilot surface
              </button>
              <button
                aria-label="Close workspace copilot"
                className="button-secondary"
                onClick={closeLauncherAndRestoreFocus}
                type="button"
              >
                Close
              </button>
            </div>
          </header>
          <div className="workspace-copilot-mobile__body">
            <WorkspaceCopilotComposer compact={false} symbolSuggestions={symbolSuggestions} />
          </div>
        </section>
      ) : null}
    </>
  );
}

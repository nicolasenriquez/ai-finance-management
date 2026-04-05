import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Link } from "react-router-dom";

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

const OPERATION_OPTIONS: PortfolioCopilotOperation[] = [
  "chat",
  "opportunity_scan",
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
    return "/portfolio/reports";
  }
  if (
    normalizedToolId.includes("contribution") ||
    normalizedToolId.includes("time_series") ||
    normalizedToolId.includes("summary")
  ) {
    return "/portfolio/analytics";
  }
  if (normalizedToolId.includes("transaction")) {
    return "/portfolio/transactions";
  }
  return "/portfolio/home";
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

export function WorkspaceCopilotComposer({ compact }: WorkspaceCopilotComposerProps) {
  const copilotWorkspace = useOptionalPortfolioCopilotWorkspace();
  const [documentReferenceDraft, setDocumentReferenceDraft] = useState("");
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
  const limitations = latestResponse?.limitations || [];
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
    () => resolveAnswerHighlights(latestResponse?.answer_text || ""),
    [latestResponse?.answer_text],
  );

  function handleSuggestionKeydown(
    event: KeyboardEvent<HTMLButtonElement>,
    suggestion: string,
  ): void {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }
    event.preventDefault();
    actions.applyPromptSuggestion(suggestion);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    void actions.submitCopilotRequest();
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
          : "workspace-copilot-composer"
      }
    >
      {launchContext ? (
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
      ) : null}

      <form className="copilot-composer" onSubmit={handleSubmit}>
        <div className="workspace-copilot-composer__controls">
          <label className="transactions-filters__field">
            <span>Operation</span>
            <select
              aria-label="Copilot operation"
              className="transactions-filters__select"
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
              <input
                aria-label="Copilot instrument symbol"
                className="transactions-filters__input"
                maxLength={16}
                onChange={(event) => actions.setInstrumentSymbol(event.target.value)}
                placeholder="AAPL"
                value={state.instrumentSymbol}
              />
            </label>
          ) : null}
        </div>

        <label className="copilot-composer__field" htmlFor="workspace-copilot-message">
          Question
        </label>
        <textarea
          id="workspace-copilot-message"
          aria-label="Copilot user message"
          className="copilot-composer__textarea"
          maxLength={2000}
          onChange={(event) => actions.setDraftMessage(event.target.value)}
          placeholder="Explain recent portfolio risk posture and concentration changes."
          value={state.draftMessage}
        />

        {suggestions.length > 0 ? (
          <section className="workspace-copilot-suggestions">
            <h3>Prompt suggestions</h3>
            <p>
              Suggestions are informational and remain inside read-only copilot boundaries.
            </p>
            <div className="workspace-copilot-suggestions__list">
              {suggestions.slice(0, 4).map((suggestion) => (
                <button
                  className="workspace-copilot-suggestions__chip"
                  key={suggestion}
                  onClick={() => actions.applyPromptSuggestion(suggestion)}
                  onKeyDown={(event) => handleSuggestionKeydown(event, suggestion)}
                  type="button"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </section>
        ) : null}

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

        <div className="copilot-composer__footer">
          <span aria-live="polite" className="copilot-composer__counter">
            {state.draftMessage.length}/2000 characters
          </span>
          <button
            className={state.isPending ? "button-primary button-primary--loading" : "button-primary"}
            disabled={isSubmitDisabled}
            type="submit"
          >
            {state.isPending ? "Submitting..." : "Submit request"}
          </button>
        </div>
      </form>

      <section className="workspace-copilot-surfaces">
        <article className="workspace-copilot-surfaces__panel" aria-live="polite">
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
                <h4>Response map</h4>
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
                {evidenceDeepLinks.length > 0 ? (
                  <div className="copilot-structured-response__links">
                    {evidenceDeepLinks.map((deepLink) => (
                      <Link className="copilot-structured-response__link" key={deepLink.id} to={deepLink.to}>
                        <strong>{deepLink.label}</strong>
                        <span>{deepLink.meta}</span>
                      </Link>
                    ))}
                  </div>
                ) : null}
              </section>
              <CopilotMarkdown
                content={latestResponse?.answer_text || "No answer text returned."}
              />
            </article>
          ) : null}
        </article>

        <article className="workspace-copilot-surfaces__panel">
          <h3>Evidence panel</h3>
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
          <h4>Limitations</h4>
          {limitations.length > 0 ? (
            <ul className="copilot-limitation-list">
              {limitations.map((limitation, index) => (
                <li key={`${limitation}-${index}`}>{limitation}</li>
              ))}
            </ul>
          ) : (
            <p>Limitation messaging will appear after first response.</p>
          )}
        </article>
      </section>
    </div>
  );
}

type WorkspaceCopilotLauncherProps = {
  routePathname: string;
  currentContext: WorkspaceNavigationContext;
};

export function WorkspaceCopilotLauncher({
  routePathname,
  currentContext,
}: WorkspaceCopilotLauncherProps) {
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
        className="button-secondary workspace-nav__copilot-trigger"
        onClick={handleOpenLauncher}
        ref={launcherTriggerRef}
        type="button"
      >
        Open workspace copilot
      </button>
      <Link className="button-secondary workspace-nav__copilot-link" to={expandedCopilotTarget.to}>
        Open expanded copilot surface
      </Link>

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
            <h2>Copilot assistant</h2>
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
                {state.isLauncherCollapsed ? "Expand" : "Collapse"}
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
          {!state.isLauncherCollapsed ? (
            <WorkspaceCopilotComposer compact />
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
            <h2>Copilot assistant</h2>
            <div className="workspace-copilot-mobile__actions">
              <Link className="button-secondary" to={expandedCopilotTarget.to}>
                Open expanded copilot surface
              </Link>
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
            <WorkspaceCopilotComposer compact={false} />
          </div>
        </section>
      ) : null}
    </>
  );
}

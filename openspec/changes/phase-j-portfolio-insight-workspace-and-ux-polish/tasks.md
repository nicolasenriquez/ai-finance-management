## 1. Scope and Experience Freeze

- [x] 1.1 Audit current portfolio workspace routes, shared layout primitives, duplicated controls, and first-viewport issues that this change will replace.
  Notes:
  - Audit baseline and route-by-route findings are frozen in `design.md` under `Frozen Execution Baseline (2026-04-05)`.
- [x] 1.2 Freeze the `phase-j` information architecture for persistent shell, command palette scope, context strip behavior, and copilot launch modes.
  Notes:
  - Shell zones, command-palette v1 scope, context carryover/reset contract, and responsive copilot launch modes are frozen in `design.md`.
- [x] 1.3 Freeze the `Core 10` KPI set, route ownership, and personal-finance decision tags before page refactors begin.
  Notes:
  - `Core 10` catalog with route ownership and decision tags is frozen in `design.md` for implementation use.
- [x] 1.4 Adopt `.codex/skills/emil-design-eng/SKILL.md` as a required UX polish rubric and record which principles are in scope for shell, navigation, and copilot interactions.
  Notes:
  - Skill-derived interaction and motion rules are frozen in `design.md` section `Emil Design Rubric Scope`.

## 2. Fail-First Navigation and Shell Tests

- [x] 2.1 Add fail-first frontend tests for persistent shell rendering, active-route indication, and stable route framing across portfolio surfaces.
  Notes:
  - Added fail-first contract suite `frontend/src/app/workspace-shell-navigation.contract.fail-first.test.ts`.
  - Contract asserts one nested `/portfolio` shell route and stable child framing requirements.
- [x] 2.2 Add fail-first tests for command palette route jump, symbol lookup, and compatible context carryover.
  Notes:
  - Added fail-first assertions for command-palette trigger contract, symbol lookup entrypoint, and destination-registry/context-carryover modules.
- [x] 2.3 Add fail-first tests proving incompatible scope or symbol context is reset explicitly instead of being submitted silently.
  Notes:
  - Added fail-first reset-policy contract requiring explicit incompatible-context reset semantics and copy contract in shared carryover utility.

## 3. Workspace Shell and Route Composition

- [x] 3.1 Implement shared workspace shell, context strip, and route-layout primitives for portfolio surfaces.
  Notes:
  - Extended shared shell with deterministic context carryover/reset handling, context reset banner copy, and reusable primary-job/state primitives in `frontend/src/components/workspace-layout/*` and `frontend/src/features/portfolio-workspace/*`.
- [x] 3.2 Implement the command palette interaction model and destination registry for routes, symbols, and approved analytical actions.
  Notes:
  - Implemented command destination registry plus route/symbol/action resolution in `frontend/src/features/portfolio-workspace/command-palette.ts` and wired `Cmd/Ctrl+K` shell interaction in `PortfolioWorkspaceLayout`.
- [x] 3.3 Refactor `Home`, `Analytics`, `Risk`, and `Quant/Reports` so each route owns one first-viewport analytical job and a clear `Core 10` interpretation layer.
  Notes:
  - Refactored primary routes to render `WorkspacePrimaryJobPanel` and `Core 10` first-pass interpretation before advanced modules.
- [x] 3.4 Add or wire explicit personal-finance insight modules for allocation drift, dividend income, goal progress, forecast confidence, and freshness or trust context.
  Notes:
  - Added/wired route modules for allocation drift (Analytics), dividend context (Home), goal-progress + forecast-confidence context (Quant/Reports), and persistent freshness/provenance trust strip in shared layout.
- [x] 3.5 Normalize route-level `loading`, `ready`, `stale`, `unavailable`, `blocked`, and `error` state presentation with shared utility copy and layout behavior.
  Notes:
  - Introduced shared lifecycle copy utility + `WorkspaceStateBanner` and applied normalized route-level state rendering across Home/Analytics/Risk/Reports.

## 4. Copilot Access and Context Integration

- [x] 4.1 Add fail-first tests for persistent copilot entry, desktop docked-collapsible presentation, mobile full-screen presentation, contextual launch from workspace routes, and answer continuity across presentation modes.
  Notes:
  - Added launcher contract coverage in `frontend/src/components/workspace-layout/WorkspaceCopilotLauncher.fail-first.test.tsx` including dock/mobile modes, context handoff, continuity, and collapse/focus behavior.
- [x] 4.2 Implement persistent copilot launcher behavior with desktop right-side docking plus collapse/expand controls and mobile full-screen presentation, while preserving a dedicated expanded copilot surface for deeper sessions.
  Notes:
  - Implemented persistent launcher/docked/mobile surfaces in `WorkspaceCopilotLauncher` and shared session state via `frontend/src/features/portfolio-copilot/workspace-session.tsx`.
- [x] 4.3 Implement explicit context handoff from analytical routes into the copilot composer for route, scope, symbol, and period when supported.
  Notes:
  - Wired launcher + expanded-route context application to composer launch context (`route/period/scope/instrumentSymbol`) using workspace navigation context/search-param synchronization.
- [x] 4.4 Preserve answer, evidence, and limitation surfaces when moving between persistent and expanded copilot presentations.
  Notes:
  - Unified persistent and expanded copilot rendering on one provider state so answer/evidence/limitations survive mode switches and route transitions.
- [x] 4.5 Add fail-first and implementation coverage for prompt-suggestion chips (bounded list, keyboard support, deterministic prefill behavior).
  Notes:
  - Added bounded suggestion-chip UI + keyboard prefill handling in shared composer and coverage in `PortfolioCopilotPage.test.tsx`.
- [x] 4.6 Implement composer attachment references for validated `document_id` chips (add/remove before submit) without introducing raw-file upload in chat.
  Notes:
  - Added document-reference chips (add/remove) and request wiring (`document_ids`) in frontend schemas/api/session flow; no multipart upload path introduced.

## 5. KPI Governance and Visual System Hardening

- [x] 5.1 Implement shared visual primitives for typography, spacing, section hierarchy, state banners, and restrained motion across the workspace shell.
  Notes:
  - Added shared shell/coplayout visual primitives and state-surface styles in `frontend/src/app/styles.css` (state banners, copilot surfaces, route hierarchy, spacing/motion constraints).
- [x] 5.2 Update KPI governance artifacts so promoted metrics carry `Core 10` or advanced tier, route ownership, and personal-finance decision tags.
  Notes:
  - Extended KPI catalog governance model with interpretation tier metadata and advanced entries in `frontend/src/features/portfolio-workspace/core-ten-catalog.ts`; documented catalog in `docs/product/portfolio-kpi-governance.md`.
- [x] 5.3 Update explainability copy and route labels so promoted metrics use portfolio and personal-finance semantics consistently.
  Notes:
  - Normalized shell route labels (`Home`, `Analytics`, `Risk`, `Quant/Reports`, `Copilot`) and aligned KPI interpretation copy/doc semantics with portfolio/personal-finance framing.
- [x] 5.4 Run an `emil-design-eng` polish review covering animation purpose/easing/duration, high-frequency interaction responsiveness, and button/input press feedback behavior.
  Notes:
  - Added explicit polish-review artifact using required Before/After/Why table format: `docs/product/phase-j-emil-design-polish-review.md`.

## 6. Validation and Handoff

- [x] 6.1 Add responsive and accessibility coverage for shell navigation, command palette, copilot launcher, panel collapse/focus behavior, suggestion chips, and route-level primary analytical actions.
  Notes:
  - Added responsive/a11y launcher coverage (mobile full-screen, collapse/expand, focus restoration, keyboard suggestion chips) plus route-primary-panel contract assertions in frontend tests.
- [x] 6.2 Run frontend validation gates (`lint`, `type-check`, `test`, `build`) and targeted backend contract tests if any route payload assumptions change.
  Notes:
  - Validation run complete: frontend `lint`, `type-check`, `test`, `build` passed; backend targeted copilot tests passed including integration-marked `test_ml_contract_extensions_fail_first.py` with explicit mutation authorization.
- [x] 6.3 Run OpenSpec status or validation checks, update delivery docs or changelog entries, and prepare implementation handoff notes.
  Notes:
  - Added governance/polish docs and changelog entry; OpenSpec validation/status checks rerun for handoff.

## 1. Scope and Experience Freeze

- [ ] 1.1 Audit current portfolio workspace routes, shared layout primitives, duplicated controls, and first-viewport issues that this change will replace.
- [ ] 1.2 Freeze the `phase-j` information architecture for persistent shell, command palette scope, context strip behavior, and copilot launch modes.
- [ ] 1.3 Freeze the `Core 10` KPI set, route ownership, and personal-finance decision tags before page refactors begin.

## 2. Fail-First Navigation and Shell Tests

- [ ] 2.1 Add fail-first frontend tests for persistent shell rendering, active-route indication, and stable route framing across portfolio surfaces.
- [ ] 2.2 Add fail-first tests for command palette route jump, symbol lookup, and compatible context carryover.
- [ ] 2.3 Add fail-first tests proving incompatible scope or symbol context is reset explicitly instead of being submitted silently.

## 3. Workspace Shell and Route Composition

- [ ] 3.1 Implement shared workspace shell, context strip, and route-layout primitives for portfolio surfaces.
- [ ] 3.2 Implement the command palette interaction model and destination registry for routes, symbols, and approved analytical actions.
- [ ] 3.3 Refactor `Home`, `Analytics`, `Risk`, and `Quant/Reports` so each route owns one first-viewport analytical job and a clear `Core 10` interpretation layer.
- [ ] 3.4 Add or wire explicit personal-finance insight modules for allocation drift, dividend income, goal progress, forecast confidence, and freshness or trust context.
- [ ] 3.5 Normalize route-level `loading`, `ready`, `stale`, `unavailable`, `blocked`, and `error` state presentation with shared utility copy and layout behavior.

## 4. Copilot Access and Context Integration

- [ ] 4.1 Add fail-first tests for persistent copilot entry, desktop docked-collapsible presentation, mobile full-screen presentation, contextual launch from workspace routes, and answer continuity across presentation modes.
- [ ] 4.2 Implement persistent copilot launcher behavior with desktop right-side docking plus collapse/expand controls and mobile full-screen presentation, while preserving a dedicated expanded copilot surface for deeper sessions.
- [ ] 4.3 Implement explicit context handoff from analytical routes into the copilot composer for route, scope, symbol, and period when supported.
- [ ] 4.4 Preserve answer, evidence, and limitation surfaces when moving between persistent and expanded copilot presentations.
- [ ] 4.5 Add fail-first and implementation coverage for prompt-suggestion chips (bounded list, keyboard support, deterministic prefill behavior).
- [ ] 4.6 Implement composer attachment references for validated `document_id` chips (add/remove before submit) without introducing raw-file upload in chat.

## 5. KPI Governance and Visual System Hardening

- [ ] 5.1 Implement shared visual primitives for typography, spacing, section hierarchy, state banners, and restrained motion across the workspace shell.
- [ ] 5.2 Update KPI governance artifacts so promoted metrics carry `Core 10` or advanced tier, route ownership, and personal-finance decision tags.
- [ ] 5.3 Update explainability copy and route labels so promoted metrics use portfolio and personal-finance semantics consistently.

## 6. Validation and Handoff

- [ ] 6.1 Add responsive and accessibility coverage for shell navigation, command palette, copilot launcher, panel collapse/focus behavior, suggestion chips, and route-level primary analytical actions.
- [ ] 6.2 Run frontend validation gates (`lint`, `type-check`, `test`, `build`) and targeted backend contract tests if any route payload assumptions change.
- [ ] 6.3 Run OpenSpec status or validation checks, update delivery docs or changelog entries, and prepare implementation handoff notes.

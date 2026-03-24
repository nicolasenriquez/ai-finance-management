# Frontend Architecture Guide

## Purpose

This guide defines the concrete frontend architecture for the MVP.
It bridges product scope, UX rules, and implementation decisions so frontend work can start without inventing structure during delivery.

This architecture is intentionally narrow:

- optimized for the current ledger-only analytics API
- designed for one frontend application, not a frontend platform
- strict about finance-safe formatting and explicit unsupported states

## Architectural Goals

- Keep the implementation simple and fast to ship.
- Preserve ledger-first truth without client-side invention.
- Separate server state, UI state, formatting, and view composition cleanly.
- Keep the frontend testable, accessible, and performance-aware from day one.

## Recommended Stack

- `React`
- `TypeScript`
- `Vite`
- `React Router`
- `@tanstack/react-query`
- `Zod`
- `decimal.js`
- `Vitest`
- `@testing-library/react`
- `Playwright`

## Why This Stack

- `React + TypeScript`: standard, productive, strong typing for UI contracts.
- `Vite`: minimal setup overhead and fast local iteration.
- `React Router`: enough routing for `/portfolio` and `/portfolio/:symbol` without extra complexity.
- `TanStack Query`: correct default for server-state lifecycles, retries, caching, and loading/error states.
- `Zod`: runtime validation at the API boundary so malformed payloads fail explicitly.
- `decimal.js`: avoids finance bugs from binary floating-point arithmetic.
- `Vitest + Testing Library + Playwright`: good MVP testing pyramid without overengineering.

## Explicit Non-Choices

- No global client state store such as Redux or Zustand in v1.
- No full UI component framework such as MUI, Ant Design, or Chakra.
- No charting library in v1.
- No SSR or Next.js requirement for the initial MVP.

Reason:

- current frontend scope is small
- backend contract is narrow and stable
- a custom design-system baseline is already documented
- introducing more infrastructure now would add drag without leverage

## Application Shape

Initial routes:

- `/portfolio`
- `/portfolio/:symbol`

Primary screens:

- portfolio summary screen
- lot-detail screen

Cross-cutting layout primitives:

- app shell
- page header
- timestamp badge
- error banner
- empty-state block
- loading skeletons

## Layering Model

Use a simple 5-layer frontend structure.

### 1. App Layer

Responsibility:

- application bootstrap
- router setup
- query client setup
- global providers
- global error boundaries

Examples:

- `App.tsx`
- router configuration
- query provider
- theme provider with semantic token bootstrap

### 2. Pages Layer

Responsibility:

- route-level composition
- screen layout orchestration
- page-specific loading/error/empty branching

Examples:

- `PortfolioSummaryPage`
- `PortfolioLotDetailPage`

### 3. Features Layer

Responsibility:

- domain-specific UI blocks and hooks
- feature composition around one business capability

Examples:

- summary table feature
- lot detail feature
- symbol detail header

### 4. Shared UI Layer

Responsibility:

- reusable presentational components
- design-system primitives
- generic UI states

Examples:

- `DataTable`
- `PageSection`
- `StatusBadge`
- `ErrorBanner`
- `EmptyState`
- `SkeletonRow`

### 5. Core Layer

Responsibility:

- API client
- schemas
- formatting utilities
- decimal helpers
- environment config
- test helpers

Examples:

- `api/client.ts`
- `api/schemas.ts`
- `lib/decimal.ts`
- `lib/formatters.ts`
- `config/env.ts`

## Recommended Folder Structure

```text
frontend/
├── public/
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   ├── providers.tsx
│   │   ├── router.tsx
│   │   └── styles.css
│   ├── pages/
│   │   ├── portfolio-summary-page/
│   │   │   └── PortfolioSummaryPage.tsx
│   │   └── portfolio-lot-detail-page/
│   │       └── PortfolioLotDetailPage.tsx
│   ├── features/
│   │   ├── portfolio-summary/
│   │   │   ├── api.ts
│   │   │   ├── hooks.ts
│   │   │   ├── PortfolioSummaryTable.tsx
│   │   │   └── PortfolioSummaryHeader.tsx
│   │   └── portfolio-lot-detail/
│   │       ├── api.ts
│   │       ├── hooks.ts
│   │       ├── PortfolioLotTable.tsx
│   │       └── PortfolioLotHeader.tsx
│   ├── components/
│   │   ├── app-shell/
│   │   ├── data-table/
│   │   ├── error-banner/
│   │   ├── empty-state/
│   │   ├── timestamp-badge/
│   │   └── skeletons/
│   ├── core/
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── errors.ts
│   │   │   └── schemas.ts
│   │   ├── config/
│   │   │   └── env.ts
│   │   ├── lib/
│   │   │   ├── decimal.ts
│   │   │   ├── formatters.ts
│   │   │   └── dates.ts
│   │   └── testing/
│   │       └── render.tsx
│   └── test/
│       ├── e2e/
│       └── fixtures/
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## Data Strategy

### Server State

Use `TanStack Query` for all API-driven state.

Reason:

- summary and lot-detail data are server-owned
- loading/error/retry behavior matters
- cache invalidation needs are simple

Recommended query keys:

- `["portfolio", "summary"]`
- `["portfolio", "lot-detail", symbol]`

Recommended defaults:

- short stale time for analytics reads
- no aggressive background polling in v1
- retry server failures conservatively
- do not retry `404` and `422`

## Theme Strategy

Use a narrow theme model for MVP:

- themes: `light` and `dark`
- persistence: `localStorage`
- initial resolution: stored user preference first, then `prefers-color-scheme`
- application: set `data-theme` on `document.documentElement`

Guidance:

- keep theme logic in the app layer, not in feature components
- keep all visual differences token-driven from `styles.css`
- do not add per-component ad hoc dark-mode branches unless a semantic token cannot express the change
- verify contrast, focus, and status semantics in both themes

## Screen Composition Guidance

Summary and lot-detail pages should follow the same hierarchy:

1. app shell and route framing
2. hero context explaining ledger scope
3. page header with `as_of_ledger_at`
4. derived overview cards clearly labeled as API-row-derived when applicable
5. primary data table or lot-card collection
6. explicit empty/error states

Rationale:

- keeps trust cues visible before data interpretation
- improves scanability on large screens
- preserves a deterministic mental model on mobile

### UI State

Use local component state for:

- row expansion
- table interaction state
- view-local toggles
- client-side filter text if later needed

Do not introduce a global store unless one of these becomes true:

- multiple unrelated screens need to coordinate the same writable state
- deep prop drilling becomes persistent and expensive
- local state duplication creates real defects

### Derived State

Keep derived state close to the page or feature boundary.

Examples:

- selected row visuals
- compact display mode
- grouped display metadata from already-fetched payloads

Do not derive unsupported finance metrics such as market value or unrealized return in the client.

## API Boundary Strategy

All HTTP access should go through a thin API layer in `core/api/`.

Rules:

- parse environment base URL once
- use one fetch client wrapper
- validate responses with `Zod`
- map HTTP failures into typed frontend error categories

Suggested error categories:

- `not_found`
- `validation_error`
- `server_error`
- `network_error`
- `unexpected_payload`

## Finance-Safe Numeric Strategy

Use `decimal.js` for:

- parsing money values
- parsing quantity values
- any comparison that affects UI logic
- any client-side derived display value

Rules:

- never use JavaScript `Number` for finance math
- keep quantities and money formatting centralized
- preserve backend precision semantics
- only round at defined formatting boundaries

Suggested utility split:

- `parseMoneyDecimal()`
- `parseQuantityDecimal()`
- `formatUsdMoney()`
- `formatQuantity()`
- `compareDecimal()`

## Component Strategy

### App Shell Components

- `AppShell`
- `PageHeader`
- `PageSection`

### Domain Components

- `PortfolioSummaryHeader`
- `PortfolioSummaryTable`
- `PortfolioSummaryRow`
- `PortfolioLotHeader`
- `PortfolioLotTable`
- `LotDispositionList`

### State Components

- `ErrorBanner`
- `EmptyState`
- `InlineNotice`
- `LoadingTableSkeleton`

### Utility Components

- `TimestampBadge`
- `SymbolChip`
- `MetricCell`
- `DefinitionTooltip`

## Page Composition Strategy

### `/portfolio`

Responsibilities:

- fetch summary data
- render page-level timestamp and scope note
- branch between loading, empty, error, and ready states
- route to lot detail on row activation

### `/portfolio/:symbol`

Responsibilities:

- normalize route param use
- fetch lot-detail data
- branch between loading, not-found, error, and ready states
- render canonical symbol from response, not from raw input

## Styling Strategy

Use the design-system guide as source of truth.

Implementation recommendation:

- global CSS variables for tokens
- scoped component CSS via CSS Modules or well-bounded co-located styles

Reason:

- keeps token use explicit
- avoids premature Tailwind-only utility sprawl
- matches the small size of the MVP

If the team strongly prefers Tailwind, keep these constraints:

- tokens still originate from CSS variables
- avoid one-off visual values in JSX
- do not bypass documented spacing/color/motion rules

## Accessibility Strategy

Frontend implementation must satisfy the repository frontend standard.

Operational requirements:

- semantic table markup for financial tables where appropriate
- visible keyboard focus on rows and controls
- reduced-motion support
- explicit error identification
- accessible names for all interactive controls

## Performance Strategy

The frontend MVP should optimize for fast initial usefulness, not animation or chart spectacle.

Rules:

- keep route bundles small
- defer non-critical enhancements
- avoid expensive client-side data reshaping
- render useful skeletons early
- keep image and font loading disciplined

## Testing Strategy

### Unit Tests

Target:

- formatters
- decimal utilities
- error mapping
- small presentational state branches

### Component Tests

Target:

- summary ready/loading/error/empty states
- lot-detail ready/loading/not-found/error states
- keyboard interaction for summary row activation

### E2E Tests

Target:

- summary route happy path
- lot-detail happy path
- unknown symbol flow
- server error rendering

## Suggested Implementation Order

1. Bootstrap app shell, router, query client, env config, and token foundation.
2. Build API client, schemas, error mapping, and decimal/formatting utilities.
3. Implement summary page and summary feature components.
4. Implement lot-detail page and disposition rendering.
5. Add accessibility, performance, and E2E hardening.

## Decision Summary

For the MVP, the frontend should be:

- one React + TypeScript app
- route-driven, not store-driven
- query-driven for server state
- decimal-safe for finance behavior
- custom design-system based, not framework-heavy
- tested through unit, component, and E2E layers

This is enough architecture to ship well without turning the MVP into framework theater.

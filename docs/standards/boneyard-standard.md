# Boneyard Standard: Skeleton Capture, Registry Lifecycle, and Loading UX

## Overview

This document defines how to use **Boneyard** in this repository for production-grade skeleton loading generated from real UI.

Boneyard is the standard for source-derived loading placeholders where the app already has stable renderable components and skeletons must stay aligned with the real interface.

## Why Boneyard

- Skeletons are generated from real UI, not hand-drawn approximations.
- A single workflow supports multiple frameworks through the same bone format.
- Registry-based loading is deterministic at runtime.
- Capture can be automated in development via CLI or Vite plugin.

## Scope

Applies to:

- route-level and module-level loading states tied to real components
- reusable skeletons for dashboard cards, tables, and detail panels
- automated recapture workflows after UI layout changes

Does not apply to:

- speculative placeholders for components that do not exist yet
- decorative skeletons disconnected from real component structure
- custom runtime loaders that bypass Boneyard registry workflow

## Installation and Dependency Policy

Use repository-managed frontend dependencies.

```bash
npm install boneyard-js
```

For Vite-based apps, prefer plugin-based capture by default.

## Core Usage Rules

### 1. Wrap real components with stable skeleton boundaries

Every skeletonized surface must use a `Skeleton` wrapper with a stable, unique `name`.

Rules:

- `name` must remain stable across refactors unless a deliberate migration is intended.
- One semantic surface maps to one skeleton name.
- Do not generate names dynamically per render.

Example:

```tsx
import { Skeleton } from "boneyard-js/react";

<Skeleton name="portfolio-card" loading={isLoading}>
  <PortfolioCard data={data} />
</Skeleton>;
```

### 2. Bones are generated artifacts

Do not manually maintain geometry when source UI can be updated and recaptured.

Rules:

- Update the real component first.
- Recapture bones after meaningful layout changes.
- Avoid manual placeholder drift from source UI.

### 3. Import registry once at app startup

Generated bones must be registered once in app bootstrap:

```ts
import "./bones/registry";
```

Do not duplicate registry imports across route components.

### 4. Prefer Vite plugin in Vite projects

If the frontend uses Vite, use `boneyardPlugin()` as default capture mode.

```ts
import { defineConfig } from "vite";
import { boneyardPlugin } from "boneyard-js/vite";

export default defineConfig({
  plugins: [boneyardPlugin()],
});
```

Use CLI-only mode when the project is non-Vite or needs explicit capture control.

### 5. Keep capture settings centralized

Shared capture behavior belongs in `boneyard.config.json`.

Recommended baseline:

```json
{
  "breakpoints": [375, 768, 1280],
  "out": "./src/bones",
  "wait": 800,
  "animate": "pulse"
}
```

Rules:

- Keep output path deterministic and consistent with registry imports.
- Keep breakpoints aligned with supported responsive tiers.
- Use per-component overrides only when justified.

### 6. Use props for behavior, not workflow drift

Common props include `loading`, `name`, `color`, `darkColor`, `animate`, `stagger`, `transition`, `boneClass`, `fixture`, `initialBones`, and `fallback`.

Rules:

- `loading` controls render state only.
- `fallback` is only for unavailable bones, not normal flow.
- `fixture` is development support only.
- `initialBones` is an escape hatch, not default.

### 7. Capture must follow UI changes

If a PR changes component layout, density, spacing, or responsive behavior, recapture associated bones in the same PR.

### 8. Use watch mode for active UI work

For iterative design work:

```bash
npx boneyard-js build --watch
```

### 9. Preserve responsive skeleton behavior

Breakpoint capture is part of the contract.

Rules:

- Do not reduce breakpoints to speed up capture unless product breakpoints changed.
- Any breakpoint policy change requires explicit review.

### 10. React Native uses native scanning

For React Native:

```bash
npx boneyard-js build --native --out ./bones
```

Use default font-scale capture and rely on runtime scaling support.

## Approved Workflows

### Vite-based web apps

```bash
npm install boneyard-js
# configure vite with boneyardPlugin()
# run normal dev server
```

### Non-Vite web apps

```bash
npm install boneyard-js
npx boneyard-js build
```

### Active recapture loop

```bash
npx boneyard-js build --watch
```

### Chrome session reuse

```bash
npx boneyard-js build --cdp 9222
```

### Env-file driven capture

```bash
npx boneyard-js build --env-file .env.local
```

## Loading UX Rules

- Use skeletons for content expected imminently.
- Prefer skeletons over spinners for dense dashboard modules.
- Do not render duplicated placeholder systems for the same surface.
- Keep animation mode consistent unless explicitly justified.

## Validation Rules

A Boneyard-related change is complete only when:

1. Source component renders correctly.
2. `Skeleton` uses a stable `name`.
3. Registry import exists at startup.
4. Bones were regenerated after layout changes.
5. Loading behavior was manually verified at supported breakpoints.

## Troubleshooting

### Skeleton does not render

- Confirm registry import path is valid.
- Confirm skeleton `name` matches generated artifact.
- Confirm output folder matches config and import location.

### Captured skeleton is stale

- Re-run capture after layout changes.
- Use `--force` when cache is suspected.

### Authenticated route capture needed

- Use `--cdp` against existing Chrome session, or `--env-file` where applicable.

### Routes not discovered

- Review route scanning behavior.
- Use `--no-scan` only intentionally.

## Validation Commands

```bash
npx boneyard-js build --force
npm run lint
npm run test
npm run build
```

## Resources (Official)

- Repository and README: https://github.com/0xGF/boneyard
- README direct: https://github.com/0xGF/boneyard#readme
- Releases: https://github.com/0xGF/boneyard/releases

---

**Last Updated:** 2026-04-18

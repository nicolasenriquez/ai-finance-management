# Frontend References

## Purpose

This file curates high-value external references for frontend quality, UX maturity, and design execution discipline.
Use these references for principles and constraints, not for blind copy-paste implementation.

## Priority 1: Direct Frontend Design Workflow

### OpenAI: Designing Delightful Frontends with GPT-5.4

- URL: https://developers.openai.com/blog/designing-delightful-frontends-with-gpt-5-4
- Why it matters:
  - practical prompt and workflow guidance for generating stronger UI outcomes
  - emphasizes explicit design principles, references, hierarchy, and interaction context
- What to apply:
  - define design constraints before coding
  - include utility-first guidance for dashboard-like products
  - iterate from concrete design critique, not generic prompts

### UI UX Pro Max Skill Repository

- URL: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- Why it matters:
  - structured design-system generation approach
  - domain-aware UX recommendations with accessibility and responsiveness checks
- What to apply:
  - lock a master design-system recommendation first
  - produce page-level overrides second
  - keep pre-delivery checks mandatory

### Impeccable Repository

- URL: https://github.com/pbakaus/impeccable
- Why it matters:
  - command-driven design refinement workflow
  - strong emphasis on context gathering before audits and polish
- What to apply:
  - define audience, use cases, and tone before UI review loops
  - run focused audit and normalization passes
  - keep UX writing and interaction clarity explicit

## Priority 2: Accessibility And Performance Authorities

### WCAG 2.2

- URL: https://www.w3.org/TR/WCAG22/
- Why it matters:
  - canonical accessibility standard for focus, contrast, target size, and interaction clarity
- What to apply:
  - WCAG 2.2 AA as baseline for frontend acceptance

### Core Web Vitals

- URL: https://web.dev/articles/defining-core-web-vitals-thresholds
- Why it matters:
  - objective user-centric performance baselines
- What to apply:
  - release gates for LCP, INP, and CLS

### MDN Accessibility Patterns

- URLs:
  - https://developer.mozilla.org/en-US/docs/Web/CSS/:focus
  - https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-label
  - https://developer.mozilla.org/en-US/docs/Web/CSS/%40media/prefers-reduced-motion
- Why it matters:
  - practical implementation guidance for keyboard focus, naming, and motion reduction
- What to apply:
  - enforce focus visibility, accessible naming, and reduced-motion compliance

## Local Cross-Reference

Before using any external pattern, validate it against:

- `docs/product/frontend-mvp-prd-addendum.md`
- `docs/guides/frontend-api-and-ux-guide.md`
- `docs/guides/frontend-design-system-guide.md`
- `docs/standards/frontend-standard.md`

## Usage Rule

- External references can inform quality and workflow.
- Local product constraints always take precedence.
- Any adopted pattern must map to repository scope and backend contract reality.

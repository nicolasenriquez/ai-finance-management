## MODIFIED Requirements

### Requirement: Dashboard visual system SHALL prioritize first-viewport compactness
The frontend SHALL define visual and layout rules that keep the dominant decision strip and hero insight visible in the first viewport on primary desktop use cases.

#### Scenario: First viewport stays compact and decision-oriented
- **WHEN** the compact dashboard renders on a standard desktop viewport
- **THEN** the primary decision strip, hero module, and top action framing are visible without relying on long vertical scrolling
- **THEN** supporting modules use bounded density and progressive disclosure patterns instead of expanding the first surface indefinitely

### Requirement: Dashboard visual system SHALL support five-route storytelling
The frontend SHALL define route-aware visual rules for `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/signals`, and `/portfolio/asset-detail/:ticker` so each route reads as a different analytical question.

#### Scenario: Route differentiation reinforces the user journey
- **WHEN** the user moves from executive state to explanation, risk, tactical review, and asset detail
- **THEN** the page layout, chart selection, and hierarchy change with the route purpose
- **THEN** executive routes remain compact while detail routes can increase analytical density

### Requirement: Dashboard visual system SHALL preserve institutional clarity over decorative styling
The frontend SHALL use restrained premium-fintech styling with semantic colors, high-contrast typography, and data-dense readability rather than decorative AI-dashboard patterns.

#### Scenario: Styling reinforces trust instead of distraction
- **WHEN** the compact dashboard renders its primary surfaces
- **THEN** accent colors remain subordinate to content and semantic state
- **THEN** typography, spacing, and numeric rhythm support dense financial reading
- **THEN** the interface avoids novelty styling that weakens clarity or age stability

### Requirement: Dashboard visual system SHALL implement a phi-derived spacing rhythm
The frontend SHALL define spacing, panel rhythm, and selected module-height tokens from a phi-derived ratio baseline (`1.613`) while preserving accessibility and readability constraints.

#### Scenario: Spacing remains harmonic across modules without harming scanability
- **WHEN** dashboard layout tokens are applied to cards, gutters, and vertical rhythm
- **THEN** spacing follows a consistent phi-derived progression
- **THEN** first-viewport compactness remains within dashboard height budgets
- **THEN** accessibility/readability rules override strict ratio application when conflicts occur

### Requirement: Dashboard visual system SHALL define explicit corner-radius families
The frontend SHALL define consistent corner tokens for dense cards and emphasis controls, including large rounded styles requested for high-emphasis chips and actions.

#### Scenario: Rounded controls remain intentional and consistent
- **WHEN** rendering dense data cards, tables, and controls
- **THEN** cards use compact radius tokens suited for information density
- **THEN** high-emphasis chips/buttons may use large rounded styles equivalent to requested `100`/`135` pill treatments
- **THEN** corner styles are not mixed arbitrarily inside the same component family

### Requirement: Dashboard visual system SHALL keep loading skeleton geometry stable
The frontend SHALL use stable skeleton geometry for primary modules so loading-to-ready transitions do not shift layout unexpectedly.

#### Scenario: Loading states preserve visual structure
- **WHEN** a module is loading or retrying
- **THEN** skeleton placeholders keep module height and internal hierarchy close to ready-state geometry
- **THEN** transition to ready/error states avoids abrupt vertical jumps

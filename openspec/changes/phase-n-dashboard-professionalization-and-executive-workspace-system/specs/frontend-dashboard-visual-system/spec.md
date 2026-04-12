## ADDED Requirements

### Requirement: Dashboard visual system SHALL define explicit panel hierarchy
The frontend SHALL provide reusable dashboard panel variants named `hero`, `standard`, and `utility`, and every first-surface module on a primary dashboard route SHALL declare one of those hierarchy levels.

#### Scenario: First-surface modules use explicit hierarchy roles
- **WHEN** a primary dashboard route renders its first scrollable surface
- **THEN** exactly one dominant insight surface is presented using the `hero` hierarchy
- **THEN** supporting visual modules use `standard` hierarchy and metadata or trust surfaces use `utility` hierarchy

### Requirement: Dashboard visual system SHALL provide lens-aware visual tokens
The frontend SHALL define route-lens visual tokens for `Overview`, `Holdings`, `Performance`, and `Cash/Transactions`, including accent, surface, border, and status semantics that preserve readability and professional contrast.

#### Scenario: Lens context is visible without overpowering content
- **WHEN** a user navigates between dashboard lenses
- **THEN** each lens presents stable visual token differences that reinforce route orientation
- **THEN** accent usage remains subordinate to content readability and does not replace semantic status colors

### Requirement: Dashboard visual system SHALL separate narrative typography from numeric rhythm
The frontend SHALL use distinct typography roles for narrative headings, UI labels, and tabular numeric content so dense financial data remains scannable without making the entire workspace feel terminal-like.

#### Scenario: Metrics remain dense and readable without flattening the interface
- **WHEN** KPI strips, tables, and analytical cards are rendered
- **THEN** numeric values use consistent alignment and tabular rhythm suitable for cross-period comparison
- **THEN** route titles, section labels, and explanatory copy use typography roles optimized for reading and hierarchy

### Requirement: Dashboard visual system SHALL define professional lifecycle-state surfaces
The frontend SHALL define reusable loading, empty, stale, unavailable, and error-state surfaces for dashboard modules, and those states SHALL include trust-oriented copy and recovery semantics without collapsing layout hierarchy.

#### Scenario: Module lifecycle states preserve structure and trust
- **WHEN** a hero or standard panel enters `loading`, `stale`, `empty`, `unavailable`, or `error`
- **THEN** the panel preserves its hierarchy and layout footprint predictably
- **THEN** the state copy communicates freshness or recovery context explicitly instead of falling back to generic placeholders

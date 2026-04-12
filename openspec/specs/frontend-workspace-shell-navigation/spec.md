# frontend-workspace-shell-navigation Specification

## Purpose
TBD - created by archiving change phase-j-portfolio-insight-workspace-and-ux-polish. Update Purpose after archive.
## Requirements
### Requirement: Portfolio workspace SHALL provide one persistent shell across analytical routes
The frontend SHALL render `Home`, `Analytics`, `Risk`, `Transactions`, `Quant/Reports`, and `Copilot` inside one persistent workspace shell so route changes do not feel like isolated applications.

#### Scenario: User navigates between workspace routes without losing shell orientation
- **WHEN** a user switches between supported portfolio workspace routes
- **THEN** the navigation frame, active-route indication, and shared workspace chrome remain stable
- **THEN** route changes do not require a separate top-level application frame to reinitialize

### Requirement: Workspace shell SHALL expose a global command palette for analytical navigation
The frontend SHALL provide one command palette that supports route jump, symbol lookup, and direct launch of approved analytical destinations.

#### Scenario: User jumps to route or symbol from one palette interaction
- **WHEN** a user opens the command palette and selects a supported route or instrument result
- **THEN** the workspace navigates directly to the selected destination
- **THEN** the resulting route preserves or applies compatible context without requiring a second search flow

### Requirement: Workspace shell SHALL preserve compatible analytical context across route transitions
The frontend SHALL carry forward compatible workspace context such as scope, selected symbol, and period across route transitions, and SHALL reset incompatible context explicitly rather than silently.

#### Scenario: Compatible context follows user into the next route
- **WHEN** a user navigates from one analytical route to another route that supports the same scope and symbol context
- **THEN** the destination route reuses that context deterministically
- **THEN** the user does not need to re-enter the same scope inputs

#### Scenario: Incompatible context is cleared explicitly
- **WHEN** a user navigates to a route that cannot honor the current scope or symbol context
- **THEN** the UI resets only the incompatible fields and communicates that reset in stable route-level copy
- **THEN** stale or hidden context is not submitted silently

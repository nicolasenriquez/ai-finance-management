## ADDED Requirements

### Requirement: Compact-route release readiness SHALL include anti-waterfall performance evidence
Release readiness SHALL include route-level evidence that compact first-viewport modules avoid serial request waterfalls on `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, and `/portfolio/signals`.

#### Scenario: Performance evidence confirms non-serial primary-module loading
- **WHEN** compact-route release validation is executed
- **THEN** evidence includes route-level loading behavior showing independent primary-module requests are not serialized
- **THEN** unresolved waterfall regressions block release readiness for the affected route

### Requirement: Compact-route release readiness SHALL reject generic first-surface unavailable copy
Release readiness SHALL fail if first-surface compact modules rely on generic `Unavailable` copy where factual state-specific messaging is required.

#### Scenario: Validation detects generic unavailable regression
- **WHEN** release validation inspects first-surface async states on compact routes
- **THEN** modules use factual loading/empty/unavailable/error copy with explicit reason context
- **THEN** generic ambiguous unavailable messaging is treated as release-readiness failure

### Requirement: Compact-route release readiness SHALL verify primary-chart container stability
Release readiness SHALL verify stable responsive container behavior for primary compact-route charts so loading-to-ready transitions do not introduce avoidable layout shift or clipping regressions.

#### Scenario: Chart-container stability is validated before release sign-off
- **WHEN** compact-route chart validation is run on supported breakpoints
- **THEN** primary chart modules preserve stable geometry and readable axis/tooltip behavior
- **THEN** clipping or unstable container regressions fail release-readiness checks

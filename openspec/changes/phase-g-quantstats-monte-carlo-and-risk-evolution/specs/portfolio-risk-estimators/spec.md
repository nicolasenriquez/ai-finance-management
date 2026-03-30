## ADDED Requirements

### Requirement: Risk estimator contracts SHALL include threshold-aware interpretation metadata
Risk estimator responses SHALL include threshold or band metadata sufficient for frontend interpretation of good/neutral/adverse ranges.

#### Scenario: Estimator payload includes interpretation threshold context
- **WHEN** risk estimators are returned successfully
- **THEN** each estimator includes interpretation metadata or band context as defined by the active contract
- **THEN** frontend clients can render contextual interpretation without hidden defaults

### Requirement: Risk contracts SHALL support timeline-context linkage for estimator interpretation
Risk responses SHALL include explicit linkage to timeline datasets where available so users can interpret current values against recent evolution.

#### Scenario: Risk response indicates timeline availability and context
- **WHEN** estimator responses are returned for supported scope and period
- **THEN** the payload includes explicit timeline-availability metadata for related estimators
- **THEN** clients can distinguish snapshot-only and timeline-backed interpretation paths

### Requirement: Mixed-unit guardrails SHALL remain explicit for risk visual interpretation
When risk datasets contain non-comparable units, contracts SHALL require unit-separated rendering guidance and SHALL prevent invalid one-axis mixed-unit comparisons.

#### Scenario: Mixed-unit payload enforces separated interpretation guidance
- **WHEN** risk payload includes estimator values with mixed units
- **THEN** the payload includes explicit guardrail metadata requiring separated visual groups
- **THEN** clients do not render a single-axis mixed-unit comparison as valid output

### Requirement: Risk estimators SHALL expose health-pillar contribution context
Risk estimator contracts SHALL include deterministic contribution context so Risk route can explain how risk metrics affect aggregate portfolio-health interpretation.

#### Scenario: Risk payload links estimators to health risk pillar signals
- **WHEN** risk estimators are returned for supported scope/period
- **THEN** payload includes per-estimator contribution direction/severity metadata for the `risk` pillar
- **THEN** clients can render a factual explanation of why risk metrics improve or penalize overall health interpretation

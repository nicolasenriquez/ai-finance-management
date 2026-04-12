## ADDED Requirements

### Requirement: News context SHALL be grounded to portfolio holdings and watch symbols
The system SHALL provide a holdings-aware news context contract that maps approved symbols to recent market context entries with explicit source metadata.

#### Scenario: Holdings-linked news context is returned
- **WHEN** a client requests portfolio news context
- **THEN** the response includes entries mapped to held or explicitly tracked symbols only
- **THEN** each entry includes symbol linkage, source metadata, and publication timestamp

#### Scenario: Symbol has no approved context entries
- **WHEN** no approved context entry is available for one requested symbol
- **THEN** that symbol is returned with explicit unavailable context metadata
- **THEN** the system does not inject unrelated or inferred symbol context

### Requirement: News summaries SHALL include evidence and uncertainty posture
The system SHALL expose concise summaries for grouped news context with explicit evidence references and uncertainty/caveat metadata.

#### Scenario: Summary generated with evidence references
- **WHEN** a summary is generated for one symbol or portfolio scope
- **THEN** the summary includes linked evidence items and summary generation timestamp
- **THEN** the output includes caveat metadata indicating possible incompleteness or latency

#### Scenario: Summary generation fails safely
- **WHEN** summarization cannot be completed due provider/runtime error
- **THEN** the endpoint returns explicit error state and factual failure reason metadata
- **THEN** raw fallback text is not presented as a completed summary

### Requirement: News context SHALL preserve non-advice boundaries
The system SHALL keep news context informational and SHALL not produce execution directives or guaranteed-outcome recommendations.

#### Scenario: User asks for trade action from news context
- **WHEN** downstream consumers request prescriptive execution conclusions from news summaries
- **THEN** the response keeps informational framing and explicit non-advice language
- **THEN** no buy/sell/execute instruction is emitted by the contract

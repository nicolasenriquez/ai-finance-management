## ADDED Requirements

### Requirement: Portfolio quant report contracts SHALL remain route-agnostic for dedicated analytical surfaces
The portfolio analytics API SHALL expose quant report generation and retrieval contracts that are consumable from any approved workspace route surface, including dedicated `Quant/Reports`, without requiring Home-specific request context.

#### Scenario: Quant report endpoints succeed without Home-route coupling
- **WHEN** a client requests quant report generation or retrieval from a dedicated analytical workflow
- **THEN** the API validates scope inputs using contract-defined request fields only
- **THEN** the API does not require Home-route-only context flags or implied UI state to process the request

### Requirement: Portfolio quant report responses SHALL expose explicit workflow metadata for promoted UX
The portfolio analytics API SHALL include explicit report workflow metadata required by promoted Quant/Reports UX, including deterministic scope identity and artifact lifecycle status.

#### Scenario: Report payload provides deterministic scope and lifecycle context
- **WHEN** a report generation or retrieval request returns successfully
- **THEN** the payload includes explicit scope identity and artifact lifecycle metadata needed for route-level rendering
- **THEN** frontend clients do not infer report state from missing fields or implicit defaults

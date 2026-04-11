## ADDED Requirements

### Requirement: Dashboard refactors SHALL start from a complete widget inventory
The frontend workflow SHALL maintain a route-scoped widget inventory before dashboard composition changes are implemented.

#### Scenario: Widget inventory captures analytical intent and overlap
- **WHEN** one dashboard route is reviewed for simplification
- **THEN** every widget is documented with visualization type, primary metric, question answered, decision enabled, and source contract
- **THEN** overlap with other widgets is recorded explicitly instead of inferred informally

### Requirement: Dashboard audit SHALL classify each widget with deterministic disposition
Each inventoried widget SHALL be labeled as `KEEP`, `MERGE`, `MOVE`, or `REMOVE` with severity and rationale.

#### Scenario: Redundant widgets are dispositioned with rationale
- **WHEN** two or more widgets answer the same analytical question
- **THEN** the audit marks one as canonical and marks duplicates as `MERGE`, `MOVE`, or `REMOVE`
- **THEN** the final disposition includes one rationale tied to business interpretation outcomes

### Requirement: Dashboard audit artifacts SHALL include UX and visualization severity findings
Audit output SHALL include heuristic and visualization findings with severity (`low`, `medium`, `high`) and impact description.

#### Scenario: Heuristic and visualization issues are tracked before implementation
- **WHEN** dashboard audit is completed for a route
- **THEN** findings include usability and visualization-fit issues with explicit severity and impact
- **THEN** high-severity findings are linked to implementation tasks before refactor completion is declared

### Requirement: Dashboard simplification SHALL publish route wireframes and lens mapping
Refactor planning SHALL publish textual wireframes that map modules to `Overview`, `Holdings`, `Performance`, and `Cash/Transactions` lenses.

#### Scenario: Route wireframes are available before module migration
- **WHEN** a route enters implementation planning for IA simplification
- **THEN** a wireframe artifact identifies primary, secondary, and deferred module groups
- **THEN** the route is mapped to one primary lens and any cross-lens modules are marked for move or collapse

# Phase J Emil Design Polish Review

| Before | After | Why |
| --- | --- | --- |
| No persistent workspace copilot launcher in shell navigation. | Added persistent launcher actions in shell nav (`Open workspace copilot`, `Open expanded copilot surface`). | High-frequency analytical workflows keep orientation and reduce route-travel overhead. |
| Copilot interaction only on dedicated route. | Added desktop docked copilot panel and mobile full-screen panel with shared session state. | Presentation now matches device class while preserving continuity of answer/evidence/limitations. |
| Route lifecycle copy authored per page without one shared tone system. | Added shared `WorkspaceStateBanner` with `loading/ready/stale/unavailable/blocked/error` copy registry. | Trust-state semantics stay consistent across routes and reduce interpretation drift. |
| KPI promotion had only route-local card placement. | Added governed KPI catalog entries with `tier`, route ownership, decision tags, and interpretation copy. | Core vs advanced layering is explicit and auditable for future route changes. |
| No deterministic follow-up affordance for copilot prompts. | Added bounded suggestion chips (`max 4`) with deterministic composer prefill and keyboard activation. | Suggestion interactions are fast, editable, and safe for frequent workflow usage. |
| No chat-level document reference attachment workflow. | Added `document_id` add/remove chips with bounded submission (`max 8`) and ingestion guidance copy. | Enables explicit context attachment without introducing raw-file upload into chat routes. |
| Desktop copilot panel collapse had no contract. | Added collapse/expand controls with preserved in-memory conversation and trust surfaces. | Reduces viewport pressure while keeping continuity and minimizing cognitive reset. |

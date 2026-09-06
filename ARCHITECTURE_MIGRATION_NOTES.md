# Architecture consolidation notes

The repository previously contained a runtime FastAPI/SQLite application plus a second staged backend/frontend architecture. This updated version makes the root application the canonical runtime and removes the duplicate staged UI/backend tree.

The integrated runtime keeps the existing KYC domain services and adds the missing target-state control plane: Supervisor, specialist workers, screening, anomaly detection, knowledge retrieval, MCP, durable execution, observability, governance metadata and monitoring.

The old staged architecture is no longer required at runtime. Its useful concepts have been integrated under the root packages documented in `TARGET_ARCHITECTURE_IMPLEMENTED.md`.

# OnboardAI Target Architecture Implementation

This version integrates the target-state architecture into the existing FastAPI/SQLite runtime without deleting the working KYC foundation.

## Runtime flow

Customer/RM -> React -> FastAPI -> Supervisor -> Outreach -> Data Intake -> Document Intelligence -> Identity + Screening -> Risk -> Anomaly -> Decision -> Human Review when required -> AI Explanation -> Monitoring.

## Added components

- `orchestration/target_graph.py`: Supervisor, shared state, deterministic routing and LangGraph integration.
- `agents/outreach.py`: Outreach worker.
- `agents/data_intake.py`: Intake validation worker.
- `agents/screening.py`: Sanctions/PEP/adverse-media worker through MCP.
- `agents/anomaly.py`: anomaly and alert worker.
- `agents/monitoring.py`: monitoring worker.
- `integrations/mcp_gateway.py`: allow-listed integration boundary.
- `knowledge/service.py`: ChromaDB knowledge service with local policy fallback.
- `observability/tracing.py`: OpenTelemetry tracing hooks.
- `services/job_queue.py`: durable SQLite-backed queue with retries/idempotency.
- `worker.py`: dedicated durable worker process.
- `services/target_persistence.py`: workflow snapshots, screening, anomaly, events and AI explanation persistence.
- `api/dashboard.py`: dashboard and agent-runtime metrics.
- `api/kyc.py`: compatibility endpoint for role-based KYC intake.

## Existing functionality preserved

Authentication/RBAC, customer/case management, OCR, Groq document extraction, deterministic identity/risk/decision logic, human review, email, evidence and audit remain in the existing runtime.

## Optional infrastructure

The code uses the target dependencies when installed. A dependency-free sequential fallback is retained so local development does not fail before `langgraph`, ChromaDB or LlamaIndex are installed. Production deployments should install the full `requirements.txt`.

## Important security note

The previous archive contained a credential-looking Groq secret. The `.env` file has deliberately been removed from this updated archive. Create a fresh `.env` from `.env.example` and use a newly rotated credential.

## Run

1. `python -m pip install -r requirements.txt`
2. Install Tesseract OCR separately.
3. Create `.env` from `.env.example`.
4. Start API: `uvicorn main:app --reload`
5. For a separate worker instead of API autostart: set `QUEUE_AUTOSTART=false` and run `python worker.py`.
6. Frontend: `cd frontend && npm install && npm run dev`

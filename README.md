# OnboardAI — Integrated Agentic KYC Platform

OnboardAI is a role-aware KYC onboarding prototype with a Supervisor/Worker architecture.

## Canonical runtime architecture

React/Vite -> FastAPI -> LangGraph Supervisor -> Outreach -> Data Intake -> Document Intelligence -> Identity + Screening -> Risk -> Anomaly & Alert -> Deterministic Decision -> Human Review when required -> Assistive AI Explanation -> Monitoring.

Supporting layers: approved knowledge retrieval (LlamaIndex/ChromaDB when installed, deterministic local fallback otherwise), MCP Tool Gateway, durable SQLite job queue, evidence/audit, OpenTelemetry hooks, and production SQLAlchemy adapter.

## Roles

- CUSTOMER: profile, own cases, document intake and progress.
- ANALYST: KYC processing and human review.
- QA: KYC processing and human review.
- ADMIN: full user/role/notification access.

## Backend

```bash
python -m pip install -r requirements.txt
# Install Tesseract OCR separately.
cp .env.example .env
uvicorn main:app --reload
```

The API starts a lightweight durable-queue worker automatically when `QUEUE_AUTOSTART=true`. For a separate worker process, set it to `false` and run:

```bash
python worker.py
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Important endpoints

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/kyc/process-upload`
- `POST /api/documents/upload`
- `POST /api/workflow/cases/{case_id}/run`
- `GET /api/workflow/jobs/{job_id}`
- `GET /api/dashboard/stats`
- `GET /api/dashboard/agents`
- `GET /api/cases/{case_id}/summary`
- `GET /api/reviews/pending`

## Target architecture components now integrated

- Supervisor/orchestrator and shared workflow state
- Nine specialist workers plus Human Review checkpoint
- Screening through MCP allow-listed gateway
- Anomaly and alert worker
- Approved knowledge layer with ChromaDB/LlamaIndex integration and fallback
- OpenTelemetry tracing hooks
- Durable SQLite-backed job queue with retries and idempotency key
- Workflow snapshots and agent event persistence
- AI explanation with deterministic fallback
- Production SQLAlchemy persistence adapter boundary
- Stronger upload magic-byte validation
- Dashboard and agent monitoring APIs/UI
- Single canonical React frontend

## Security

Never commit `.env` or real credentials. The previous source archive contained a credential-looking Groq secret, so that secret should be rotated and a fresh `.env` created from `.env.example`.

The current risk/decision rules are demonstration policy, not regulatory advice. For production KYC, replace demo screening adapters with a trusted provider, use a production database/object store, add malware scanning, rate limiting, formal migrations, secret management and policy governance.

# App.zip + OnboardAI Full Additive Merge Analysis

## Merge rule followed
App.zip is the runtime baseline. Its existing backend files were not replaced or deleted.
Every file from onboardai_role_based_groq.zip is included under `onboardai_source_additions/`.
Reusable modules that do not overwrite App.zip are also surfaced under `extensions/`.

## What App.zip already contains
- FastAPI application (`main.py`)
- SQLite database (`services/database.py`)
- APIs for customers, cases, documents, evidence, audit, reviews and workflow
- KYC agents: document, identity, risk, decision, human_review
- Existing orchestration and workflow process
- Groq client under `llm/`
- React/Vite operations dashboard

## What was added from OnboardAI
### Authentication / RBAC source
- JWT security/auth
- Register/login/profile APIs
- CUSTOMER, ANALYST, QA, ADMIN roles
- User management API and role access documentation

These files are preserved under:
`onboardai_source_additions/backend/security/`
`onboardai_source_additions/backend/api/auth.py`
`onboardai_source_additions/backend/database/`

They use SQLAlchemy, while App.zip uses sqlite3 directly. They are intentionally not substituted into App.zip's main database layer, because doing so would change the existing backend architecture.

### Additional AI capabilities
Surfaced under `extensions/additional_agents/`:
- anomaly_agent
- data_intake_agent
- monitoring_agent
- outreach_agent
- screening_agent
- common

### Integrations
Surfaced under `extensions/integrations/`:
- MCP gateway
- document verification
- screening integration

### Platform capabilities
- knowledge service
- observability/tracing
- OCR service source
- storage source
- AI explanation source
- persistence source
- dashboard/notification/health/KYC API source
- schemas
- tests
- Docker files and documentation

### Frontend
- Original App frontend remains untouched as the primary UI/process.
- The complete role-based frontend from OnboardAI is included at:
  `frontend/onboardai_role_based_ui/`
- This gives login/register, role-aware navigation, admin user management, monitoring and customer/staff views as a complete source implementation without destroying the existing dashboard.

## Existing process preserved
Customer -> Create Case -> Upload Document -> Document Agent -> Identity Agent -> Risk Agent -> Decision Agent -> Human Review when required -> Final decision.

## Why some files are staged rather than overwritten
OnboardAI uses SQLAlchemy/repository models and a different orchestrator/API contract.
Replacing App.zip's backend would violate the requirement to keep its backend and process unchanged.
The merged project therefore contains every OnboardAI file plus surfaced additions, while preserving App.zip as the runtime baseline.

## Next integration phase
To make every staged feature live in the baseline backend, add compatibility adapters:
1. SQLite users table + JWT auth adapter
2. mount auth router in existing main.py
3. connect customer user_id to existing customers/cases
4. add role guards to existing APIs
5. invoke screening/monitoring/anomaly agents from existing workflow
6. expose dashboard/notifications through baseline services
7. merge role UI components into existing React dashboard after API contracts are adapted

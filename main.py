from fastapi import FastAPI

from config.settings import settings
from fastapi.middleware.cors import CORSMiddleware
from services.database import initialize_database
from api.audit import router as audit_router
from api.auth import router as auth_router
from api.notifications import router as notifications_router
from services.auth_service import ensure_admin
from services.job_queue import start_worker
from api.customers import router as customers_router
from api.cases import router as cases_router
from api.documents import router as documents_router
from api.evidence import router as evidence_router
from api.workflow import router as workflow_router
from api.dashboard import router as dashboard_router
from api.kyc import router as kyc_router

app = FastAPI(
    title=settings.app_name,
    description="Agentic KYC Onboarding Platform",
    version="1.0.0",
)

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ==========================================
# DATABASE
# ==========================================

initialize_database()
ensure_admin()
start_worker(settings.queue_poll_seconds) if settings.queue_autostart else None


# ==========================================
# API ROUTES

app.include_router(auth_router)
app.include_router(notifications_router)
# ==========================================

app.include_router(
    customers_router
)

app.include_router(
    cases_router
)

app.include_router(
    documents_router
)

app.include_router(
    evidence_router
) 
app.include_router(
    audit_router
)
from api.reviews import (
    router as reviews_router
)
app.include_router(
    reviews_router
)
# ==========================================
# ROOT
# ==========================================

@app.get("/")
def root():

    return {
        "application": settings.app_name,
        "status": "running",
        "environment": settings.app_env,
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    } 


app.include_router(
    workflow_router
)
app.include_router(dashboard_router)
app.include_router(kyc_router)

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from security.auth import require_roles, get_current_user, can_access_case
from services.case_service import get_case
from services.job_queue import enqueue_kyc, get_job, list_jobs

router=APIRouter(prefix="/api/workflow", tags=["KYC Workflow"] )

class RunWorkflowRequest(BaseModel):
    document_id: int | None = None

@router.post("/cases/{case_id}/run")
def run_kyc_workflow(case_id:int, payload:RunWorkflowRequest|None=None, user=Depends(require_roles("ADMIN","ANALYST","QA"))):
    if not get_case(case_id): raise HTTPException(status_code=404, detail="Case not found.")
    job=enqueue_kyc(case_id, payload.document_id if payload else None)
    return {"case_id":case_id,"job_id":job["id"],"status":job["status"],"workflow_status":"QUEUED"}

@router.get("/jobs/{job_id}")
def workflow_job(job_id:int, user=Depends(get_current_user)):
    job=get_job(job_id)
    if not job: raise HTTPException(status_code=404,detail="Workflow job not found.")
    if not can_access_case(user, job["case_id"]): raise HTTPException(status_code=403,detail="You cannot access this workflow job.")
    return job

@router.get("/jobs")
def workflow_jobs(user=Depends(require_roles("ADMIN","ANALYST","QA"))):
    return list_jobs()

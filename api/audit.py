from fastapi import APIRouter, Depends, HTTPException
from security.auth import get_current_user, can_access_case

from services.audit_service import (
    get_case_audit_events,
)


router = APIRouter(
    prefix="/api/audit",
    tags=["Audit"],
)


@router.get(
    "/case/{case_id}"
)
def get_audit_for_case(
    case_id: int, user=Depends(get_current_user)
):

    if not can_access_case(user, case_id): raise HTTPException(status_code=403, detail="You cannot access this audit trail.")
    return get_case_audit_events(case_id)
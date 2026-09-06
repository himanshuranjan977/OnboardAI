from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
)

from security.auth import get_current_user, can_access_case
from services.evidence_service import (
    get_case_evidence,
    get_document_evidence,
)


router = APIRouter(
    prefix="/api/evidence",
    tags=["Evidence"],
)


@router.get(
    "/case/{case_id}"
)
def get_evidence_for_case(
    case_id: int, user=Depends(get_current_user)
):

    if not can_access_case(user, case_id): raise HTTPException(status_code=403, detail="You cannot access this case evidence.")
    return get_case_evidence(case_id)


@router.get(
    "/document/{document_id}"
)
def get_evidence_for_document(
    document_id: int, user=Depends(get_current_user)
):

    evidence = get_document_evidence(document_id)
    if evidence:
        if not can_access_case(user, evidence[0]["case_id"]): raise HTTPException(status_code=403, detail="You cannot access this evidence.")
    return evidence
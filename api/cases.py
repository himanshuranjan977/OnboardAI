from fastapi import APIRouter, HTTPException, Depends
from services.case_service import (
    get_case_timeline,
) 
from fastapi import (
    APIRouter,
    HTTPException,
)
from models.case import (
    CaseCreate,
    CaseResponse,
)
from services.case_summary_service import (
    get_case_summary,
)
from security.auth import get_current_user, require_roles, can_access_case, can_access_customer
from services.case_service import (
    create_case,
    get_case,
    get_case_by_number,
    get_customer_cases,
    get_all_cases,
    update_case_status,
)


router = APIRouter(
    prefix="/api/cases",
    tags=["KYC Cases"],
)


@router.post(
    "",
    response_model=CaseResponse
)
def create_new_case(case: CaseCreate, user=Depends(get_current_user)):

    if not can_access_customer(user, case.customer_id):
        raise HTTPException(status_code=403, detail="You cannot create a KYC case for another customer.")

    result, error = create_case(
        customer_id=case.customer_id
    )

    if error == "CUSTOMER_NOT_FOUND":

        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    return result


@router.get(
    "",
    response_model=list[CaseResponse]
)
def list_cases(user=Depends(get_current_user)):

    if user["role"] == "CUSTOMER":
        return get_customer_cases(user["customer_id"])
    return get_all_cases()


@router.get(
    "/{case_id}",
    response_model=CaseResponse
)
def get_case_by_id(case_id: int, user=Depends(get_current_user)):

    if not can_access_case(user, case_id): raise HTTPException(status_code=403, detail="You cannot access this case.")

    case = get_case(case_id)

    if case is None:

        raise HTTPException(
            status_code=404,
            detail="Case not found.",
        )

    return case


@router.get(
    "/number/{case_number}",
    response_model=CaseResponse
)
def get_case_using_number(case_number: str, user=Depends(get_current_user)):

    case = get_case_by_number(case_number)

    if case and not can_access_case(user, case["id"]): raise HTTPException(status_code=403, detail="You cannot access this case.")

    if case is None:

        raise HTTPException(
            status_code=404,
            detail="Case not found.",
        )

    return case


@router.get(
    "/customer/{customer_id}",
    response_model=list[CaseResponse]
)
def get_cases_for_customer(customer_id: int, user=Depends(get_current_user)):

    if not can_access_customer(user, customer_id): raise HTTPException(status_code=403, detail="You cannot access these cases.")
    return get_customer_cases(customer_id)


@router.get(
    "/{case_id}/timeline"
)
def case_timeline(
    case_id: int, user=Depends(get_current_user)
):

    timeline = get_case_timeline(
        case_id
    )

    return {
        "case_id":
            case_id,

        "timeline":
            timeline,
    }
@router.get(
    "/{case_id}/summary"
)
def case_summary(
    case_id: int, user=Depends(get_current_user)
):

    summary = get_case_summary(
        case_id
    )

    if summary is None:

        raise HTTPException(
            status_code=404,
            detail="Case not found.",
        )

    return summary

@router.patch(
    "/{case_id}/status",
    response_model=CaseResponse
)
def change_case_status(
    case_id: int,
    status: str,
    _user=Depends(require_roles("ADMIN", "ANALYST", "QA"))
):

    allowed_statuses = {
        "CREATED",
        "DOCUMENT_COLLECTION",
        "IN_PROGRESS",
        "HUMAN_REVIEW",
        "COMPLETED",
        "APPROVED",
        "REJECTED",
    }

    if status not in allowed_statuses:

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid case status.",
                "allowed_statuses": sorted(
                    allowed_statuses
                ),
            },
        )

    case = update_case_status(
        case_id,
        status
    )

    if case is None:

        raise HTTPException(
            status_code=404,
            detail="Case not found.",
        )

    return case
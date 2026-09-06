from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
)

from pydantic import BaseModel

from services.review_service import (
    get_pending_reviews,
    get_review,
    complete_review,
)

from services.audit_service import (
    create_audit_event,
)

from services.evidence_service import (
    create_evidence,
)

from security.auth import require_roles
from services.email_service import send_kyc_completed_email, send_kyc_decision_email
from services.customer_service import get_customer
from services.case_service import (
    update_case_status,
    get_case,
)

router = APIRouter(
    prefix="/api/reviews",
    tags=["Human Review"],
)


# ==========================================
# Request model
# ==========================================

class ReviewDecision(BaseModel):

    decision: str

    reviewer_name: str

    reviewer_comment: str | None = None


# ==========================================
# Pending reviews
# ==========================================

@router.get(
    "/pending"
)
def pending_reviews(_user=Depends(require_roles("ADMIN", "ANALYST", "QA"))):

    return get_pending_reviews()


# ==========================================
# Get one review
# ==========================================

@router.get(
    "/{review_id}"
)
def get_one_review(
    review_id: int, _user=Depends(require_roles("ADMIN", "ANALYST", "QA"))
):

    review = get_review(
        review_id
    )

    if review is None:

        raise HTTPException(
            status_code=404,
            detail="Review not found.",
        )

    return review


# ==========================================
# Complete review
# ==========================================

@router.post(
    "/{review_id}/decision"
)

def submit_review(
    review_id: int,
    payload: ReviewDecision,
    _user=Depends(require_roles("ADMIN", "ANALYST", "QA")),
):

    # ======================================
    # Validate decision
    # ======================================

    decision = (
        payload.decision
        .upper()
        .strip()
    )

    if decision not in {
        "APPROVE",
        "REJECT",
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "Decision must be "
                "APPROVE or REJECT."
            ),
        )

    # ======================================
    # Complete review
    # ======================================

    try:

        review = complete_review(

            review_id=review_id,

            decision=decision,

            reviewer_name=
                payload.reviewer_name,

            reviewer_comment=
                payload.reviewer_comment,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if review is None:

        raise HTTPException(
            status_code=404,
            detail="Review not found.",
        )

    case_id = review["case_id"]

    # ======================================
    # Verify case exists
    # ======================================

    case = get_case(
        case_id
    )

    if case is None:

        raise HTTPException(
            status_code=404,
            detail="Case not found.",
        )

    # ======================================
    # Update case status
    # ======================================

    if decision == "APPROVE":

        new_status = "APPROVED"

    else:

        new_status = "REJECTED"

    updated_case = update_case_status(

        case_id=case_id,

        status=new_status,
    )

    if updated_case and new_status in {"APPROVED", "REJECTED"}:
        customer = get_customer(case["customer_id"])
        if customer:
            send_kyc_decision_email(customer, updated_case, new_status)

    # ======================================
    # Audit
    # ======================================

    create_audit_event(

        case_id=case_id,

        agent_name=
            "human_reviewer",

        event_type=
            "HUMAN_DECISION",

        event_message=(
            f"Human reviewer selected "
            f"{decision}. "
            f"Case status changed to "
            f"{new_status}."
        ),

        event_data={

            "review_id":
                review["id"],

            "reviewer_name":
                review["reviewer_name"],

            "decision":
                decision,

            "case_status":
                new_status,

            "comment":
                review["reviewer_comment"],
        },
    )

    # ======================================
    # Evidence
    # ======================================

    create_evidence(

        case_id=case_id,

        document_id=None,

        agent_name=
            "human_reviewer",

        evidence_type=
            "HUMAN_REVIEW_DECISION",

        field_name=None,

        source="HUMAN_REVIEW",

        customer_value=None,

        document_value=None,

        result=decision,

        confidence=None,

        explanation=(
            review["reviewer_comment"]
            or
            (
                "Human reviewer "
                "submitted the decision."
            )
        ),
    )

    # Monitoring closes the target-state human-in-the-loop cycle.
    from services.database import get_connection
    c=get_connection(); c.execute("INSERT INTO agent_events(case_id,agent_name,status,duration_ms,details) VALUES(?,?,?,?,?)",(case_id,"MonitoringAgent","COMPLETED",0.0,"{\"source\":\"human_review\"}")); c.commit(); c.close()
    create_audit_event(
        case_id=case_id,
        agent_name="monitoring_agent",
        event_type="WORKFLOW_COMPLETED",
        event_message=f"Human review completed with {new_status}.",
        event_data={"review_id":review["id"],"decision":decision},
    )

    # ======================================
    # Response
    # ======================================

    return {
        "message":
            "Human review completed.",

        "review":
            review,

        "case":
            updated_case,
    }


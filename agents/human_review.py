from services.review_service import (
    create_review,
)

from services.audit_service import (
    create_audit_event,
)


def human_review_agent(state):

    print(
        "\n[HUMAN REVIEW] "
        "Creating review request..."
    )

    case_id = state.get(
        "case_id"
    )

    reason = state.get(
        "human_review_reason"
    )

    # ======================================
    # Validate case
    # ======================================

    if not case_id:

        return {
            "current_agent":
                "human_review",

            "workflow_status":
                "FAILED",

            "error":
                "Case ID is missing.",

            "requires_human_review":
                True,

            "human_review_reason":
                "Cannot create review "
                "without a case ID.",
        }

    # ======================================
    # Create review
    # ======================================

    review = create_review(
        case_id
    )

    # ======================================
    # Audit
    # ======================================

    create_audit_event(

        case_id=case_id,

        agent_name=
            "human_review",

        event_type=
            "REVIEW_CREATED",

        event_message=(
            "Human review request "
            "created."
        ),

        event_data={

            "review_id":
                review["id"],

            "reason":
                reason,
        },
    )

    print(
        "[HUMAN REVIEW] "
        f"Review #{review['id']} created."
    )

    return {

        "current_agent":
            "human_review",

        "workflow_status":
            "WAITING_FOR_HUMAN_REVIEW",

        "review_status":
            "PENDING",

        "human_review_reason":
            reason,

        "requires_human_review":
            True,
    }
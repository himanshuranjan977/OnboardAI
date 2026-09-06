def supervisor_router(state):

    workflow_status = state.get(
        "workflow_status"
    )

    review_status = state.get(
        "review_status"
    )

    requires_human_review = state.get(
        "requires_human_review",
        False
    )

    # ==================================
    # Waiting for human
    # ==================================

    if (
        workflow_status
        == "WAITING_FOR_HUMAN_REVIEW"
    ):

        return "human_review"

    # ==================================
    # Already completed review
    # ==================================

    if review_status == "COMPLETED":

        return "complete"

    # ==================================
    # Human review required
    # ==================================

    if requires_human_review:

        return "human_review"

    # ==================================
    # Document
    # ==================================

    if workflow_status in {
        "CREATED",
        "DOCUMENT_COLLECTION",
        "READY_FOR_DOCUMENT_ANALYSIS",
    }:

        return "document_agent"

    # ==================================
    # Identity
    # ==================================

    if workflow_status == "DOCUMENT_ANALYZED":

        return "identity_agent"

    # ==================================
    # Risk
    # ==================================

    if workflow_status == "IDENTITY_VERIFIED":

        return "risk_agent"

    # ==================================
    # Decision
    # ==================================

    if workflow_status == "RISK_ASSESSED":

        return "decision_agent"

    # ==================================
    # Approved
    # ==================================

    if workflow_status == "APPROVED":

        return "complete"

    # ==================================
    # Failed
    # ==================================

    if workflow_status == "FAILED":

        return "human_review"

    return "human_review"
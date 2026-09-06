from services.evidence_service import (
    create_evidence,
)

from services.audit_service import (
    create_audit_event,
)


def make_decision(
    identity_verification: dict,
    risk_assessment: dict,
):
    """
    Deterministic decision engine.

    This is a demo workflow policy and
    is not a real-world regulatory policy.
    """

    identity_status = (
        identity_verification.get(
            "identity_status"
        )
    )

    risk_level = (
        risk_assessment.get(
            "risk_level"
        )
    )

    risk_score = (
        risk_assessment.get(
            "risk_score"
        )
    )

    reasons = []

    # ======================================
    # Identity rules
    # ======================================

    if identity_status == "MISMATCH":

        return {
            "decision": "REVIEW",

            "reason": (
                "Identity information "
                "does not match customer records."
            ),

            "identity_status":
                identity_status,

            "risk_level":
                risk_level,

            "risk_score":
                risk_score,

            "decision_basis": [
                "IDENTITY_MISMATCH"
            ],
        }

    if identity_status == "REQUIRES_REVIEW":

        return {
            "decision": "REVIEW",

            "reason": (
                "Identity verification "
                "requires manual review."
            ),

            "identity_status":
                identity_status,

            "risk_level":
                risk_level,

            "risk_score":
                risk_score,

            "decision_basis": [
                "IDENTITY_REVIEW_REQUIRED"
            ],
        }

    # ======================================
    # Risk rules
    # ======================================

    if risk_level == "HIGH":

        return {
            "decision": "ESCALATE",

            "reason": (
                "Risk assessment indicates "
                "a high-risk case."
            ),

            "identity_status":
                identity_status,

            "risk_level":
                risk_level,

            "risk_score":
                risk_score,

            "decision_basis": [
                "HIGH_RISK"
            ],
        }

    if risk_level == "MEDIUM":

        return {
            "decision": "REVIEW",

            "reason": (
                "Risk assessment indicates "
                "a medium-risk case."
            ),

            "identity_status":
                identity_status,

            "risk_level":
                risk_level,

            "risk_score":
                risk_score,

            "decision_basis": [
                "MEDIUM_RISK"
            ],
        }

    # ======================================
    # Approval
    # ======================================

    if (
        identity_status == "MATCH"
        and risk_level == "LOW"
    ):

        reasons.append(
            "Identity verification matched."
        )

        reasons.append(
            "Risk level is LOW."
        )

        return {
            "decision": "APPROVE",

            "reason": (
                "Customer passed identity "
                "verification and the "
                "risk assessment."
            ),

            "identity_status":
                identity_status,

            "risk_level":
                risk_level,

            "risk_score":
                risk_score,

            "decision_basis": [
                "IDENTITY_MATCH",
                "LOW_RISK",
            ],
        }

    # ======================================
    # Safe fallback
    # ======================================

    return {
        "decision": "REVIEW",

        "reason": (
            "The case does not satisfy "
            "the automatic decision rules."
        ),

        "identity_status":
            identity_status,

        "risk_level":
            risk_level,

        "risk_score":
            risk_score,

        "decision_basis": [
            "RULES_NOT_SATISFIED"
        ],
    }


def decision_agent(state):

    print(
        "\n[DECISION AGENT] Started"
    )

    case_id = state.get(
        "case_id"
    )

    document_id = state.get(
        "document_id"
    )

    identity_verification = (
        state.get(
            "identity_verification"
        )
    )

    risk_assessment = (
        state.get(
            "risk_assessment"
        )
    )

    # ======================================
    # Validate identity
    # ======================================

    if not identity_verification:

        create_audit_event(

            case_id=case_id,

            agent_name="decision_agent",

            event_type="AGENT_FAILED",

            event_message=(
                "Decision cannot be made "
                "because identity verification "
                "is missing."
            ),
        )

        return {

            "current_agent":
                "decision_agent",

            "workflow_status":
                "FAILED",

            "requires_human_review":
                True,

            "human_review_reason":
                "Identity verification "
                "is missing.",
        }

    # ======================================
    # Validate risk
    # ======================================

    if not risk_assessment:

        create_audit_event(

            case_id=case_id,

            agent_name="decision_agent",

            event_type="AGENT_FAILED",

            event_message=(
                "Decision cannot be made "
                "because risk assessment "
                "is missing."
            ),
        )

        return {

            "current_agent":
                "decision_agent",

            "workflow_status":
                "FAILED",

            "requires_human_review":
                True,

            "human_review_reason":
                "Risk assessment "
                "is missing.",
        }

    # ======================================
    # Audit start
    # ======================================

    create_audit_event(

        case_id=case_id,

        agent_name="decision_agent",

        event_type="AGENT_STARTED",

        event_message=(
            "Final decision evaluation started."
        ),
    )

    # ======================================
    # Make decision
    # ======================================

    result = make_decision(

        identity_verification=
            identity_verification,

        risk_assessment=
            risk_assessment,
    )

    decision = result[
        "decision"
    ]

    reason = result[
        "reason"
    ]

    # ======================================
    # Store evidence
    # ======================================

    create_evidence(

        case_id=case_id,

        document_id=document_id,

        agent_name="decision_agent",

        evidence_type=
            "FINAL_DECISION",

        field_name=None,

        source="KYC_WORKFLOW",

        customer_value=None,

        document_value=None,

        result=decision,

        confidence=None,

        explanation=reason,
    )

    # ======================================
    # Audit decision
    # ======================================

    create_audit_event(

        case_id=case_id,

        agent_name="decision_agent",

        event_type="DECISION_MADE",

        event_message=(
            f"Final decision: "
            f"{decision}."
        ),

        event_data=result,
    )

    # ======================================
    # Workflow status
    # ======================================

    if decision == "APPROVE":

        workflow_status = (
            "APPROVED"
        )

        requires_review = False

        review_reason = None

    elif decision == "ESCALATE":

        workflow_status = (
            "ESCALATION_REQUIRED"
        )

        requires_review = True

        review_reason = (
            "High-risk case requires "
            "escalation."
        )

    else:

        workflow_status = (
            "HUMAN_REVIEW"
        )

        requires_review = True

        review_reason = reason

    print(
        "[DECISION AGENT] Completed"
    )

    return {

        "current_agent":
            "decision_agent",

        "workflow_status":
            workflow_status,

        "final_decision":
            result,

        "requires_human_review":
            requires_review,

        "human_review_reason":
            review_reason,
    }
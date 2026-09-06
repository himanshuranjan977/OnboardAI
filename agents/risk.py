from services.evidence_service import (
    create_evidence,
)

from services.audit_service import (
    create_audit_event,
)


def calculate_risk(
    document_analysis: dict,
    identity_verification: dict,
):
    """
    Deterministic demo risk calculation.

    This is NOT a regulatory KYC scoring model.
    It is only for demonstrating the
    multi-agent workflow.
    """

    score = 0

    risk_factors = []

    # ======================================
    # Identity
    # ======================================

    identity_status = identity_verification.get(
        "identity_status"
    )

    if identity_status == "MATCH":

        score += 0

    elif identity_status == "REQUIRES_REVIEW":

        score += 30

        risk_factors.append(
            "Identity verification requires review."
        )

    elif identity_status == "MISMATCH":

        score += 50

        risk_factors.append(
            "Identity information mismatch."
        )

    else:

        score += 60

        risk_factors.append(
            "Identity verification failed."
        )

    # ======================================
    # Document confidence
    # ======================================

    confidence = document_analysis.get(
        "confidence"
    )

    if confidence is None:

        score += 20

        risk_factors.append(
            "Document confidence unavailable."
        )

    elif confidence < 0.70:

        score += 25

        risk_factors.append(
            "Low document extraction confidence."
        )

    elif confidence < 0.85:

        score += 10

        risk_factors.append(
            "Moderate document extraction confidence."
        )

    # ======================================
    # Missing fields
    # ======================================

    missing_fields = document_analysis.get(
        "missing_fields",
        []
    )

    if missing_fields:

        missing_score = min(
            len(missing_fields) * 5,
            20
        )

        score += missing_score

        risk_factors.append(
            f"Missing fields: "
            f"{', '.join(missing_fields)}"
        )

    # ======================================
    # Warnings
    # ======================================

    warnings = document_analysis.get(
        "warnings",
        []
    )

    if warnings:

        warning_score = min(
            len(warnings) * 10,
            20
        )

        score += warning_score

        risk_factors.append(
            f"Document warnings detected: "
            f"{len(warnings)}"
        )

    # ======================================
    # Cap score
    # ======================================

    score = min(
        score,
        100
    )

    # ======================================
    # Risk level
    # ======================================

    if score <= 20:

        risk_level = "LOW"

    elif score <= 50:

        risk_level = "MEDIUM"

    else:

        risk_level = "HIGH"

    # ======================================
    # Recommendation
    # ======================================

    if risk_level == "LOW":

        recommendation = "CONTINUE"

    elif risk_level == "MEDIUM":

        recommendation = "HUMAN_REVIEW"

    else:

        recommendation = "ESCALATE"

    return {
        "risk_score": score,

        "risk_level": risk_level,

        "risk_factors": risk_factors,

        "recommendation": recommendation,
    }


def risk_agent(state):

    print(
        "\n[RISK AGENT] Started"
    )

    case_id = state.get(
        "case_id"
    )

    document_id = state.get(
        "document_id"
    )

    document_analysis = state.get(
        "document_analysis"
    )

    identity_verification = state.get(
        "identity_verification"
    )

    # ======================================
    # Validate required inputs
    # ======================================

    if not document_analysis:

        create_audit_event(

            case_id=case_id,

            agent_name="risk_agent",

            event_type="AGENT_FAILED",

            event_message=(
                "Risk assessment could not "
                "start because document "
                "analysis is missing."
            ),
        )

        return {
            "current_agent":
                "risk_agent",

            "workflow_status":
                "FAILED",

            "requires_human_review":
                True,

            "human_review_reason":
                "Risk assessment requires "
                "document analysis.",
        }

    if not identity_verification:

        create_audit_event(

            case_id=case_id,

            agent_name="risk_agent",

            event_type="AGENT_FAILED",

            event_message=(
                "Risk assessment could not "
                "start because identity "
                "verification is missing."
            ),
        )

        return {
            "current_agent":
                "risk_agent",

            "workflow_status":
                "FAILED",

            "requires_human_review":
                True,

            "human_review_reason":
                "Risk assessment requires "
                "identity verification.",
        }

    # ======================================
    # Audit start
    # ======================================

    create_audit_event(

        case_id=case_id,

        agent_name="risk_agent",

        event_type="AGENT_STARTED",

        event_message=(
            "Risk assessment started."
        ),
    )

    # ======================================
    # Calculate risk
    # ======================================

    result = calculate_risk(

        document_analysis=
            document_analysis,

        identity_verification=
            identity_verification,
    )

    risk_score = result[
        "risk_score"
    ]

    risk_level = result[
        "risk_level"
    ]

    recommendation = result[
        "recommendation"
    ]

    # ======================================
    # Store overall evidence
    # ======================================

    create_evidence(

        case_id=case_id,

        document_id=document_id,

        agent_name="risk_agent",

        evidence_type=
            "RISK_ASSESSMENT",

        field_name=None,

        source="KYC_WORKFLOW",

        customer_value=None,

        document_value=None,

        result=risk_level,

        confidence=None,

        explanation=(
            f"Deterministic risk assessment "
            f"produced a score of "
            f"{risk_score}/100."
        ),
    )

    # ======================================
    # Store individual risk factors
    # ======================================

    for factor in result[
        "risk_factors"
    ]:

        create_evidence(

            case_id=case_id,

            document_id=document_id,

            agent_name="risk_agent",

            evidence_type=
                "RISK_FACTOR",

            field_name=None,

            source="KYC_WORKFLOW",

            customer_value=None,

            document_value=None,

            result="FLAGGED",

            confidence=None,

            explanation=factor,
        )

    # ======================================
    # Determine workflow
    # ======================================

    if recommendation == "CONTINUE":

        workflow_status = (
            "RISK_ASSESSED"
        )

        requires_review = False

        review_reason = None

    elif recommendation == "HUMAN_REVIEW":

        workflow_status = (
            "HUMAN_REVIEW"
        )

        requires_review = True

        review_reason = (
            "Risk assessment requires "
            "human review."
        )

    else:

        workflow_status = (
            "ESCALATION_REQUIRED"
        )

        requires_review = True

        review_reason = (
            "High-risk case requires "
            "escalation."
        )

    # ======================================
    # Audit completion
    # ======================================

    create_audit_event(

        case_id=case_id,

        agent_name="risk_agent",

        event_type="AGENT_COMPLETED",

        event_message=(
            f"Risk assessment completed: "
            f"{risk_level} risk."
        ),

        event_data={
            "risk_score":
                risk_score,

            "risk_level":
                risk_level,

            "recommendation":
                recommendation,

            "risk_factors":
                result[
                    "risk_factors"
                ],
        },
    )

    print(
        "[RISK AGENT] Completed"
    )

    return {

        "current_agent":
            "risk_agent",

        "workflow_status":
            workflow_status,

        "risk_assessment":
            result,

        "requires_human_review":
            requires_review,

        "human_review_reason":
            review_reason,
    }
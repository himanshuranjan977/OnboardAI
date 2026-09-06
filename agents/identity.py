import re

from services.database import get_connection
from services.evidence_service import (
    create_evidence,
    
)
from services.audit_service import (
    create_audit_event,
)

def normalize_text(value: str | None) -> str:
    """
    Normalize text before comparison.
    """

    if not value:
        return ""

    value = value.lower().strip()

    # Remove punctuation
    value = re.sub(
        r"[^a-z0-9\s]",
        "",
        value
    )

    # Normalize multiple spaces
    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


def normalize_date(value: str | None) -> str:
    """
    Basic date normalization.

    This is intentionally conservative.
    We don't guess ambiguous dates.
    """

    if not value:
        return ""

    value = value.strip().lower()

    value = value.replace(
        "/",
        "-"
    )

    value = value.replace(
        ".",
        "-"
    )

    return value


def get_customer_for_identity(
    customer_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            date_of_birth,
            address
        FROM customers
        WHERE id = ?
        """,
        (customer_id,),
    )

    customer = cursor.fetchone()

    connection.close()

    if customer is None:
        return None

    return dict(customer)


def compare_field(
    field_name: str,
    customer_value: str | None,
    document_value: str | None,
):

    if not customer_value or not document_value:

        return {
            "field": field_name,
            "status": "MISSING",
            "customer_value": customer_value,
            "document_value": document_value,
        }

    if field_name == "date_of_birth":

        normalized_customer = normalize_date(
            customer_value
        )

        normalized_document = normalize_date(
            document_value
        )

    else:

        normalized_customer = normalize_text(
            customer_value
        )

        normalized_document = normalize_text(
            document_value
        )

    if normalized_customer == normalized_document:

        status = "MATCH"

    else:

        status = "MISMATCH"

    return {
        "field": field_name,
        "status": status,
        "customer_value": customer_value,
        "document_value": document_value,
    }


def verify_identity(
    customer_id: int,
    document_analysis: dict,
):

    customer = get_customer_for_identity(
        customer_id
    )

    if customer is None:

        return {
            "identity_status": "ERROR",
            "match_score": 0.0,
            "field_results": [],
            "warnings": [
                "Customer not found."
            ],
        }

    field_results = []

    # ======================================
    # NAME
    # ======================================

    field_results.append(
        compare_field(
            "name",
            customer.get("name"),
            document_analysis.get(
                "full_name"
            ),
        )
    )

    # ======================================
    # DATE OF BIRTH
    # ======================================

    field_results.append(
        compare_field(
            "date_of_birth",
            customer.get(
                "date_of_birth"
            ),
            document_analysis.get(
                "date_of_birth"
            ),
        )
    )

    # ======================================
    # ADDRESS
    # ======================================

    field_results.append(
        compare_field(
            "address",
            customer.get("address"),
            document_analysis.get(
                "address"
            ),
        )
    )

    matches = sum(
        1
        for result in field_results
        if result["status"] == "MATCH"
    )

    mismatches = sum(
        1
        for result in field_results
        if result["status"] == "MISMATCH"
    )

    missing = sum(
        1
        for result in field_results
        if result["status"] == "MISSING"
    )

    total = len(field_results)

    match_score = (
        matches / total
        if total > 0
        else 0.0
    )

    warnings = []

    # A hard mismatch in identity data
    # should not automatically approve anything.

    if mismatches > 0:

        identity_status = "MISMATCH"

        warnings.append(
            "One or more identity fields do not match."
        )

    elif missing > 0:

        identity_status = "REQUIRES_REVIEW"

        warnings.append(
            "Some identity fields could not be verified."
        )

    else:

        identity_status = "MATCH"

    return {
        "identity_status": identity_status,
        "match_score": round(
            match_score,
            2
        ),
        "field_results": field_results,
        "warnings": warnings,
    }


def identity_agent(state):

    print(
        "\n[IDENTITY AGENT] Started"
    )
    create_audit_event(

        case_id=state.get(
            "case_id"
        ),

        agent_name=
            "identity_agent",

        event_type=
            "AGENT_STARTED",

        event_message=
            "Identity verification started.",
    )

    customer_id = state.get(
        "customer_id"
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

    document_path = state.get(
        "document_path"
    )

    if not customer_id:

        return {
            "current_agent":
                "identity_agent",

            "workflow_status":
                "FAILED",

            "error":
                "Customer ID is missing.",

            "requires_human_review":
                True,

            "human_review_reason":
                "Identity verification "
                "cannot identify the customer.",
        }

    if not document_analysis:

        return {
            "current_agent":
                "identity_agent",

            "workflow_status":
                "FAILED",

            "error":
                "Document analysis is missing.",

            "requires_human_review":
                True,

            "human_review_reason":
                "Identity verification "
                "cannot proceed without "
                "document analysis.",
        }

    # ======================================
    # Perform verification
    # ======================================

    result = verify_identity(
        customer_id=customer_id,
        document_analysis=document_analysis,
    )

    identity_status = result.get(
        "identity_status"
    )

    # ======================================
    # Store evidence
    # ======================================

    field_results = result.get(
        "field_results",
        []
    )

    document_source = (
        document_path
        or "document"
    )

    for field in field_results:

        field_status = field.get(
            "status"
        )

        customer_value = field.get(
            "customer_value"
        )

        document_value = field.get(
            "document_value"
        )

        explanation = (
            f"Identity field "
            f"'{field.get('field')}' "
            f"was evaluated using "
            f"customer records and "
            f"document extraction."
        )

        create_evidence(

            case_id=case_id,

            document_id=document_id,

            agent_name=
                "identity_agent",

            evidence_type=
                "IDENTITY_FIELD_COMPARISON",

            field_name=
                field.get("field"),

            source=
                document_source,

            customer_value=
                str(customer_value)
                if customer_value is not None
                else None,

            document_value=
                str(document_value)
                if document_value is not None
                else None,

            result=
                field_status,

            confidence=
                result.get(
                    "match_score"
                ),

            explanation=
                explanation,
        )

    # ======================================
    # Store overall identity evidence
    # ======================================

    create_evidence(

        case_id=case_id,

        document_id=document_id,

        agent_name=
            "identity_agent",

        evidence_type=
            "IDENTITY_VERIFICATION",

        field_name=None,

        source=
            document_source,

        customer_value=None,

        document_value=None,

        result=
            identity_status,

        confidence=
            result.get(
                "match_score"
            ),

        explanation=(
            "Identity verification "
            "completed using deterministic "
            "field comparison."
        ),
    )

    # ======================================
    # Determine workflow
    # ======================================

    if identity_status == "MATCH":

        workflow_status = (
            "IDENTITY_VERIFIED"
        )

        requires_review = False

        review_reason = None

    elif identity_status == "MISMATCH":

        workflow_status = (
            "HUMAN_REVIEW"
        )

        requires_review = True

        review_reason = (
            "Identity information "
            "does not match customer records."
        )

    else:

        workflow_status = (
            "HUMAN_REVIEW"
        )

        requires_review = True

        review_reason = (
            "Identity verification "
            "requires manual review."
        )

    print(
        "[IDENTITY AGENT] Completed"
    )
    create_audit_event(

        case_id=case_id,

        agent_name=
            "identity_agent",

        event_type=
            "AGENT_COMPLETED",

        event_message=(
            "Identity verification "
            f"completed with status "
            f"{identity_status}."
        ),

        event_data={

            "identity_status":
                identity_status,

            "match_score":
                result.get(
                    "match_score"
                ),
        },
    )
    return {

        "current_agent":
            "identity_agent",

        "workflow_status":
            workflow_status,

        "identity_verification":
            result,

        "requires_human_review":
            requires_review,

        "human_review_reason":
            review_reason,
    }
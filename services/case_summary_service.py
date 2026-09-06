from services.database import get_connection
import json
from services.target_persistence import latest_screening, latest_anomaly


def get_case_summary(case_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    # ==========================================
    # CASE
    # ==========================================

    cursor.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    )

    case_row = cursor.fetchone()

    if case_row is None:

        connection.close()

        return None

    case = dict(case_row)

    # ==========================================
    # CUSTOMER
    # ==========================================

    customer = None

    customer_id = case.get(
        "customer_id"
    )

    if customer_id:

        cursor.execute(
            """
            SELECT *
            FROM customers
            WHERE id = ?
            """,
            (customer_id,),
        )

        customer_row = cursor.fetchone()

        if customer_row:

            customer = dict(
                customer_row
            )

    # ==========================================
    # DOCUMENTS
    # ==========================================

    cursor.execute(
        """
        SELECT *
        FROM documents
        WHERE case_id = ?
        ORDER BY id ASC
        """,
        (case_id,),
    )

    document_rows = cursor.fetchall()

    documents = [
        dict(row)
        for row in document_rows
    ]

    # ==========================================
    # EVIDENCE
    # ==========================================

    cursor.execute(
        """
        SELECT *
        FROM evidence
        WHERE case_id = ?
        ORDER BY id ASC
        """,
        (case_id,),
    )

    evidence_rows = cursor.fetchall()

    evidence = [
        dict(row)
        for row in evidence_rows
    ]

    # ==========================================
    # AUDIT
    # ==========================================

    cursor.execute(
        """
        SELECT *
        FROM audit_events
        WHERE case_id = ?
        ORDER BY id ASC
        """,
        (case_id,),
    )

    audit_rows = cursor.fetchall()

    audit = [
        dict(row)
        for row in audit_rows
    ]

    # ==========================================
    # HUMAN REVIEWS
    # ==========================================

    cursor.execute(
        """
        SELECT *
        FROM human_reviews
        WHERE case_id = ?
        ORDER BY id ASC
        """,
        (case_id,),
    )

    review_rows = cursor.fetchall()

    reviews = [
        dict(row)
        for row in review_rows
    ]

    # ==========================================
    # Latest human review
    # ==========================================

    human_review = None

    if reviews:

        human_review = reviews[-1]

    # ==========================================
    # Extract agent results from evidence
    # ==========================================

    identity = None

    risk = None

    decision = None

    for item in evidence:

        evidence_type = item.get(
            "evidence_type"
        )

        if evidence_type == "IDENTITY_VERIFICATION":

            identity = item

        elif evidence_type == "RISK_ASSESSMENT":

            risk = item

        elif evidence_type in {"DECISION", "FINAL_DECISION"}:

            decision = item

    # ==========================================
    # Timeline
    # ==========================================

    timeline = []

    for item in audit:

        timeline.append(
            {
                "type": "AUDIT",

                "title":
                    item.get(
                        "event_type"
                    ),

                "description":
                    item.get(
                        "event_message"
                    ),

                "agent":
                    item.get(
                        "agent_name"
                    ),

                "timestamp":
                    item.get(
                        "created_at"
                    ),
            }
        )

    for review in reviews:

        timeline.append(
            {
                "type":
                    "HUMAN_REVIEW",

                "title":
                    "Human Review",

                "description":
                    (
                        review.get(
                            "reviewer_comment"
                        )
                        or
                        "Human review created."
                    ),

                "review_id":
                    review.get("id"),

                "status":
                    review.get("status"),

                "decision":
                    review.get("decision"),

                "reviewer":
                    review.get(
                        "reviewer_name"
                    ),

                "timestamp":
                    review.get(
                        "updated_at"
                    ),
            }
        )

    timeline.sort(
        key=lambda item:
            item.get("timestamp")
            or ""
    )

    connection.close()

    screening = latest_screening(case_id)
    anomaly = latest_anomaly(case_id)
    c2 = get_connection()
    agent_rows = c2.execute("SELECT * FROM agent_events WHERE case_id=? ORDER BY id ASC", (case_id,)).fetchall()
    explanation_row = c2.execute("SELECT * FROM ai_explanations WHERE case_id=?", (case_id,)).fetchone()
    job_row = c2.execute("SELECT * FROM workflow_jobs WHERE case_id=? ORDER BY id DESC LIMIT 1", (case_id,)).fetchone()
    c2.close()
    agent_events = [dict(r) for r in agent_rows]
    explanation = dict(explanation_row) if explanation_row else None
    workflow_job = dict(job_row) if job_row else None

    # ==========================================
    # Frontend status
    # ==========================================

    status = case.get(
        "status",
        "UNKNOWN"
    )

    if status == "APPROVED":

        status_label = "Approved"

    elif status == "REJECTED":

        status_label = "Rejected"

    elif status == "WAITING_FOR_HUMAN_REVIEW":

        status_label = "Waiting for Human Review"

    elif status == "FAILED":

        status_label = "Failed"

    else:

        status_label = status.replace(
            "_",
            " "
        ).title()

    # ==========================================
    # FINAL RESPONSE
    # ==========================================

    return {

        "case": case,

        "customer": customer,

        "documents": documents,

        "identity": identity,

        "risk": risk,

        "screening": screening,

        "anomaly": anomaly,

        "decision": decision,

        "human_review":
            human_review,

        "evidence": evidence,

        "audit": audit,

        "agent_events": agent_events,

        "ai_explanation": explanation,

        "workflow_job": workflow_job,

        "timeline": timeline,

        "ui": {

            "status":
                status,

            "status_label":
                status_label,

            "requires_human_review":
                status
                in {"WAITING_FOR_HUMAN_REVIEW", "HUMAN_REVIEW"},

            "has_human_review":
                human_review is not None,

            "review_completed":
                (
                    human_review is not None
                    and
                    human_review.get(
                        "status"
                    )
                    == "COMPLETED"
                ),
        },
    }
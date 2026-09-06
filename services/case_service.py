import uuid

from services.database import get_connection


def generate_case_number():

    unique_id = uuid.uuid4().hex[:8].upper()

    return f"CASE-{unique_id}"


def create_case(customer_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    # Check customer exists
    cursor.execute(
        """
        SELECT id
        FROM customers
        WHERE id = ?
        """,
        (customer_id,),
    )

    customer = cursor.fetchone()

    if customer is None:

        connection.close()

        return None, "CUSTOMER_NOT_FOUND"

    case_number = generate_case_number()

    cursor.execute(
        """
        INSERT INTO cases
        (
            case_number,
            customer_id,
            status
        )
        VALUES (?, ?, ?)
        """,
        (
            case_number,
            customer_id,
            "CREATED",
        ),
    )

    connection.commit()

    case_id = cursor.lastrowid

    cursor.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    )

    case = cursor.fetchone()

    connection.close()

    return dict(case), None


def get_case(case_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    )

    case = cursor.fetchone()

    connection.close()

    if case is None:
        return None

    return dict(case)


def get_case_by_number(case_number: str):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM cases
        WHERE case_number = ?
        """,
        (case_number,),
    )

    case = cursor.fetchone()

    connection.close()

    if case is None:
        return None

    return dict(case)


def get_customer_cases(customer_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM cases
        WHERE customer_id = ?
        ORDER BY id DESC
        """,
        (customer_id,),
    )

    cases = cursor.fetchall()

    connection.close()

    return [dict(case) for case in cases]


def get_all_cases():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM cases
        ORDER BY id DESC
        """
    )

    cases = cursor.fetchall()

    connection.close()

    return [dict(case) for case in cases]


def update_case_status(
    case_id: int,
    status: str
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE cases
        SET
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            status,
            case_id,
        ),
    )

    connection.commit()

    cursor.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    )

    case = cursor.fetchone()

    connection.close()

    if case is None:
        return None

    return dict(case) 

def get_case_timeline(
    case_id: int,
):

    connection = get_connection()

    cursor = connection.cursor()

    timeline = []

    # ======================================
    # Audit events
    # ======================================

    cursor.execute(
        """
        SELECT
            id,
            case_id,
            agent_name,
            event_type,
            event_message,
            created_at
        FROM audit_events
        WHERE case_id = ?
        ORDER BY created_at ASC, id ASC
        """,
        (case_id,),
    )

    audit_events = cursor.fetchall()

    for event in audit_events:

        timeline.append(
            {
                "type": "AUDIT",

                "title":
                    event["event_type"],

                "description":
                    event["event_message"],

                "agent":
                    event["agent_name"],

                "timestamp":
                    event["created_at"],
            }
        )

    # ======================================
    # Human reviews
    # ======================================

    cursor.execute(
        """
        SELECT
            id,
            case_id,
            status,
            decision,
            reviewer_name,
            reviewer_comment,
            created_at,
            updated_at
        FROM human_reviews
        WHERE case_id = ?
        ORDER BY created_at ASC, id ASC
        """,
        (case_id,),
    )

    reviews = cursor.fetchall()

    for review in reviews:

        timeline.append(
            {
                "type": "HUMAN_REVIEW",

                "title":
                    "Human review",

                "description":
                    (
                        review["reviewer_comment"]
                        or
                        "Human review created."
                    ),

                "review_id":
                    review["id"],

                "status":
                    review["status"],

                "decision":
                    review["decision"],

                "reviewer":
                    review["reviewer_name"],

                "timestamp":
                    review["updated_at"],
            }
        )

    # ======================================
    # Sort timeline
    # ======================================

    timeline.sort(
        key=lambda item:
            item["timestamp"]
            or ""
    )

    connection.close()

    return timeline
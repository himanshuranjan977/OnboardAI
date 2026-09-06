from services.database import (
    get_connection,
)


VALID_DECISIONS = {
    "APPROVE",
    "REJECT",
}


def create_review(
    case_id: int,
):
    """
    Create a pending human review.
    """

    connection = get_connection()

    cursor = connection.cursor()

    # Check if a pending review already exists.

    cursor.execute(
        """
        SELECT *
        FROM human_reviews
        WHERE case_id = ?
        AND status = 'PENDING'
        ORDER BY id DESC
        LIMIT 1
        """,
        (case_id,),
    )

    existing = cursor.fetchone()

    if existing:

        connection.close()

        return dict(existing)

    cursor.execute(
        """
        INSERT INTO human_reviews
        (
            case_id,
            status
        )
        VALUES (?, ?)
        """,
        (
            case_id,
            "PENDING",
        ),
    )

    connection.commit()

    review_id = cursor.lastrowid

    cursor.execute(
        """
        SELECT *
        FROM human_reviews
        WHERE id = ?
        """,
        (review_id,),
    )

    review = cursor.fetchone()

    connection.close()

    return dict(review)


def get_pending_reviews():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM human_reviews
        WHERE status = 'PENDING'
        ORDER BY created_at ASC
        """
    )

    reviews = cursor.fetchall()

    connection.close()

    return [
        dict(review)
        for review in reviews
    ]


def get_review(
    review_id: int,
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM human_reviews
        WHERE id = ?
        """,
        (review_id,),
    )

    review = cursor.fetchone()

    connection.close()

    if review is None:

        return None

    return dict(review)


def complete_review(
    review_id: int,
    decision: str,
    reviewer_name: str,
    reviewer_comment: str | None = None,
):

    decision = decision.upper().strip()

    if decision not in VALID_DECISIONS:

        raise ValueError(
            "Invalid review decision. "
            "Use APPROVE or REJECT."
        )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM human_reviews
        WHERE id = ?
        """,
        (review_id,),
    )

    review = cursor.fetchone()

    if review is None:

        connection.close()

        return None

    if review["status"] != "PENDING":

        connection.close()

        raise ValueError(
            "This review is already completed."
        )

    cursor.execute(
        """
        UPDATE human_reviews

        SET
            status = ?,
            decision = ?,
            reviewer_name = ?,
            reviewer_comment = ?,
            updated_at = CURRENT_TIMESTAMP

        WHERE id = ?
        """,
        (
            "COMPLETED",
            decision,
            reviewer_name,
            reviewer_comment,
            review_id,
        ),
    )

    connection.commit()

    cursor.execute(
        """
        SELECT *
        FROM human_reviews
        WHERE id = ?
        """,
        (review_id,),
    )

    updated_review = cursor.fetchone()

    connection.close()

    return dict(updated_review)
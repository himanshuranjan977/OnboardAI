from services.database import get_connection


def create_evidence(
    case_id: int,
    document_id: int | None,
    agent_name: str,
    evidence_type: str,
    field_name: str | None,
    source: str | None,
    customer_value: str | None,
    document_value: str | None,
    result: str | None,
    confidence: float | None,
    explanation: str | None,
):
    """
    Store one piece of evidence.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO evidence
        (
            case_id,
            document_id,
            agent_name,
            evidence_type,
            field_name,
            source,
            customer_value,
            document_value,
            result,
            confidence,
            explanation
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_id,
            document_id,
            agent_name,
            evidence_type,
            field_name,
            source,
            customer_value,
            document_value,
            result,
            confidence,
            explanation,
        ),
    )

    connection.commit()

    evidence_id = cursor.lastrowid

    cursor.execute(
        """
        SELECT *
        FROM evidence
        WHERE id = ?
        """,
        (evidence_id,),
    )

    evidence = cursor.fetchone()

    connection.close()

    return dict(evidence)


def get_case_evidence(
    case_id: int
):
    """
    Return all evidence for a KYC case.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM evidence
        WHERE case_id = ?
        ORDER BY id ASC
        """,
        (case_id,),
    )

    evidence = cursor.fetchall()

    connection.close()

    return [
        dict(item)
        for item in evidence
    ]


def get_document_evidence(
    document_id: int
):
    """
    Return evidence related to a document.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM evidence
        WHERE document_id = ?
        ORDER BY id ASC
        """,
        (document_id,),
    )

    evidence = cursor.fetchall()

    connection.close()

    return [
        dict(item)
        for item in evidence
    ]
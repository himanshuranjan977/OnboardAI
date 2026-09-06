from services.database import get_connection


def create_document(
    case_id: int,
    document_type: str,
    file_name: str,
    file_path: str,
    mime_type: str | None,
):

    connection = get_connection()

    cursor = connection.cursor()

    # Check that the case exists
    cursor.execute(
        """
        SELECT id
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    )

    case = cursor.fetchone()

    if case is None:

        connection.close()

        return None, "CASE_NOT_FOUND"

    cursor.execute(
        """
        INSERT INTO documents
        (
            case_id,
            document_type,
            file_name,
            file_path,
            mime_type,
            status,
            extraction_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_id,
            document_type,
            file_name,
            file_path,
            mime_type,
            "UPLOADED",
            "PENDING",
        ),
    )

    connection.commit()

    document_id = cursor.lastrowid

    cursor.execute(
        """
        SELECT *
        FROM documents
        WHERE id = ?
        """,
        (document_id,),
    )

    document = cursor.fetchone()

    connection.close()

    return dict(document), None


def get_document(document_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM documents
        WHERE id = ?
        """,
        (document_id,),
    )

    document = cursor.fetchone()

    connection.close()

    if document is None:
        return None

    return dict(document)


def get_case_documents(case_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM documents
        WHERE case_id = ?
        ORDER BY id DESC
        """,
        (case_id,),
    )

    documents = cursor.fetchall()

    connection.close()

    return [
        dict(document)
        for document in documents
    ]


def update_document_status(
    document_id: int,
    status: str,
    extraction_status: str | None = None,
):

    connection = get_connection()

    cursor = connection.cursor()

    if extraction_status is None:

        cursor.execute(
            """
            UPDATE documents
            SET
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                status,
                document_id,
            ),
        )

    else:

        cursor.execute(
            """
            UPDATE documents
            SET
                status = ?,
                extraction_status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                status,
                extraction_status,
                document_id,
            ),
        )

    connection.commit()

    cursor.execute(
        """
        SELECT *
        FROM documents
        WHERE id = ?
        """,
        (document_id,),
    )

    document = cursor.fetchone()

    connection.close()

    if document is None:
        return None

    return dict(document)

def update_document_extraction(document_id: int, extracted_data: str, confidence: float | None = None, status: str = "PROCESSING"):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE documents SET extracted_data = ?, confidence = ?, extraction_status = ?,
        updated_at = CURRENT_TIMESTAMP WHERE id = ?
    """, (extracted_data, confidence, status, document_id))
    connection.commit()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None

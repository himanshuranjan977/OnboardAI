import json

from services.database import (
    get_connection,
)


def create_audit_event(
    case_id: int,
    event_type: str,
    event_message: str,
    agent_name: str | None = None,
    event_data: dict | None = None,
):

    connection = get_connection()

    cursor = connection.cursor()

    serialized_data = None

    if event_data is not None:

        serialized_data = json.dumps(
            event_data,
            default=str
        )

    cursor.execute(
        """
        INSERT INTO audit_events
        (
            case_id,
            agent_name,
            event_type,
            event_message,
            event_data
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            case_id,
            agent_name,
            event_type,
            event_message,
            serialized_data,
        ),
    )

    connection.commit()

    event_id = cursor.lastrowid

    cursor.execute(
        """
        SELECT *
        FROM audit_events
        WHERE id = ?
        """,
        (event_id,),
    )

    event = cursor.fetchone()

    connection.close()

    return dict(event)


def get_case_audit_events(
    case_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM audit_events
        WHERE case_id = ?
        ORDER BY id ASC
        """,
        (case_id,),
    )

    events = cursor.fetchall()

    connection.close()

    return [
        dict(event)
        for event in events
    ]
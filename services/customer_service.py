from services.database import get_connection


def create_customer(
    name: str,
    email: str,
    phone: str | None,
    date_of_birth: str | None,
    address: str | None,
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO customers
        (
            name,
            email,
            phone,
            date_of_birth,
            address
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            name,
            email,
            phone,
            date_of_birth,
            address,
        ),
    )

    connection.commit()

    customer_id = cursor.lastrowid

    cursor.execute(
        """
        SELECT *
        FROM customers
        WHERE id = ?
        """,
        (customer_id,),
    )

    customer = cursor.fetchone()

    connection.close()

    return dict(customer)


def get_customer(customer_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
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


def get_all_customers():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM customers
        ORDER BY id DESC
        """
    )

    customers = cursor.fetchall()

    connection.close()

    return [dict(customer) for customer in customers]
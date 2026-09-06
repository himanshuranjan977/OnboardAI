from fastapi import APIRouter, HTTPException, Depends
from security.auth import get_current_user, require_roles

from models.customer import (
    CustomerCreate,
    CustomerResponse,
)

from services.email_service import send_registration_success_email
from services.customer_service import (
    create_customer,
    get_customer,
    get_all_customers,
)


router = APIRouter(
    prefix="/api/customers",
    tags=["Customers"],
)


@router.post(
    "",
    response_model=CustomerResponse
)
def create_new_customer(customer: CustomerCreate, _user=Depends(require_roles("ADMIN", "ANALYST", "QA"))):

    try:

        created = create_customer(
            name=customer.name,
            email=customer.email,
            phone=customer.phone,
            date_of_birth=customer.date_of_birth,
            address=customer.address,
        )

        # Notification is best-effort and never blocks successful registration.
        send_registration_success_email(created)
        return created

    except Exception as error:

        if "UNIQUE constraint failed" in str(error):

            raise HTTPException(
                status_code=409,
                detail="Customer with this email already exists.",
            )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@router.get(
    "",
    response_model=list[CustomerResponse]
)
def list_customers(user=Depends(get_current_user)):

    if user["role"] == "CUSTOMER":
        customer = get_customer(user["customer_id"]) if user.get("customer_id") else None
        return [customer] if customer else []
    return get_all_customers()


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse
)
def get_customer_by_id(customer_id: int, user=Depends(get_current_user)):

    if user["role"] == "CUSTOMER" and user.get("customer_id") != customer_id:
        raise HTTPException(status_code=403, detail="You can only access your own customer profile.")

    customer = get_customer(customer_id)

    if customer is None:

        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    return customer
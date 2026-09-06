from pydantic import BaseModel, EmailStr
from typing import Optional


class CustomerCreate(BaseModel):

    name: str

    email: EmailStr

    phone: Optional[str] = None

    date_of_birth: Optional[str] = None

    address: Optional[str] = None


class CustomerResponse(BaseModel):

    id: int

    name: str

    email: str

    phone: Optional[str] = None

    date_of_birth: Optional[str] = None

    address: Optional[str] = None

    created_at: str
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class CustomerInput(BaseModel):
    customer_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    date_of_birth: Optional[str] = None

class DocumentInput(BaseModel):
    document_type: str = Field(default="UNKNOWN", max_length=50)
    file_name: str = Field(default="document", max_length=255)
    ocr_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    classification_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    fields: Dict[str, Any] = Field(default_factory=dict)

class KYCProcessRequest(BaseModel):
    customer: CustomerInput
    document: DocumentInput

class ReviewDecision(BaseModel):
    decision: str
    comment: str = ""

class AssignRequest(BaseModel):
    analyst_id: str = Field(min_length=1, max_length=100)

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=5, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    date_of_birth: Optional[str] = None
    address: Optional[str] = Field(default=None, max_length=1000)

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    email: Optional[str] = Field(default=None, min_length=5, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    date_of_birth: Optional[str] = None
    address: Optional[str] = Field(default=None, max_length=1000)

class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    active: Optional[bool] = None

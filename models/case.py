from pydantic import BaseModel
from typing import Optional


class CaseCreate(BaseModel):
    customer_id: int


class CaseResponse(BaseModel):
    id: int
    case_number: str
    customer_id: int
    status: str
    risk_level: Optional[str] = None
    risk_score: Optional[int] = None
    decision: Optional[str] = None
    created_at: str
    updated_at: str
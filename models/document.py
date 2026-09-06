from pydantic import BaseModel
from typing import Optional


class DocumentResponse(BaseModel):

    id: int

    case_id: int

    document_type: str

    file_name: str

    file_path: str

    mime_type: Optional[str] = None

    status: str

    extraction_status: str

    confidence: Optional[float] = None

    extracted_data: Optional[str] = None

    created_at: str

    updated_at: str
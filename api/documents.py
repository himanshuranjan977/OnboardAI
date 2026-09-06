from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    Depends,
)
from fastapi.responses import FileResponse

from models.document import DocumentResponse

from security.auth import get_current_user, require_roles, can_access_case
from services.document_service import (
    create_document,
    get_document,
    get_case_documents,
    update_document_status,
)
from services.ocr_service import extract_text
from services.document_service import update_document_extraction
from services.case_service import update_case_status
from services.audit_service import create_audit_event
from services.email_service import send_email
from agents.document import document_agent
import json


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)


UPLOAD_DIRECTORY = Path("uploads")


ALLOWED_DOCUMENT_TYPES = {
    "passport",
    "national_id",
    "driving_license",
    "address_proof",
    "bank_statement",
}


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


@router.post(
    "/upload",
    response_model=DocumentResponse
)
async def upload_document(
    case_id: int = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):

    if not can_access_case(user, case_id):
        raise HTTPException(status_code=403, detail="You cannot upload documents to this case.")

    # ==========================================
    # Validate document type
    # ==========================================

    document_type = document_type.lower().strip()

    if document_type not in ALLOWED_DOCUMENT_TYPES:

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported document type.",
                "allowed_types": sorted(
                    ALLOWED_DOCUMENT_TYPES
                ),
            },
        )

    # ==========================================
    # Validate file extension
    # ==========================================

    original_file_name = file.filename or ""

    extension = Path(
        original_file_name
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported file format.",
                "allowed_extensions": sorted(
                    ALLOWED_EXTENSIONS
                ),
            },
        )

    # ==========================================
    # Create case upload directory
    # ==========================================

    case_directory = (
        UPLOAD_DIRECTORY / f"case_{case_id}"
    )

    case_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    # ==========================================
    # Generate safe file name
    # ==========================================

    import uuid

    safe_file_name = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    file_path = (
        case_directory / safe_file_name
    )

    # ==========================================
    # Save file
    # ==========================================

    file_content = await file.read()
    if not file_content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(file_content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Document is too large. Maximum size is 15 MB.")
    from services.file_security import validate_signature
    if not validate_signature(extension, file_content):
        raise HTTPException(status_code=400, detail="File signature does not match the selected file type.")

    with open(file_path, "wb") as output_file:

        output_file.write(file_content)

    # ==========================================
    # Store metadata in database
    # ==========================================

    document, error = create_document(
        case_id=case_id,
        document_type=document_type,
        file_name=original_file_name,
        file_path=str(file_path),
        mime_type=file.content_type,
    )

    if error == "CASE_NOT_FOUND":

        # Remove file if case doesn't exist
        file_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=404,
            detail="Case not found.",
        )

    # Notify immediately after the upload is safely stored. OCR/KYC runs in the background.
    from services.customer_service import get_customer
    from services.case_service import get_case
    from services.email_service import send_document_received_email
    customer = get_customer(get_case(case_id)["customer_id"]) if get_case(case_id) else None
    if customer:
        send_document_received_email(customer, get_case(case_id), document)

    # Start OCR + KYC automatically after a customer upload. This keeps the customer out of the staff-only workflow endpoint.
    from services.job_queue import enqueue_kyc
    enqueue_kyc(case_id, document["id"])
    return document


@router.get(
    "/{document_id}",
    response_model=DocumentResponse
)
def get_document_by_id(
    document_id: int, user=Depends(get_current_user)
):

    document = get_document(
        document_id
    )

    if document is None:

        raise HTTPException(status_code=404, detail="Document not found.")
    if not can_access_case(user, document["case_id"]): raise HTTPException(status_code=403, detail="You cannot access this document.")
    return document


@router.get("/{document_id}/file")
def download_document_file(document_id: int, user=Depends(get_current_user)):
    document = get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not can_access_case(user, document["case_id"]):
        raise HTTPException(status_code=403, detail="You cannot access this document.")
    path = Path(document["file_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Original uploaded file is no longer available.")
    return FileResponse(path=str(path), filename=document["file_name"], media_type=document.get("mime_type") or "application/octet-stream")


@router.get(
    "/case/{case_id}",
    response_model=list[DocumentResponse]
)
def get_documents_for_case(
    case_id: int, user=Depends(get_current_user)
):

    if not can_access_case(user, case_id): raise HTTPException(status_code=403, detail="You cannot access these documents.")
    return get_case_documents(case_id)


@router.patch(
    "/{document_id}/status",
    response_model=DocumentResponse
)
def change_document_status(
    document_id: int,
    status: str,
    extraction_status: str | None = None,
    _user=Depends(require_roles("ADMIN", "ANALYST", "QA")),
):

    allowed_statuses = {
        "UPLOADED",
        "PROCESSING",
        "VERIFIED",
        "REJECTED",
        "REQUIRES_REVIEW",
    }

    allowed_extraction_statuses = {
        "PENDING",
        "PROCESSING",
        "COMPLETED",
        "FAILED",
    }

    if status not in allowed_statuses:

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid document status.",
                "allowed_statuses": sorted(
                    allowed_statuses
                ),
            },
        )

    if (
        extraction_status is not None
        and extraction_status
        not in allowed_extraction_statuses
    ):

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid extraction status.",
                "allowed_statuses": sorted(
                    allowed_extraction_statuses
                ),
            },
        )

    document = update_document_status(
        document_id=document_id,
        status=status,
        extraction_status=extraction_status,
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return document
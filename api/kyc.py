from pathlib import Path
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from security.auth import get_current_user, can_access_customer
from services.customer_service import create_customer, get_customer
from services.case_service import create_case
from services.document_service import create_document
from services.job_queue import enqueue_kyc

router=APIRouter(prefix="/api/kyc",tags=["KYC Compatibility"])
ALLOWED={".pdf",".png",".jpg",".jpeg",".webp",".tif",".tiff"}

@router.post("/process-upload")
async def process_upload(name:str=Form(...),date_of_birth:str=Form(""),document_type:str=Form(...),file:UploadFile=File(...),demo_sanctions_status:str=Form("CLEAR"),demo_pep_status:str=Form("CLEAR"),user=Depends(get_current_user)):
    if user["role"]=="CUSTOMER":
        customer_id=user.get("customer_id")
        if not customer_id: raise HTTPException(400,"Customer profile is not linked.")
        customer=get_customer(customer_id)
    else:
        # Staff demo path: create a customer record from the submitted identity fields.
        email=f"case-{uuid.uuid4().hex[:10]}@example.local"
        customer=create_customer(name=name,email=email,phone=None,date_of_birth=date_of_birth or None,address=None)
        customer_id=customer["id"]
    case,err=create_case(customer_id)
    if err: raise HTTPException(400,err)
    ext=Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED: raise HTTPException(400,"Unsupported file format")
    content=await file.read()
    if not content: raise HTTPException(400,"Empty document")
    from services.file_security import validate_signature
    if not validate_signature(ext, content): raise HTTPException(400,"File signature does not match the selected file type.")
    folder=Path("uploads")/f"case_{case['id']}"; folder.mkdir(parents=True,exist_ok=True)
    path=folder/f"{uuid.uuid4().hex}{ext}"; path.write_bytes(content)
    document,err=create_document(case["id"],document_type.lower(),file.filename or path.name,str(path),file.content_type)
    if err: path.unlink(missing_ok=True); raise HTTPException(400,err)
    # Demo screening controls are stored in the document metadata for the screening adapter.
    import json
    document["demo_sanctions_status"]=demo_sanctions_status; document["demo_pep_status"]=demo_pep_status
    # Persist the demo controls in extracted_data so the adapter can consume them.
    from services.document_service import update_document_extraction
    update_document_extraction(document["id"],json.dumps({"demo_sanctions_status":demo_sanctions_status,"demo_pep_status":demo_pep_status}),None,"PENDING")
    job=enqueue_kyc(case["id"],document["id"])
    return {"case_id":case["id"],"case_number":case["case_number"],"document_id":document["id"],"job_id":job["id"],"status":"QUEUED"}

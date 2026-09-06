from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from security.auth import require_roles
from services.email_service import get_email_notifications, send_email

router=APIRouter(prefix="/api/notifications", tags=["Notifications"])

class TestEmailRequest(BaseModel):
    recipient: EmailStr

@router.get("/emails")
def email_notifications(_user=Depends(require_roles("ADMIN", "ANALYST", "QA"))):
    return get_email_notifications()

@router.post("/test-email")
def test_email(payload: TestEmailRequest, _user=Depends(require_roles("ADMIN"))):
    ok=send_email(str(payload.recipient), "OnboardAI - SMTP Test", "This is a test email from OnboardAI. If you received it, SMTP email delivery is working.", notification_type="SMTP_TEST")
    if not ok:
        raise HTTPException(status_code=502, detail="SMTP test failed. Open Email Notifications for the recorded delivery error.")
    return {"status":"SENT", "recipient":str(payload.recipient)}

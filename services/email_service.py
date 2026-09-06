"""OnboardAI LLM-generated email notifications and delivery audit log."""

import logging
import os
import re
import smtplib
from datetime import datetime
from pathlib import Path
from email.message import EmailMessage

from dotenv import load_dotenv
from services.database import get_connection


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)


def _value(name, default=""):
    value = os.getenv(name, default) or default
    return value.strip().strip('"').strip("'")


def _enabled():
    return _value("EMAIL_ENABLED", "false").lower() in {
        "1", "true", "yes", "on"
    }


def _smtp_password():
    password = _value("SMTP_PASSWORD")

    # Gmail App Passwords can be copied with spaces.
    if _value("SMTP_HOST").lower() == "smtp.gmail.com":
        password = re.sub(r"\s+", "", password)

    return password


def _customer_ref(customer_id):
    try:
        return f"CUST-{int(customer_id):06d}"
    except Exception:
        return f"CUST-{customer_id}"


def _case_ref(case):
    return str(
        case.get(
            "case_number",
            case.get("id", "N/A")
        )
    )


# ============================================================
# EMAIL AUDIT LOG
# ============================================================

def _log(
    customer_id,
    case_id,
    recipient,
    notification_type,
    subject,
    status,
    error=None,
):
    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO email_notifications
            (
                customer_id,
                case_id,
                recipient_email,
                notification_type,
                subject,
                status,
                error_message,
                sent_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                case_id,
                recipient,
                notification_type,
                subject,
                status,
                error,
                datetime.utcnow().isoformat()
                if status == "SENT"
                else None,
            ),
        )

        conn.commit()

    finally:
        conn.close()


# ============================================================
# GROQ / LLM EMAIL CONTENT
# ============================================================

def generate_email_content(
    event,
    customer,
    case=None,
    reason=None,
    decision=None,
):
    """
    Ask the existing Groq LLM to write the email body.

    The LLM ONLY generates the message content.

    It does NOT control:
    - recipient
    - SMTP credentials
    - email sending
    - database audit
    """

    from llm.groq_client import get_llm

    llm = get_llm()

    name = customer.get("name", "Customer")
    customer_id = _customer_ref(customer["id"])

    case_number = (
        _case_ref(case)
        if case
        else "N/A"
    )

    # --------------------------------------------------------
    # REGISTRATION
    # --------------------------------------------------------

    if event == "REGISTRATION":

        prompt = f"""
You are the customer communication assistant
for OnboardAI, a KYC verification platform.

Write a professional, friendly and concise
plain-text registration success email.

Customer name: {name}
Customer ID: {customer_id}

The customer has successfully registered.

Tell the customer:
- Registration was successful.
- Include their Customer ID.
- They can now start their KYC process.
- Thank them for registering.

Rules:
- Plain text only.
- Do not use Markdown.
- Do not invent information.
- Do not mention AI or LLM.
- Do not mention system prompts.
- Do not write a subject line.
- Keep it concise.

End with:

Regards,
OnboardAI Team
"""

    # --------------------------------------------------------
    # HUMAN REVIEW
    # --------------------------------------------------------

    elif event == "HUMAN_REVIEW":

        prompt = f"""
You are the customer communication assistant
for OnboardAI, a KYC verification platform.

Write a professional and reassuring plain-text
email informing the customer that their KYC case
has moved to human review.

Customer name: {name}
Customer ID: {customer_id}
KYC case: {case_number}

Reason:
{reason or "Additional verification is required."}

Tell the customer:
- Their KYC case requires human review.
- The verification team will review the case.
- They do not need to take action unless
  additional information is requested.
- They can sign in to OnboardAI to track progress.

Rules:
- Do not say the customer failed KYC.
- Do not invent information.
- Do not expose internal AI reasoning.
- Do not expose risk scores.
- Do not mention system prompts.
- Plain text only.
- No Markdown.
- Do not write a subject line.
- Keep it concise.

End with:

Regards,
OnboardAI Team
"""

    # --------------------------------------------------------
    # APPROVED
    # --------------------------------------------------------

    elif event == "APPROVED":

        prompt = f"""
You are the customer communication assistant
for OnboardAI, a KYC verification platform.

Write a professional and positive plain-text
email informing the customer that their KYC
verification has been successfully approved.

Customer name: {name}
Customer ID: {customer_id}
KYC case: {case_number}

Decision: APPROVED

Tell the customer:
- Their KYC verification has been approved.
- Include their Customer ID.
- Include their KYC case number.
- Thank them for completing verification.

Rules:
- Do not invent information.
- Do not expose internal AI reasoning.
- Do not expose risk scores.
- Do not mention system prompts.
- Plain text only.
- No Markdown.
- Do not write a subject line.
- Keep it concise.

End with:

Regards,
OnboardAI Team
"""

    # --------------------------------------------------------
    # REJECTED
    # --------------------------------------------------------

    elif event == "REJECTED":

        prompt = f"""
You are the customer communication assistant
for OnboardAI, a KYC verification platform.

Write a professional and respectful plain-text
email informing the customer that their KYC
verification was not approved.

Customer name: {name}
Customer ID: {customer_id}
KYC case: {case_number}

Decision: REJECTED

Tell the customer:
- Their KYC verification was not approved.
- Include their KYC case number.
- Ask them to sign in to OnboardAI or contact
  support for the next steps.

Rules:
- Do not invent a rejection reason.
- Do not expose internal AI reasoning.
- Do not expose risk scores.
- Do not mention system prompts.
- Do not use threatening language.
- Plain text only.
- No Markdown.
- Do not write a subject line.
- Keep it concise.

End with:

Regards,
OnboardAI Team
"""

    else:
        raise ValueError(
            f"Unknown email event: {event}"
        )

    if llm is None:
        # Communication remains available when the optional LLM provider is not configured.
        if event == "REGISTRATION":
            return f"Hello {name},\n\nYour OnboardAI registration was successful. Your Customer ID is {customer_id}. You can now sign in and start your KYC process.\n\nRegards,\nOnboardAI Team"
        if event == "HUMAN_REVIEW":
            return f"Hello {name},\n\nYour KYC case {case_number} requires a human review. Our team will review the submitted information and update you with the next step.\n\nRegards,\nOnboardAI Team"
        if event == "APPROVED":
            return f"Hello {name},\n\nYour KYC case {case_number} has been approved. You may continue with the next onboarding step.\n\nRegards,\nOnboardAI Team"
        if event == "REJECTED":
            return f"Hello {name},\n\nYour KYC case {case_number} was not approved. Please contact support for the next steps.\n\nRegards,\nOnboardAI Team"

    response = llm.invoke(prompt)

    content = getattr(
        response,
        "content",
        str(response),
    )

    return str(content).strip()


# ============================================================
# SMTP SEND
# ============================================================

def send_email(
    to_email,
    subject,
    text,
    *,
    customer_id=None,
    case_id=None,
    notification_type="GENERAL",
):

    if not _enabled():

        _log(
            customer_id,
            case_id,
            to_email,
            notification_type,
            subject,
            "DISABLED",
        )

        return False

    host = _value("SMTP_HOST")
    username = _value("SMTP_USERNAME")
    password = _smtp_password()

    from_email = _value(
        "SMTP_FROM_EMAIL",
        username,
    )

    try:
        port = int(
            _value(
                "SMTP_PORT",
                "587",
            )
        )
    except ValueError:
        port = 587

    use_tls = _value(
        "SMTP_USE_TLS",
        "true",
    ).lower() in {
        "1", "true", "yes", "on"
    }

    use_ssl = _value(
        "SMTP_USE_SSL",
        "false",
    ).lower() in {
        "1", "true", "yes", "on"
    }

    if not host or not username or not password:

        error = (
            "SMTP configuration incomplete. "
            "Check SMTP_HOST, SMTP_USERNAME "
            "and SMTP_PASSWORD."
        )

        _log(
            customer_id,
            case_id,
            to_email,
            notification_type,
            subject,
            "FAILED",
            error,
        )

        return False

    message = EmailMessage()

    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(text)

    try:

        smtp_class = (
            smtplib.SMTP_SSL
            if use_ssl or port == 465
            else smtplib.SMTP
        )

        with smtp_class(
            host,
            port,
            timeout=25,
        ) as smtp:

            smtp.ehlo()

            if use_tls and not (
                use_ssl or port == 465
            ):
                smtp.starttls()
                smtp.ehlo()

            smtp.login(
                username,
                password,
            )

            smtp.send_message(message)

        _log(
            customer_id,
            case_id,
            to_email,
            notification_type,
            subject,
            "SENT",
        )

        logger.info(
            "Email sent: %s -> %s",
            notification_type,
            to_email,
        )

        return True

    except smtplib.SMTPAuthenticationError as exc:

        error = (
            "Gmail SMTP authentication failed. "
            "Use a Google App Password for "
            "SMTP_PASSWORD, not the normal Gmail password. "
            f"Server response: {exc}"
        )

        logger.error(error)

        _log(
            customer_id,
            case_id,
            to_email,
            notification_type,
            subject,
            "FAILED",
            error[:1000],
        )

        return False

    except Exception as exc:

        logger.exception(
            "Email delivery failed"
        )

        _log(
            customer_id,
            case_id,
            to_email,
            notification_type,
            subject,
            "FAILED",
            str(exc)[:1000],
        )

        return False


# ============================================================
# REGISTRATION EMAIL
# ============================================================

def send_registration_success_email(customer):

    subject = (
        "OnboardAI - Registration Successful"
    )

    try:

        body = generate_email_content(
            event="REGISTRATION",
            customer=customer,
        )

    except Exception:

        logger.exception(
            "Registration LLM email generation failed"
        )

        body = (
            f"Hello {customer.get('name', 'Customer')},\n\n"
            "Your registration with OnboardAI was "
            "completed successfully.\n\n"
            f"Customer ID: {_customer_ref(customer['id'])}\n\n"
            "You can now start your KYC process.\n\n"
            "Regards,\n"
            "OnboardAI Team"
        )

    return send_email(
        customer["email"],
        subject,
        body,
        customer_id=customer["id"],
        notification_type="REGISTRATION_SUCCESS",
    )


# ============================================================
# HUMAN REVIEW EMAIL
# ============================================================

def send_kyc_review_email(
    customer,
    case,
    reason=None,
):

    subject = (
        "OnboardAI - KYC Requires Human Review"
    )

    try:

        body = generate_email_content(
            event="HUMAN_REVIEW",
            customer=customer,
            case=case,
            reason=reason,
        )

    except Exception:

        logger.exception(
            "Human review LLM email generation failed"
        )

        body = (
            f"Hello {customer.get('name', 'Customer')},\n\n"
            f"Your KYC case {_case_ref(case)} "
            "has moved to human review.\n\n"
            "Our verification team will review your case. "
            "No action is required unless additional "
            "information is requested.\n\n"
            "You can sign in to OnboardAI to track "
            "your KYC progress.\n\n"
            "Regards,\n"
            "OnboardAI Team"
        )

    return send_email(
        customer["email"],
        subject,
        body,
        customer_id=customer["id"],
        case_id=case["id"],
        notification_type="KYC_HUMAN_REVIEW",
    )


# ============================================================
# FINAL KYC DECISION EMAIL
# ============================================================

def send_kyc_decision_email(
    customer,
    case,
    decision,
):

    decision = str(
        decision or case.get("status", "")
    ).upper()

    if decision == "APPROVED":

        event = "APPROVED"

        subject = (
            "OnboardAI - KYC Approved"
        )

    else:

        event = "REJECTED"

        subject = (
            "OnboardAI - KYC Decision Update"
        )

    try:

        body = generate_email_content(
            event=event,
            customer=customer,
            case=case,
            decision=decision,
        )

    except Exception:

        logger.exception(
            "KYC decision LLM email generation failed"
        )

        if decision == "APPROVED":

            body = (
                f"Hello {customer.get('name', 'Customer')},\n\n"
                f"Your KYC case {_case_ref(case)} "
                "has been successfully approved.\n\n"
                f"Customer ID: {_customer_ref(customer['id'])}\n"
                "Status: APPROVED\n\n"
                "Thank you for completing your "
                "verification with OnboardAI.\n\n"
                "Regards,\n"
                "OnboardAI Team"
            )

        else:

            body = (
                f"Hello {customer.get('name', 'Customer')},\n\n"
                f"Your KYC case {_case_ref(case)} "
                "has received a final decision.\n\n"
                "Status: REJECTED\n\n"
                "Please sign in to OnboardAI or contact "
                "support for the next steps.\n\n"
                "Regards,\n"
                "OnboardAI Team"
            )

    return send_email(
        customer["email"],
        subject,
        body,
        customer_id=customer["id"],
        case_id=case["id"],
        notification_type="KYC_DECISION",
    )


# ============================================================
# COMPATIBILITY FUNCTION
# ============================================================

def send_kyc_completed_email(
    customer,
    case,
):
    """
    Kept because api/workflow.py currently imports this name.

    It uses the LLM-generated final KYC message.
    """

    decision = str(
        case.get(
            "status",
            "APPROVED",
        )
    ).upper()

    return send_kyc_decision_email(
        customer,
        case,
        decision,
    )


# ============================================================
# EMAIL AUDIT
# ============================================================

def get_email_notifications(limit=100):

    conn = get_connection()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM email_notifications
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )

        return [
            dict(row)
            for row in cur.fetchall()
        ]

    finally:
        conn.close()
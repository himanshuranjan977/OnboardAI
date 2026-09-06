import json
import re

from llm.groq_client import llm
from services.audit_service import (
    create_audit_event,
)

DOCUMENT_EXTRACTION_PROMPT = """
You are a KYC Document Intelligence Agent.

Your task is to analyze document text and extract
identity information.

Return ONLY valid JSON.

Do not use markdown.

Use exactly this structure:

{
    "document_type": null,
    "full_name": null,
    "date_of_birth": null,
    "document_number": null,
    "address": null,
    "nationality": null,
    "confidence": 0.0,
    "missing_fields": [],
    "warnings": []
}

Rules:

1. Never invent information.
2. Use null when information is unavailable.
3. confidence must be between 0 and 1.
4. missing_fields must list unavailable important fields.
5. warnings must contain unclear or suspicious observations.
"""


def extract_document_information(
    document_text: str,
) -> dict:

    prompt = f"""
{DOCUMENT_EXTRACTION_PROMPT}

DOCUMENT TEXT:

{document_text}
"""

    try:
        response = llm.invoke(prompt)
        content = response.content
    except Exception:
        # Provider failure must not stop the workflow; use conservative OCR parsing.
        text=document_text
        def first(patterns):
            for pattern in patterns:
                match=re.search(pattern,text,re.I|re.M)
                if match: return re.sub(r"\s+"," ",match.group(1)).strip()
            return None
        name=first([r"(?:NAME|FULL NAME)[\s:.-]+([A-Za-z][A-Za-z .'-]{2,})"])
        dob=first([r"(?:DOB|DATE OF BIRTH|D\.O\.B)[^0-9]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", r"(?:DOB|DATE OF BIRTH|D\.O\.B)[^0-9]*(\d{4}[/-]\d{1,2}[/-]\d{1,2})"])
        return {"document_type":None,"full_name":name,"date_of_birth":dob,"document_number":None,"address":None,"nationality":None,"confidence":0.60 if (name or dob) else 0.0,"missing_fields":[x for x,v in {"full_name":name,"date_of_birth":dob}.items() if not v],"warnings":["Groq unavailable; deterministic OCR fallback used."]}

    

    if not isinstance(content, str):
        content = str(content)

    content = content.strip()

    # Remove accidental markdown fences
    if content.startswith("```json"):

        content = content[
            len("```json"):
        ].strip()

    if content.endswith("```"):

        content = content[:-3].strip()

    try:

        result = json.loads(content)

    except json.JSONDecodeError as error:

        return {
            "document_type": None,
            "full_name": None,
            "date_of_birth": None,
            "document_number": None,
            "address": None,
            "nationality": None,
            "confidence": 0.0,
            "missing_fields": [],
            "warnings": [
                "Invalid JSON returned by LLM.",
                str(error),
            ],
        }

    required = {"document_type": None, "full_name": None, "date_of_birth": None, "document_number": None, "address": None, "nationality": None, "confidence": 0.0, "missing_fields": [], "warnings": []}
    normalized={**required, **(result if isinstance(result, dict) else {})}
    try: normalized["confidence"]=max(0.0,min(1.0,float(normalized.get("confidence") or 0.0)))
    except Exception: normalized["confidence"]=0.0
    if not isinstance(normalized.get("missing_fields"),list): normalized["missing_fields"]=[]
    if not isinstance(normalized.get("warnings"),list): normalized["warnings"]=[]
    return normalized


def document_agent(state):

    print("\n[DOCUMENT AGENT] Started")
    create_audit_event(

        case_id=state.get(
            "case_id"
        ),

        agent_name=
            "document_agent",

        event_type=
            "AGENT_STARTED",

        event_message=
            "Document analysis started.",
    )

    document_text = state.get(
        "document_text"
    )

    if not document_text:

        return {
            "current_agent": "document_agent",
            "workflow_status": "FAILED",
            "error": (
                "No document text available."
            ),
            "requires_human_review": True,
            "human_review_reason": (
                "Document text could not be extracted."
            ),
        }

    result = extract_document_information(
        document_text
    )

    confidence = result.get(
        "confidence",
        0
    )

    warnings = result.get(
        "warnings",
        []
    )

    # --------------------------------
    # Basic deterministic validation
    # --------------------------------

    requires_review = False
    review_reason = None

    if confidence < 0.70:

        requires_review = True

        review_reason = (
            "Document extraction confidence "
            "is below the review threshold."
        )

    elif warnings:

        requires_review = True

        review_reason = (
            "Document contains warnings."
        )

    print(
        "[DOCUMENT AGENT] Completed"
    )
    create_audit_event(

        case_id=state.get(
            "case_id"
        ),

        agent_name=
            "document_agent",

        event_type=
            "AGENT_COMPLETED",

        event_message=
            "Document analysis completed.",

        event_data={
            "document_type":
                result.get(
                    "document_type"
                ),

            "confidence":
                result.get(
                    "confidence"
                ),

            "missing_fields":
                result.get(
                    "missing_fields"
                ),

            "warnings":
                result.get(
                    "warnings"
                ),
        },
    )

    return {
        "current_agent": "document_agent",

        "workflow_status": (
            "HUMAN_REVIEW"
            if requires_review
            else "DOCUMENT_ANALYZED"
        ),

        "document_analysis": result,

        "requires_human_review": (
            requires_review
        ),

        "human_review_reason": (
            review_reason
        ),
    }
from extensions.integrations.mcp_gateway import gateway
from services.audit_service import create_audit_event
from services.evidence_service import create_evidence

def screening_agent(state):
    case_id=state.get("case_id"); document=state.get("document_analysis") or {}; customer_id=state.get("customer_id")
    customer={"customer_id":customer_id}
    # Carry optional demo screening controls stored at intake into the controlled tool call.
    try:
        from services.document_service import get_document
        import json
        raw=(get_document(state.get("document_id")) or {}).get("extracted_data")
        if raw:
            extra=json.loads(raw)
            document={**document,"fields":{**(document.get("fields") or {}),**extra}}
    except Exception:
        pass
    result=gateway.call("screening", {"customer":customer, "document":document}).get("result", {})
    sanctions=result.get("sanctions",{}); pep=result.get("pep",{}); media=result.get("adverse_media",{})
    review=any(x.get("status") not in {"CLEAR","NO_MATCH","DISABLED"} for x in (sanctions,pep,media))
    out={"status":"REVIEW" if review else "CLEAR", "sanctions":sanctions, "pep":pep, "adverse_media":media, "provider":result.get("provider","MCP"), "manual_review_required":review}
    create_evidence(case_id, state.get("document_id"), "screening_agent", "SCREENING_RESULT", None, out["provider"], None, None, out["status"], None, "Sanctions, PEP and adverse-media screening result.")
    create_audit_event(case_id=case_id, agent_name="screening_agent", event_type="AGENT_COMPLETED", event_message=f"Screening completed with status {out['status']}.", event_data=out)
    return {"current_agent":"screening_agent", "workflow_status":"SCREENING_COMPLETED", "screening":out, "requires_human_review":review, "human_review_reason":"Screening returned a potential match or provider exception." if review else None}

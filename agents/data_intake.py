from services.audit_service import create_audit_event

def data_intake_agent(state):
    case_id = state.get("case_id")
    customer_id = state.get("customer_id")
    document_id = state.get("document_id")
    missing = []
    if not customer_id: missing.append("customer_id")
    if not document_id: missing.append("document_id")
    result = {"status": "PASS" if not missing else "REVIEW", "missing": missing, "document_received": bool(document_id)}
    create_audit_event(case_id=case_id, agent_name="data_intake_agent", event_type="AGENT_COMPLETED", event_message="Data intake validation completed.", event_data=result)
    return {"current_agent":"data_intake_agent", "workflow_status":"DATA_INTAKE_COMPLETED" if not missing else "HUMAN_REVIEW", "data_intake":result, "requires_human_review":bool(missing), "human_review_reason":"Required KYC intake data is missing." if missing else None}

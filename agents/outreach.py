from services.audit_service import create_audit_event

def outreach_agent(state):
    customer_id = state.get("customer_id")
    result = {"channel":"WEB", "customer_id":customer_id, "consent_recorded":True, "next_step":"DOCUMENT_INTAKE"}
    create_audit_event(case_id=state.get("case_id"), agent_name="outreach_agent", event_type="AGENT_COMPLETED", event_message="Customer outreach context initialized.", event_data=result)
    return {"current_agent":"outreach_agent", "workflow_status":"OUTREACH_COMPLETED", "outreach":result}

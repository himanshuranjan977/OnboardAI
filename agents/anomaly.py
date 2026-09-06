from services.audit_service import create_audit_event
from services.evidence_service import create_evidence

def anomaly_agent(state):
    alerts=[]
    doc=state.get("document_analysis") or {}; identity=state.get("identity_verification") or {}; screening=state.get("screening") or {}; risk=state.get("risk_assessment") or {}
    if doc.get("warnings"): alerts.append("DOCUMENT_WARNING")
    if identity.get("identity_status") in {"MISMATCH","REQUIRES_REVIEW"}: alerts.append("IDENTITY_EXCEPTION")
    if screening.get("manual_review_required"): alerts.append("SCREENING_EXCEPTION")
    if risk.get("risk_level") == "HIGH": alerts.append("HIGH_RISK_PATTERN")
    status="ALERT" if alerts else "CLEAR"; severity="HIGH" if "HIGH_RISK_PATTERN" in alerts or "SCREENING_EXCEPTION" in alerts else ("MEDIUM" if alerts else "NONE")
    out={"status":status,"alerts":alerts,"severity":severity,"manual_review_required":bool(alerts)}
    create_evidence(state.get("case_id"),state.get("document_id"),"anomaly_agent","ANOMALY_ALERT",None,"RULE_ENGINE",None,None,status,None,"; ".join(alerts) or "No anomaly detected.")
    create_audit_event(case_id=state.get("case_id"),agent_name="anomaly_agent",event_type="AGENT_COMPLETED",event_message=f"Anomaly scan completed: {status}.",event_data=out)
    return {"current_agent":"anomaly_agent","workflow_status":"ANOMALY_CHECKED","anomaly":out,"requires_human_review":bool(alerts),"human_review_reason":"Anomaly/alert agent raised an exception." if alerts else None}

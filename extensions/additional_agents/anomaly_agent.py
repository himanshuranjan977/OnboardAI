def anomaly_agent(state: dict) -> dict:
    doc = state.get("document_result", {})
    identity = state.get("identity", {})
    alerts = []
    if doc.get("status") == "REVIEW": alerts.append("DOCUMENT_EXCEPTION")
    if identity.get("score", 0) < 70: alerts.append("LOW_IDENTITY_MATCH")
    return {"anomaly": {"status": "ALERT" if alerts else "CLEAR", "alerts": alerts, "manual_review_required": bool(alerts)}}

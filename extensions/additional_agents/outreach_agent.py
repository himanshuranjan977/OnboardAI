def outreach_agent(state: dict) -> dict:
    customer = state["customer"]
    return {"outreach": {"channel": "WEB", "customer_id": customer["customer_id"], "consent_recorded": True, "next_step": "DOCUMENT_INTAKE"}}

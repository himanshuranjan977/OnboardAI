def data_intake_agent(state: dict) -> dict:
    customer = state["customer"]
    document = state["document"]
    required = ["customer_id", "name"]
    missing = [x for x in required if not customer.get(x)]
    return {"data_intake": {"status": "PASS" if not missing else "REVIEW", "missing": missing, "document_received": bool(document.get("file_name"))}}

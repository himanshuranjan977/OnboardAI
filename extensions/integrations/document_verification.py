def verify_document(document: dict) -> dict:
    fields = document.get("fields", {})
    valid = bool(fields.get("document_format_valid"))
    return {"status": "FORMAT_CHECK_PASS" if valid else "FORMAT_CHECK_REVIEW", "authenticity_verified": False, "provider": "LOCAL_FORMAT_CHECK", "note": "This does not prove authenticity. Configure a trusted verification provider for production."}

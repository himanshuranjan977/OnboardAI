from integrations.mcp_gateway import gateway

def screen_customer(customer: dict, document_result: dict) -> dict:
    result=gateway.call("screening",{"customer":customer,"document":document_result})["result"]
    sanctions,pep,media=result["sanctions"],result["pep"],result["adverse_media"]
    review=any(x.get("status") not in {"CLEAR","NO_MATCH","DISABLED"} for x in (sanctions,pep,media))
    return {"status":"REVIEW" if review else "CLEAR","sanctions":sanctions,"pep":pep,"adverse_media":media,"provider":result.get("provider","MCP"),"manual_review_required":review}

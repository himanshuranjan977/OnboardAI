from .screening import screen
from .document_verification import verify_document

class MCPToolGateway:
    """Allow-listed tool boundary for KYC integrations."""
    allowed={"screening","document_verification","crm_lookup","registry_lookup"}
    def call(self,tool,payload):
        if tool not in self.allowed: raise ValueError(f"Tool '{tool}' not allowed")
        if tool=="screening": return {"tool":tool,"status":"OK","result":screen(payload.get("customer",{}),payload.get("document"))}
        if tool=="document_verification": return {"tool":tool,"status":"OK","result":verify_document(payload.get("document",{}))}
        if tool=="crm_lookup": return {"tool":tool,"status":"DEMO","result":{"found":False}}
        return {"tool":tool,"status":"DEMO","result":{"match":False}}

gateway=MCPToolGateway()

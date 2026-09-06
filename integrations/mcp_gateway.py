from extensions.integrations.mcp_gateway import gateway as _gateway

class MCPToolGateway:
    allowed_tools={"screening","document_verification","crm_lookup","registry_lookup"}
    def call(self, tool, payload):
        if tool not in self.allowed_tools: raise ValueError(f"Tool '{tool}' is not allow-listed")
        return _gateway.call(tool,payload)

gateway=MCPToolGateway()

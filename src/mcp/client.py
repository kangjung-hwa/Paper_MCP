from src.mcp.registry import ToolRegistry


class MCPClient:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def list_tools(self, full_metadata: bool = True):
        return self.registry.public_specs(full_metadata)

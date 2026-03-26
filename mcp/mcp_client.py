from mcp.client import ClientSession

class MCPClient:
    def __init__(self):
        self.session = None

    async def connect(self):
        self.session = await ClientSession.connect_stdio(
            command="python",
            args=["mcp/mcp_server.py"]
        )

    async def list_tools(self):
        return await self.session.list_tools()

    async def call_tool(self, name, args):
        return await self.session.call_tool(name, args)
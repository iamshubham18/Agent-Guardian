
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE_DIR = Path(__file__).resolve().parent

server = StdioServerParameters(
    command=sys.executable,
    args=[str(BASE_DIR / "mcp_server.py")],
)

 # Read the contents of the data directory to ensure it exists
async def main():
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()

            print("Connected to AgentGuard MCP server.")
            print("Available tools:")

            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            filename = input(
                "\nEnter filename to test (sales.txt or ../main.py): "
            ).strip()

            result = await session.call_tool(
                "read_file",
                {"filename": filename},
            )

            print("\nMCP tool response:")

            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)

            if result.isError:
                print("\nResult: BLOCKED or tool error")
            else:
                print("\nResult: TOOL CALL COMPLETED")


if __name__ == "__main__":
    asyncio.run(main())

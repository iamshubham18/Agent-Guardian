
from mcp.server.fastmcp import FastMCP
from security import inspect_request, inspect_response
import sqlite3

mcp = FastMCP("AgentGuard Protected Tools")

DB_PATH = "audit.db"


def log_event(tool_name, decision, reason):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    tool_name TEXT,
                    decision TEXT,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                INSERT INTO events
                (agent_id, tool_name, decision, reason)
                VALUES (?, ?, ?, ?)
            """, ("mcp-client", tool_name, decision, reason))
    except sqlite3.Error:
        # Never print diagnostics to stdout: MCP uses stdout for its protocol.
        pass


@mcp.tool()
def read_file(filename: str) -> str:
    """Safely read an approved text file from AgentGuard's data directory."""

    check = inspect_request("read_file", {"filename": filename})

    if check["decision"] != "ALLOWED":
        log_event("read_file", "BLOCKED", check["reason"])
        raise ValueError(f"AgentGuard blocked request: {check['reason']}")

    target = check["target"]

    try:
        content = target.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        log_event("read_file", "BLOCKED", "File could not be read safely")
        raise ValueError("AgentGuard blocked request: file could not be read")

    response_check = inspect_response(content)

    if response_check["decision"] != "ALLOWED":
        log_event("read_file", "BLOCKED", response_check["reason"])
        raise ValueError(f"AgentGuard blocked response: {response_check['reason']}")

    log_event("read_file", "ALLOWED", "Request and response passed configured checks")
    return content


if __name__ == "__main__":
    mcp.run(transport="stdio")

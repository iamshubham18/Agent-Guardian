
from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = (BASE_DIR / "data").resolve()

ALLOWED_TOOLS = {"read_file"}

SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"reveal\s+(the\s+)?(system prompt|secrets|passwords)",
    r"send\s+.{0,80}confidential",
    r"bypass\s+(security|authentication|authorization)",
]

def inspect_request(tool_name, arguments):
    """Validate the requested tool and its arguments."""

    if tool_name not in ALLOWED_TOOLS:
        return {
            "decision": "BLOCKED",
            "risk": "HIGH",
            "reason": "Tool is not allowlisted",
        }

    if not isinstance(arguments, dict):
        return {
            "decision": "BLOCKED",
            "risk": "HIGH",
            "reason": "Arguments must be an object",
        }

    if set(arguments.keys()) != {"filename"}:
        return {
            "decision": "BLOCKED",
            "risk": "MEDIUM",
            "reason": "Unexpected or missing arguments",
        }

    filename = arguments.get("filename")

    if not isinstance(filename, str) or not filename.strip():
        return {
            "decision": "BLOCKED",
            "risk": "MEDIUM",
            "reason": "Invalid filename",
        }

    try:
        target = (DATA_DIR / filename).resolve()
        target.relative_to(DATA_DIR)
    except (ValueError, OSError, RuntimeError):
        return {
            "decision": "BLOCKED",
            "risk": "HIGH",
            "reason": "Path traversal or invalid path",
        }

    if not target.is_file():
        return {
            "decision": "BLOCKED",
            "risk": "MEDIUM",
            "reason": "File not found or not permitted",
        }

    return {
        "decision": "ALLOWED",
        "risk": "LOW",
        "reason": "Tool and file path passed validation",
        "target": target,
    }


def inspect_response(content):
    """Screen returned text for known suspicious patterns."""

    if not isinstance(content, str):
        return {
            "decision": "BLOCKED",
            "risk": "HIGH",
            "reason": "Unexpected response type",
        }

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return {
                "decision": "BLOCKED",
                "risk": "HIGH",
                "reason": "Suspicious instruction pattern detected",
            }

    return {
        "decision": "ALLOWED",
        "risk": "LOW",
        "reason": "No configured suspicious patterns detected",
    }

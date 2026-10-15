
from pathlib import Path
import os
import sqlite3
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from security import inspect_request, inspect_response
from ml_detector import predict_text, evaluate_model

app = FastAPI(title="AgentGuard Security API")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "audit.db"
API_KEY = os.getenv("AGENTGUARD_API_KEY", "demo-key-change-me")


class ToolRequest(BaseModel):
    agent_id: str
    tool_name: str
    arguments: dict = Field(default_factory=dict)
    
class MLTestRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)



# --------------------------------------------------
# DATABASE INITIALIZATION AND MIGRATION
# --------------------------------------------------

def initialize_database():
    """Create the audit table and add risk fields to older databases."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                agent_id TEXT,
                tool TEXT,
                decision TEXT,
                reason TEXT,
                risk TEXT,
                risk_score INTEGER
            )
        """)

        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(events)").fetchall()
        }

        if "risk" not in columns:
            conn.execute("ALTER TABLE events ADD COLUMN risk TEXT")

        if "risk_score" not in columns:
            conn.execute(
                "ALTER TABLE events ADD COLUMN risk_score INTEGER"
            )


initialize_database()


# --------------------------------------------------
# AUDIT LOGGING
# --------------------------------------------------

def log_event(
    tool,
    decision,
    reason,
    agent_id,
    risk="UNKNOWN",
    risk_score=None,
):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO events (
                timestamp, agent_id, tool, decision,
                reason, risk, risk_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            agent_id,
            tool,
            decision,
            reason,
            risk,
            risk_score,
        ))


def security_response(
    decision,
    risk,
    risk_score,
    reason,
    result=None,
    ml_prediction=None,
    ml_suspicious_score=None,
    ml_model=None,
):
    return {
        "decision": decision,
        "risk": risk,
        "risk_score": risk_score,
        "reason": reason,
        "result": result,
        "ml_prediction": ml_prediction,
        "ml_suspicious_score": ml_suspicious_score,
        "ml_model": ml_model,
    }


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():
    return {"message": "AgentGuard is running"}


# --------------------------------------------------
# PROTECTED TOOL API
# --------------------------------------------------

@app.post("/api/tool-call")
def tool_call(
    request: ToolRequest,
    x_api_key: str = Header(default=""),
):
    tool = request.tool_name
    agent_id = request.agent_id

    # 1. Authenticate caller.
    if x_api_key != API_KEY:
        reason = "Invalid API key"
        log_event(
            tool, "BLOCKED", reason, agent_id, "HIGH", 100
        )
        raise HTTPException(
            status_code=401,
            detail={
                "decision": "BLOCKED",
                "risk": "HIGH",
                "risk_score": 100,
                "reason": reason,
            },
        )

    # 2. Validate tool and arguments.
    try:
        check = inspect_request(tool, request.arguments)
    except (OSError, ValueError, TypeError, RuntimeError):
        check = {
            "decision": "BLOCKED",
            "risk": "HIGH",
            "risk_score": 90,
            "reason": "Request validation failed",
        }

    if check["decision"] != "ALLOWED":
        reason = check.get("reason", "Request blocked")
        risk = check.get("risk", "HIGH")
        score = check.get("risk_score", 90)

        log_event(tool, "BLOCKED", reason, agent_id, risk, score)
        return security_response("BLOCKED", risk, score, reason)

    # 3. Read only after validation passes.
    try:
        content = check["target"].read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        reason = "File could not be read safely"
        log_event(
            tool, "BLOCKED", reason, agent_id, "MEDIUM", 60
        )
        return security_response("BLOCKED", "MEDIUM", 60, reason)

    # 4. Screen the response with existing security rules.
    response_check = inspect_response(content)

    if response_check["decision"] != "ALLOWED":
        reason = response_check.get(
            "reason", "Suspicious response detected"
        )
        risk = response_check.get("risk", "HIGH")
        score = response_check.get("risk_score", 95)

        log_event(tool, "BLOCKED", reason, agent_id, risk, score)
        return security_response("BLOCKED", risk, score, reason)

    # 5. Run ML detection on the file content.
    # ML is advisory only and does not override security rules.
    try:
        ml_result = predict_text(content)
        ml_prediction = ml_result["prediction"]
        ml_score = ml_result["suspicious_score"]
        ml_model = ml_result["model_type"]
    except (ValueError, FileNotFoundError, OSError):
        # Keep the existing security API available if ML is unavailable.
        ml_prediction = "UNAVAILABLE"
        ml_score = None
        ml_model = "TF-IDF + Logistic Regression"

    # 6. Log the existing rule-based security decision.
    risk = response_check.get("risk", "LOW")
    score = response_check.get("risk_score", 5)
    reason = "Security rules passed"

    if ml_prediction == "SUSPICIOUS":
        reason += "; ML flagged suspicious text (advisory)"

    log_event(tool, "ALLOWED", reason, agent_id, risk, score)

    # 7. Return rule-based decision and separate ML output.
    return security_response(
        "ALLOWED",
        risk,
        score,
        reason,
        result=content,
        ml_prediction=ml_prediction,
        ml_suspicious_score=ml_score,
        ml_model=ml_model,
    )


# --------------------------------------------------
# AUDIT EVENTS API
# --------------------------------------------------

@app.get("/api/events")
def get_events(
    x_api_key: str = Header(default=""),
):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT
                id,
                timestamp,
                agent_id,
                tool,
                decision,
                reason,
                risk,
                risk_score
            FROM events
            ORDER BY id DESC
            LIMIT 15
        """).fetchall()

    return {
        "events": [dict(row) for row in rows]
    }

# --------------------------------------------------
# ML THREAT DETECTION TEST API
# --------------------------------------------------

@app.post("/api/ml-test")
def ml_test(
    request: MLTestRequest,
    x_api_key: str = Header(default=""),
):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )

    try:
        return predict_text(request.text)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="ML model is not trained. Train it first.",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.get("/api/ml-evaluate")
def ml_evaluate(
    x_api_key: str = Header(default=""),
):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )

    try:
        return evaluate_model()

    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="ML model is not trained. Train it first.",
        )

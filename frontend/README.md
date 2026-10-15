# AgentGuard --- Runtime Defence for MCP-Connected AI Tools

> Hackurity 2026 · REVA University · Cybersecurity Club

## Problem 

**PS number:** '[problem statement 1]'
**PS title:** `[GUARDING THE AGENT 
                RUNTIME DEFENCE FOR MCP-CONNECTED AI-TOOLS]`

AgentGuard is a prototype runtime security layer for tool calls made by
AI applications. It is designed to validate tool requests, restrict
access to local sample files, inspect tool responses for suspicious
instruction patterns, and record security decisions.

Replace the placeholders above with the exact problem statement details
before submission.

## What it does

-   **Tool allowlisting:** permits the configured `read_file` tool and
    blocks unsupported tools such as `delete_file` and
    `execute_command`.
-   **Argument validation:** checks tool arguments against the expected
    schema.
-   **Path containment:** restricts file reads to `backend/data/` and is
    designed to reject path traversal.
-   **Response screening:** checks returned text for suspicious
    instruction patterns.
-   **Risk scoring:** provides a rule-based decision, reason, and risk
    score.
-   **ML threat detection:** uses TF--IDF and Logistic Regression to
    classify text as `NORMAL` or `SUSPICIOUS`. ML is advisory and must
    not override rule-based enforcement.
-   **Audit logging:** records decisions in a local SQLite database.
-   **Dashboard:** includes a security tester, ML test panel,
    model-evaluation view, and audit-log view.
-   **MCP demonstration:** includes an MCP server and test client;
    verify end-to-end operation before claiming successful integration.

This is a prototype, not a guarantee that every attack will be detected.
Only claim features as working after verifying them in the live demo.

## Architecture

``` text
User / Demo Dashboard
        |
        v
React + Vite frontend
        |  /api requests
        v
FastAPI backend (main.py)
        |
        +--> API-key check and request validation
        +--> Rule-based security layer (security.py)
        |       +--> Tool allowlist
        |       +--> Argument schema validation
        |       +--> Path containment checks
        |       +--> Tool-output screening
        +--> ML detector (ml_detector.py)
        |       +--> TF–IDF + Logistic Regression
        |       +--> Advisory NORMAL / SUSPICIOUS prediction
        +--> SQLite audit log (audit.db)
        |
        v
Decision, reason, risk score and audit events
```

The MCP server/client are separate demo components. Describe them as
integrated end-to-end only after testing them.

## How to run it

### Prerequisites

-   Python 3.10 or a compatible version supported by the dependencies
-   Node.js and npm
-   Git, if cloning from GitHub

Pin and test dependency versions before submission. The README alone
should be sufficient for setup on a clean machine.

### 1. Get the repository

``` powershell
git clone [https://github.com/iamshubham18/Agent-Guardian]
cd agentguard
```

### 2. Start the backend

``` powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
```

Install dependencies from the backend dependency file, if present:

``` powershell
pip install -r requirements.txt
```

If `requirements.txt` does not exist, create it with all required,
tested backend dependencies before submission.

If the ML model is not included in the repository, install its
dependencies and generate it:

``` powershell
pip install scikit-learn joblib
python ml_detector.py
```

Start the API:

``` powershell
python -m uvicorn main:app --reload
```

Backend URL: `http://127.0.0.1:8000`\
API documentation: `http://127.0.0.1:8000/docs`

Configure the API key consistently between the backend and frontend. Use
`.env.example` to document variable names and safe demo defaults. Do not
commit real secrets. The current demo key has been described as
`demo-key-change-me`; replace it for any non-demo deployment.

### 3. Start the frontend

Open a second terminal at the repository root:

``` powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

### Sample data and local files

-   Sample files: `backend/data/sales.txt` and
    `backend/data/malicious.txt`
-   Audit storage: local SQLite database
-   Keep `.venv/`, `node_modules/`, local `.env` files, and
    machine-specific artifacts out of Git unless intentionally required
    as safe fixtures.
-   Include sample data and all required setup instructions in the
    public repository.

## How to run the demo

Use only the local application and the project's own sample data.

1.  Start the backend and frontend.
2.  Open the dashboard.
3.  **Allowed request:** choose `read_file` and enter `sales.txt`.
    Verify the decision and audit event.
4.  **Blocked tool:** choose `delete_file` or `execute_command`. Verify
    that the request is blocked and a reason is shown.
5.  **Path traversal:** try `../main.py`. Verify the request is rejected
    and no file outside `backend/data/` is returned.
6.  **Response screening:** request `malicious.txt`. Verify whether its
    suspicious instruction patterns are detected.
7.  **ML test:** submit normal and suspicious examples in the ML Threat
    Detection Lab. Record the actual prediction and score.
8.  **Model evaluation:** run evaluation and inspect test-set size,
    accuracy, metrics, and confusion matrix. Report measured results
    honestly; do not present hardcoded illustrative values as measured
    results.
9.  **Audit log:** refresh the audit log and confirm allow/block events
    and reasons appear.
10. **MCP test:** run the MCP server and test client using commands
    confirmed from the source code. Verify the tool call and its
    security outcome.

Capture evidence from the running build. Mark a feature as **partial**
or **not done** in the technical write-up if it does not pass.

## Tech stack

-   **Frontend:** React, Vite, JavaScript, CSS
-   **Backend/API:** Python, FastAPI, Uvicorn
-   **Security:** Python validation and rule-based checks
-   **Machine learning:** scikit-learn, TF--IDF, Logistic Regression,
    joblib
-   **Audit storage:** SQLite
-   **Tool integration demo:** MCP server and test client, subject to
    end-to-end verification



## Threat model

**In scope:** malformed or unsupported tool calls, unexpected arguments,
path traversal attempts against the local sample-file tool, and
suspicious instruction patterns in returned text.

**Assumptions:** the demo runs locally; sample files are controlled by
the team; the API key is configured correctly; and rule-based checks
form the enforcement boundary.

**Not guaranteed / out of scope:** detection of every prompt injection
or unknown attack, security of arbitrary third-party systems, and
production-grade identity and authorization.

## Evidence and known limitations

-   Use metrics from the actual test run. Document dataset size, split
    method, random seed (if used), and confusion matrix.
-   The starter ML dataset contains synthetic examples; results on it do
    not establish real-world detection accuracy.
-   ML predictions are advisory; rule-based checks should remain
    authoritative for allow/block decisions.
-   Pattern-based screening can miss attacks and produce false
    positives.
-   This README describes the intended demo flow. Confirm each feature
    and report it as working, partial, or not done based on evidence.

## Safety

Test only on systems you own, local/simulated testbeds, or
organiser-provided targets. Do not scan or attack third-party systems,
venue networks, or other teams. Do not use real credentials, personal
data, or money.

## Credits and AI tools

Credit every reused library, repository, dataset, and code snippet with
its URL and a brief description of what was reused. Follow the
applicable licences.

**AI tools used:** OpenAI ChatGPT was used for project planning,
explanations, and code/documentation drafting. Update this statement to
accurately list every AI tool used by the team and its purpose.




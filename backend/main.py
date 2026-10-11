"""FastAPI backend for the Campus Customs operations dashboard."""

from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:  # Supports both `uvicorn main:app` from backend/ and package imports.
    from .team import AUDIT_PATH, run_ticket
except ImportError:  # pragma: no cover - exercised by the documented command
    from team import AUDIT_PATH, run_ticket


ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "data" / "campus_customs_new.db"
ORIGINAL_DATABASE_PATH = ROOT / "data" / "campus_customs.db"

app = FastAPI(title="Campus Customs Operations API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ApprovalRequest(BaseModel):
    kind: str = Field(min_length=1, description="payment or purchase_order")
    ref_id: int | None = None
    amount: float = Field(gt=0)
    approved_by: str = Field(min_length=1)


def _read_events() -> list[dict[str, Any]]:
    if not AUDIT_PATH.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in AUDIT_PATH.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                events.append(value)
        except json.JSONDecodeError:
            continue
    return events


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tickets")
def list_tickets() -> list[dict[str, Any]]:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, type, requester, subject, status, created_at FROM tickets ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/tickets/{ticket_id}/run")
async def run_agent_team(ticket_id: int) -> Any:
    with sqlite3.connect(DATABASE_PATH) as connection:
        exists = connection.execute(
            "SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
    if exists is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} was not found in the database.")
    try:
        decision = await run_ticket(ticket_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Agent team failed: {error}") from error
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("UPDATE tickets SET status = 'resolved' WHERE id = ?", (ticket_id,))
    return decision.model_dump()


@app.get("/events")
def recent_events(limit: int = 100) -> list[dict[str, Any]]:
    if not 1 <= limit <= 500:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")
    return _read_events()[-limit:]


@app.post("/approvals")
def approve_payment(request: ApprovalRequest) -> dict[str, Any]:
    """Apply a human-approved outgoing payment and record the audit row."""
    if request.kind not in {"payment", "purchase_order"}:
        raise HTTPException(status_code=400, detail="kind must be payment or purchase_order")
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        account = connection.execute(
            "SELECT name, balance, date FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()
        if account is None:
            raise HTTPException(status_code=500, detail="checking account is missing")
        new_balance = account["balance"] - request.amount
        if new_balance < 0:
            raise HTTPException(status_code=409, detail="approval would make checking cash negative")
        connection.execute(
            "UPDATE cash_accounts SET balance = ? WHERE name = 'checking'",
            (new_balance,),
        )
        cursor = connection.execute(
            "INSERT INTO payments(kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, datetime('now'), ?)",
            (request.kind, request.ref_id, request.amount, "checking", request.approved_by),
        )
        payment_id = cursor.lastrowid
    return {
        "payment_id": payment_id,
        "kind": request.kind,
        "amount": request.amount,
        "approved_by": request.approved_by,
        "account": "checking",
        "new_balance": new_balance,
    }


@app.get("/cash")
def checking_balance() -> dict[str, Any]:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT name, balance, date FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="checking account is missing")
    return dict(row)


@app.post("/reset")
def reset_database() -> dict[str, str]:
    """Restore the working copy from the preserved original database."""
    shutil.copyfile(ORIGINAL_DATABASE_PATH, DATABASE_PATH)
    return {"status": "reset", "database": str(DATABASE_PATH.relative_to(ROOT))}

"""Typed contracts shared by the Campus Customs agent team."""

from typing import Literal
from pydantic import BaseModel, Field


AgentRole = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]


class AgentFinding(BaseModel):
    agent: AgentRole
    facts: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    approval_required: bool = False


class AgentReport(AgentFinding):
    recommendation: str = ""
    customer_draft: str | None = None


class TicketDecision(BaseModel):
    ticket_id: int
    decision: str
    required_actions: list[str] = Field(default_factory=list)
    specialist_findings: list[AgentFinding] = Field(default_factory=list)
    remaining_approval: str | None = None
    customer_draft: str | None = None

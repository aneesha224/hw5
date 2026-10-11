"""PydanticAI team orchestration over the Campus Customs MCP server."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

try:  # Supports both package imports and `uvicorn main:app` from backend/.
    from .models import AgentFinding, AgentReport, TicketDecision
except ImportError:  # pragma: no cover - exercised by the documented command
    from models import AgentFinding, AgentReport, TicketDecision


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "output" / "audit_trail.json"
MAX_SPECIALIST_STEPS = 5
MAX_TOOL_CALLS = 12


def audit(agent: str, step: str, detail: str, **extra: Any) -> None:
    """Append one JSON-lines audit event; existing events are never removed."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "time": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "step": step,
        "detail": detail[:500],
        **extra,
    }
    with AUDIT_PATH.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")


class MCPTools:
    """Small client gateway; business facts come only through MCP."""

    def __init__(self, session: ClientSession):
        self.session = session
        self.calls = 0

    async def call(self, name: str, **arguments: Any) -> Any:
        self.calls += 1
        if self.calls > MAX_TOOL_CALLS:
            raise RuntimeError("MCP tool-call limit reached for this ticket.")
        audit("mcp", "tool_call", name, arguments=arguments)
        result = await self.session.call_tool(name, arguments)
        if not result.content:
            return None
        return json.loads(result.content[0].text)


def _agent(role: str, prompt_file: str, model: str | None) -> Agent[Any, AgentReport]:
    prompt = (ROOT / "backend" / "prompts" / prompt_file).read_text(encoding="utf-8")
    model_name = model or os.getenv("PORTKEY_MODEL", "gpt-5.6-luna")
    portkey_key = os.getenv("PORTKEY_API_KEY")
    if portkey_key:
        client = AsyncOpenAI(
            api_key=portkey_key,
            base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
            default_headers={
                "x-portkey-api-key": portkey_key,
                "x-portkey-model-id": model_name,
            },
        )
        provider = OpenAIProvider(openai_client=client)
        model_ref = OpenAIChatModel(model_name, provider=provider)
    else:
        model_ref = model_name
    return Agent(model_ref, output_type=AgentReport, system_prompt=prompt, name=role)


async def run_ticket(ticket_id: int, model: str | None = None) -> TicketDecision:
    """Run bounded specialist delegation followed by the Boss final decision."""
    audit("boss", "start", f"Reviewing ticket {ticket_id}", ticket_id=ticket_id)
    params = StdioServerParameters(
        command=str(ROOT / ".venv" / "bin" / "python"),
        args=["-m", "mcp_server.server"],
        cwd=str(ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = MCPTools(session)
            ticket_context = await tools.call("get_ticket_inventory", ticket_id=ticket_id)
            ticket = ticket_context["ticket"]
            audit("boss", "ticket_loaded", f"Loaded ticket {ticket_id}", ticket_id=ticket_id)

            specialist_roles: list[tuple[str, str, str, list[str]]] = []
            if ticket["sku"]:
                specialist_roles.append(("inventory", "inventory.md", "Inventory", ["get_ticket_inventory", "get_vendor_shipping_status", "get_product_pricing"]))
                specialist_roles.append(("accounting", "accounting.md", "Accounting", ["get_shop_cash", "get_ticket_invoice", "get_product_pricing"]))
            if ticket["lease_id"]:
                specialist_roles.append(("facilities", "facilities.md", "Facilities", ["get_ticket_lease"]))
            if ticket["requester"] and ticket["type"] == "customer_order":
                specialist_roles.append(("customer_service", "customer_service.md", "Customer Service", ["get_ticket_inventory", "get_ticket_invoice"]))

            findings: list[AgentFinding] = []
            for index, (role, prompt_file, label, tool_names) in enumerate(specialist_roles):
                if index >= MAX_SPECIALIST_STEPS:
                    break
                facts: dict[str, Any] = {}
                for tool_name in tool_names:
                    if tool_name == "get_ticket_inventory":
                        facts[tool_name] = await tools.call(tool_name, ticket_id=ticket_id)
                    elif tool_name == "get_ticket_invoice":
                        facts[tool_name] = await tools.call(tool_name, ticket_id=ticket_id)
                    elif tool_name == "get_ticket_lease":
                        facts[tool_name] = await tools.call(tool_name, ticket_id=ticket_id)
                    elif tool_name == "get_product_pricing":
                        facts[tool_name] = await tools.call(tool_name, sku=ticket["sku"])
                    else:
                        facts[tool_name] = await tools.call(tool_name)
                audit(label, "facts_collected", f"Collected MCP facts for ticket {ticket_id}", ticket_id=ticket_id)
                prompt = f"Ticket: {json.dumps(ticket)}\nMCP facts: {json.dumps(facts)}\nReturn a typed finding."
                result = await _agent(role, prompt_file, model).run(prompt)
                findings.append(result.output)
                audit(label, "finding", result.output.recommendation, ticket_id=ticket_id)

            boss_prompt = (ROOT / "backend" / "prompts" / "boss.md").read_text(encoding="utf-8")
            boss_prompt += f"\nTicket: {json.dumps(ticket)}\nSpecialist findings: {json.dumps([f.model_dump() for f in findings])}\nReturn the final decision."
            boss_result = await _agent("boss", "boss.md", model).run(boss_prompt)
            decision = TicketDecision(
                ticket_id=ticket_id,
                decision=boss_result.output.recommendation,
                required_actions=boss_result.output.actions,
                specialist_findings=findings,
                remaining_approval=("Human approval required" if boss_result.output.approval_required else None),
                customer_draft=boss_result.output.customer_draft,
            )
            audit("boss", "final_decision", decision.decision, ticket_id=ticket_id, stop_reason="completed")
            return decision

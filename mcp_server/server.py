"""FastMCP tools for the Campus Customs ticket database."""

from pathlib import Path
import sqlite3
from typing import Any

from mcp.server.fastmcp import FastMCP


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "campus_customs_new.db"
mcp = FastMCP("Campus Customs MCP")


def _ticket(ticket_id: int) -> dict[str, Any]:
    """Load a ticket, or fail instead of answering from invented context."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
    if row is None:
        raise ValueError(f"Ticket {ticket_id} was not found in the database.")
    return dict(row)


def _rows(sql: str, parameters: tuple[Any, ...]) -> list[dict[str, Any]]:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, parameters).fetchall()]


@mcp.tool()
def get_ticket_inventory(ticket_id: int) -> dict[str, Any]:
    """Return the database inventory rows for a product ticket's SKU and size."""
    ticket = _ticket(ticket_id)
    if not ticket["sku"]:
        return {"ticket": ticket, "inventory": []}
    inventory = _rows(
        """SELECT sku, name, size, qty, location
           FROM inventory
           WHERE sku = ? AND (? IS NULL OR size = ?)
           ORDER BY size""",
        (ticket["sku"], ticket["size"], ticket["size"]),
    )
    return {"ticket": ticket, "inventory": inventory}


@mcp.tool()
def get_ticket_invoice(ticket_id: int) -> dict[str, Any]:
    """Return the linked invoice and vendor details for an invoice-related ticket."""
    ticket = _ticket(ticket_id)
    if ticket["invoice_id"] is None:
        return {"ticket": ticket, "invoice": None, "vendor": None}
    rows = _rows(
        """SELECT i.id, i.vendor_id, i.amount, i.due_date, i.status,
                         i.description, v.name AS vendor_name,
                         v.specialty AS vendor_specialty, v.lead_days
                  FROM invoices AS i
                  JOIN vendors AS v ON v.id = i.vendor_id
                  WHERE i.id = ?""",
        (ticket["invoice_id"],),
    )
    return {"ticket": ticket, "invoice": rows[0] if rows else None}


@mcp.tool()
def get_ticket_lease(ticket_id: int) -> dict[str, Any]:
    """Return the linked lease details for a rent-related ticket."""
    ticket = _ticket(ticket_id)
    if ticket["lease_id"] is None:
        return {"ticket": ticket, "lease": None}
    rows = _rows(
        """SELECT id, space_name, landlord, monthly_rent, next_due, notes
           FROM leases WHERE id = ?""",
        (ticket["lease_id"],),
    )
    return {"ticket": ticket, "lease": rows[0] if rows else None}


@mcp.tool()
def get_shop_cash() -> list[dict[str, Any]]:
    """Return current cash accounts from the database for accounting review."""
    return _rows("SELECT name, balance, date FROM cash_accounts ORDER BY name", ())


@mcp.tool()
def get_product_pricing(sku: str) -> dict[str, Any] | None:
    """Return actual unit cost and list price for one SKU, or null if absent."""
    rows = _rows(
        "SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?", (sku,)
    )
    return rows[0] if rows else None


@mcp.tool()
def get_vendor_shipping_status() -> list[dict[str, Any]]:
    """Return vendors with lead times and their unpaid invoice exposure."""
    return _rows(
        """SELECT v.id, v.name, v.specialty, v.lead_days,
                  COALESCE(SUM(CASE WHEN i.status != 'paid' THEN i.amount ELSE 0 END), 0) AS unpaid_amount
           FROM vendors AS v
           LEFT JOIN invoices AS i ON i.vendor_id = v.id
           GROUP BY v.id, v.name, v.specialty, v.lead_days
           ORDER BY v.lead_days, v.id""",
        (),
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")

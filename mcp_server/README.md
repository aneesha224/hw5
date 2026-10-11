# Campus Customs MCP server

This FastMCP server gives later homework agents read-only tools for answering
Campus Customs ticket questions from the database. It uses the working copy
`data/campus_customs_new.db`; it does not use the original database and it does
not invent values.

## Tools

- `get_ticket_inventory(ticket_id)` reads `tickets` and `inventory` for a
  ticket's SKU and requested size. It supports product availability questions.
- `get_ticket_invoice(ticket_id)` reads `tickets`, `invoices`, and `vendors` to
  return the linked bill and supplier details.
- `get_ticket_lease(ticket_id)` reads `tickets` and `leases` to return the
  linked rental obligation.
- `get_shop_cash()` reads `cash_accounts` for current balances and dates.
- `get_product_pricing(sku)` reads `pricing` for actual unit cost and list price.
- `get_vendor_shipping_status()` reads `vendors` and `invoices` for lead times and unpaid invoice exposure.

The server is intentionally not started for Problem 3. When dependencies are
installed, run it from this homework folder with:

```bash
.venv/bin/python -m mcp_server.server
```

The PydanticAI team in `backend/team.py` connects to this server over stdio;
backend agents do not query SQLite directly. Its audit events are appended as
JSON Lines to `output/audit_trail.json`.

# Campus Customs Agent Harness — Homework 05

## Database overview

The working database is `data/campus_customs_new.db`, copied from the original
`data/campus_customs.db` before any later homework changes. The original is
preserved as the read-only reference copy for this project.

The database has nine tables. The main relationships are:

- `invoices.vendor_id` → `vendors.id`
- `tickets.lease_id` → `leases.id`
- `tickets.invoice_id` → `invoices.id`
- `tickets.sku` + `tickets.size` → `inventory.sku` + `inventory.size`
- `tickets.sku` → `pricing.sku`
- `payments.ref_id` is a polymorphic reference whose meaning is determined by `payments.kind`; it has no declared foreign key.

## Tables and fields

### `cash_accounts`

Tracks the shop's current cash-account balances so an agent can answer cash-position questions and check whether planned payments are affordable.

| Field | Type | Key/constraint | Why it matters |
|---|---|---|---|
| `name` | TEXT | Primary key | Identifies the account, such as checking. |
| `balance` | REAL | NOT NULL | Gives the agent the current available balance. |
| `date` | TEXT | NOT NULL | Shows when the balance was recorded. |

### `desk`

Stores shared operating context for the agent, including the current business date and staff notes.

| Field | Type | Key/constraint | Why it matters |
|---|---|---|---|
| `date_today` | TEXT | NOT NULL | Anchors due-date and urgency calculations. |
| `notes` | TEXT | — | Provides additional instructions or context for the agent. |

### `inventory`

Stores sellable stock by product and size so the agent can give accurate availability and location answers.

| Field | Type | Key/constraint | Why it matters |
|---|---|---|---|
| `sku` | TEXT | Part of primary key; NOT NULL | Identifies the product for joins with pricing and tickets. |
| `name` | TEXT | NOT NULL | Gives the customer-facing product name. |
| `size` | TEXT | Part of primary key; NOT NULL | Distinguishes stock variants. |
| `qty` | INTEGER | NOT NULL | Supplies the actual quantity available. |
| `location` | TEXT | NOT NULL | Tells staff where the item is stored. |

### `invoices`

Tracks amounts owed to vendors, allowing agents to explain invoice status, due dates, and vendor obligations.

| Field | Type | Key/constraint | Why it matters |
|---|---|---|---|
| `id` | INTEGER | Primary key | Identifies the invoice for tickets and payment workflows. |
| `vendor_id` | INTEGER | NOT NULL; foreign key to `vendors.id` | Links the bill to the responsible vendor. |
| `amount` | REAL | NOT NULL | States how much is owed. |
| `due_date` | TEXT | NOT NULL | Supports deadline and overdue checks. |
| `status` | TEXT | NOT NULL | Shows whether the invoice is open, paid, or otherwise handled. |
| `description` | TEXT | — | Explains what the invoice covers. |

### `leases`

Stores the shop's rental obligations so agents can answer rent notices and upcoming payment questions.

| Field | Type | Key/constraint | Why it matters |
|---|---|---|---|
| `id` | INTEGER | Primary key | Identifies a lease referenced by tickets. |
| `space_name` | TEXT | NOT NULL | Names the rented shop space. |
| `landlord` | TEXT | NOT NULL | Identifies who receives rent. |
| `monthly_rent` | REAL | NOT NULL | Gives the recurring rent amount. |
| `next_due` | TEXT | NOT NULL | Supports reminders and urgency calculations. |
| `notes` | TEXT | — | Holds lease-specific context. |

### `payments`

Provides an audit trail of outgoing payments so agents can report what was paid, from which account, and with whose approval.

| Field | Type | Key/constraint | Why it matters |
|---|---|---|---|
| `id` | INTEGER | Primary key | Identifies each payment. |
| `kind` | TEXT | NOT NULL | States what the payment refers to. |
| `ref_id` | INTEGER | — | Connects the payment to an invoice or other record according to `kind`. |
| `amount` | REAL | NOT NULL | Records the amount paid. |
| `account` | TEXT | NOT NULL | Identifies the account charged. |
| `paid_at` | TEXT | NOT NULL | Records when the payment occurred. |
| `approved_by` | TEXT | NOT NULL | Preserves approval accountability. |

### `pricing`

Stores product cost and selling price so agents can quote prices and reason about margins without inventing values.

| Field | Type | Key/constraint | Why it matters |
|---|---|---|---|
| `sku` | TEXT | Primary key | Identifies the product whose prices are being looked up. |
| `unit_cost` | REAL | NOT NULL | Shows the shop's cost per item. |
| `list_price` | REAL | NOT NULL | Supplies the customer-facing price. |

### `tickets`

Acts as the agent's work queue. Tickets combine customer or operational requests with product, lease, and invoice references.

| Field | Type | Key/constraint | Why it matters |
|---|---|---|---|
| `id` | INTEGER | Primary key | Identifies the request. |
| `type` | TEXT | NOT NULL | Tells the agent which workflow applies. |
| `requester` | TEXT | NOT NULL | Identifies who submitted the request. |
| `subject` | TEXT | NOT NULL | Summarizes the request for staff and the agent. |
| `sku` | TEXT | — | Links product-related work to `pricing` and `inventory`. |
| `size` | TEXT | — | Identifies the requested inventory variant with `sku`. |
| `qty` | INTEGER | — | Records requested quantity for orders or bulk requests. |
| `lease_id` | INTEGER | Foreign key to `leases.id` | Links rent notices to the relevant lease. |
| `invoice_id` | INTEGER | Foreign key to `invoices.id` | Links ticket work to a vendor invoice. |
| `status` | TEXT | NOT NULL | Shows whether the ticket still needs attention. |
| `notes` | TEXT | — | Contains details the agent needs to act accurately. |
| `created_at` | TEXT | NOT NULL | Establishes ticket age and ordering. |

### `vendors`

Maintains supplier capabilities and lead times so agents can route work and estimate reprint or fulfillment timing.

| Field | Type | Key/constraint | Why it matters |
|---|---|---|---|
| `id` | INTEGER | Primary key | Identifies the supplier referenced by invoices. |
| `name` | TEXT | NOT NULL | Gives the vendor's name. |
| `specialty` | TEXT | NOT NULL | Shows what the vendor can supply or service. |
| `lead_days` | INTEGER | NOT NULL | Supports delivery and planning estimates. |

## Open-ticket study

The database contains three open tickets:

1. Ticket `101` is a customer order for one `CC-TEE-WHITE` in size `S`. It points to invoice `501`; the matching inventory row has quantity `0`, and pricing lists the tee at `$28.00`. The invoice is for a rush reprint from vendor `1`.
2. Ticket `102` is a rent notice from Elm City Properties. Its `lease_id` is `1`, which links it to the Chapel Street shop lease with monthly rent of `$2,400.00` and a next due date of `2026-09-02`.
3. Ticket `103` is a bulk price-override request for 20 `CC-HOOD-NAVY` hoodies in size `M`. The matching inventory row has quantity `8`, and pricing lists the hoodie at `$58.00`; it has no lease or invoice link.

These examples show why ticket agents must combine ticket fields with the related inventory, pricing, lease, invoice, and vendor records before responding.

## MCP server tools — Problem 3

The server code lives in `mcp_server/server.py` and reads only
`data/campus_customs_new.db`. All three tools perform database reads; none
creates or guesses records.

| MCP tool | Tables read | Ticket unlocked | Why this is the right tool |
|---|---|---:|---|
| `get_ticket_inventory(ticket_id)` | `tickets`, `inventory` | 101 and 103 | Tickets 101 and 103 ask about specific SKU/size quantities, so this tool joins each ticket's product request to the actual stock row. |
| `get_ticket_invoice(ticket_id)` | `tickets`, `invoices`, `vendors` | 101 | Ticket 101 points to invoice 501 for the tee reprint, so this tool provides the bill amount, status, description, and responsible vendor. |
| `get_ticket_lease(ticket_id)` | `tickets`, `leases` | 102 | Ticket 102 is a rent notice with `lease_id = 1`, so this tool retrieves the shop space, landlord, rent, and next due date. |

The server's README is at `mcp_server/README.md`; it explains the database
file and how the three tools are intended to be used.

## Agent team — Problem 5

The PydanticAI team is in `backend/team.py`. The Boss delegates to specialists,
specialists receive facts collected from MCP, and the Boss produces the final
typed decision. No backend agent opens SQLite directly.

| Agent | Prompt | Responsibility | MCP tools used |
|---|---|---|---|
| Boss | `backend/prompts/boss.md` | Reads the ticket, delegates, gathers findings, and makes the final decision. | `get_ticket_inventory` (tickets, inventory); then specialist results from all MCP tools. |
| Inventory | `backend/prompts/inventory.md` | Exact SKU/size stock, shortage, vendor viability, lead time, and restock recommendation. | `get_ticket_inventory` (tickets, inventory); `get_vendor_shipping_status` (vendors, invoices); `get_product_pricing` (pricing). |
| Accounting | `backend/prompts/accounting.md` | Cash, invoice status, margins, and financially feasible proposed purchases/payments. | `get_shop_cash` (cash_accounts); `get_ticket_invoice` (tickets, invoices, vendors); `get_product_pricing` (pricing). |
| Facilities | `backend/prompts/facilities.md` | Lease, rent, due date, amount, and facilities escalation. | `get_ticket_lease` (tickets, leases). |
| Customer Service | `backend/prompts/customer_service.md` | Drafts a concise customer-facing message from confirmed facts; never sends it. | `get_ticket_inventory` (tickets, inventory); `get_ticket_invoice` (tickets, invoices, vendors). |

### Safety and loop limits

- MCP is the only shop-facts layer; agents cannot invent missing data or bypass it with direct database access.
- Payments require human approval, cash cannot go negative, and the team never contacts customers or vendors directly.
- The desk date, database vendor lead times, and unpaid-invoice shipping constraint are authoritative.
- Each ticket is capped at 5 specialist steps and 12 MCP calls; tool results and audit detail are capped to practical sizes.
- Every MCP call, fact-collection step, specialist finding, and final decision is appended to `output/audit_trail.json` as one JSON object per line. Existing events are never cleared.

## FastAPI backend routes — Problem 7

Run from `backend/` with `uvicorn main:app --reload --port 8000`.

| Route | Purpose |
|---|---|
| `GET /health` | Returns a simple backend health check. |
| `GET /tickets` | Returns tickets 101, 102, and 103 with their current open/resolved status. |
| `POST /tickets/{ticket_id}/run` | Runs the bounded PydanticAI agent team for one ticket and returns its typed decision. |
| `GET /events?limit=100` | Returns recent append-only agent/MCP audit events, including agent steps and tool calls. |
| `POST /approvals` | Applies a human-approved payment or purchase order to checking and records it in `payments`; rejects negative cash. |
| `GET /cash` | Returns the current checking balance and its recorded date. |
| `POST /reset` | Restores `data/campus_customs_new.db` from the preserved original `data/campus_customs.db`. |

## Resolution run — Problem 9

The working database was reset before the successful run. Starting checking
balance was `$3,400.00`. Tickets 101, 102, and 103 all finished with status
`resolved`; the detailed run evidence is in `output/resolved_tickets.json` and
the board snapshots are in `output/resolved_board.html`. No payment or
purchase was human-approved, so there were no `payments` rows and checking
ended at `$3,400.00`.

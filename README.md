# Campus Customs Multi-Agent Operations

Homework 05 is a small operations desk for the Campus Customs shop. It includes a FastMCP server, a PydanticAI team (Boss, Inventory, Accounting, Facilities, and Customer Service), a FastAPI backend, and a React/Vite dashboard.

## Requirements

- Python 3.11+ and Node.js
- A Portkey API key in a local `.env` file (copy `.env.example`; never commit `.env`)

The two SQLite files are included in `data/` so the project can run after cloning:

- `data/campus_customs.db` — preserved original
- `data/campus_customs_new.db` — working database

## Fresh run

Before a full three-ticket run, restore the working copy from the original:

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

The backend also exposes `POST http://localhost:8000/reset` for this reset.

## Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

Create `.env` at the project root from `.env.example`, then load it in the shell before starting the backend (for example with `set -a; source .env; set +a`).

## Start the services

Start the MCP server from the project root:

```bash
.venv/bin/python -m mcp_server.server
```

The MCP server is configured in `.mcp.json`; the backend starts its stdio MCP connection when it runs an agent team.

Start the FastAPI backend from `backend/`:

```bash
cd backend
../.venv/bin/uvicorn main:app --reload --port 8000
```

Start the React board in a second terminal:

```bash
cd frontend
npm run dev
```

Open the dashboard at `http://localhost:5173`. The backend is at `http://localhost:8000` and its interactive docs are at `/docs`.

## Dashboard workflow

1. Reset the database before a clean run.
2. Open the dashboard and select ticket 101, 102, or 103.
3. Click **Run agent team** and watch the activity feed and summaries.
4. Review any proposed financial action in the approval desk; agents never move cash without a human approval.
5. Use `output/desk_tickets.html` for the Expected/Actual plan, Cash tab, and Reflection tab. Resolution evidence is in `output/resolved_tickets.json`, `output/resolved_board.html`, and the append-only `output/audit_trail.json`.

## Project layout

See `output/harness.md` for the database schema, MCP tools, agent roles, API routes, dashboard behavior, safety rules, and token limits.

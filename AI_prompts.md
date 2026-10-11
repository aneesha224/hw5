# AI Prompts Log — Homework 05

A log of the prompts I typed to the AI assistant while working through the homework problems.

---

## Problem 1

> Add the prompts used for Problem 1 here as the homework progresses.

## Problem 2: Study the Campus Customs database

> Open data/campus_customs.db from the homework 5 folder. Look through every table and its fields. Copy the original file to data/campus_customs_new.db because later problems will udpate that working copy. Study the 3 open tickets so you can see how they link to other tables. Start output/harness.md. For each table, list the fields and one short line on why that table matters for the agents. You will keep growing this harness file in later problems

## Problem 3: Build the MCP server

> Write an MCP server in mcp_server/ using FastMCP. It will talk to data/campus_customs_new.db. You do not need to connect or run it in this problem. Every agent in this homework uses the tools in this MCP server. You will add more tools to it later. For now write 3 tools you know you will need for the tickets in the database. Keep the names clear. Never invent any data, only use information in the database. In output/harness.md, list each of your three MCP tools. For every tool include: which table it reads, which ticket it helps unlock (101, 102, 103) and one sentence on why that tool is the right one for that ticket. Vague lines like "reads inventory: score low - tie the tool to the ticket. Also add a short mcp_server/README.md file that explains what the MCP server is for, which database file it uses, adn the 3 tools it has

## Problem 4: Add the MCP server to vibe coder and test each tool

> Add the MCP server to this project so the vibe coder can call the tools. Save the connection JSON text in .mcp.json at the project root (or however yuo save local MCP server lists). When you are connected, test each of the 3 MCP tools. Save the evidence in output/mcp_smoke.json. For every tool include the prompt you asked the vibe coder, the tool name, and the tool output (must match values in data/campus_customs_new.db).

## Problem 5: Build the agent team and grow the MCP tools

> Build the agentic team for Campus Customs using PydanticAI: Boss, Inventory, Accounting, Facilities, and Customer Service. Include prompts, models, and agent loops so they can delegate work to each other with full connectivity. Put the agent prompts in backend/prompts/ with one file per agent. Put data types in backend/models.py, and the agent files under backend/. Add any tools the agents need to your MCP server so they can work on the open tickets. Shop facts come from the MCP server over data/campus_customs_new.db — do not invent a second shop-tools layer that bypasses MCP. Wire the agents so they append to output/audit_trail.json as they run. In output/harness.md, list each agent and each MCP tool along with which table the tool uses, and add safety guardrails and token limits. Update mcp_server/README.md so the tool list matches.

## Problem 6: Plan the three tickets

> Before you wire the backend, we need to write down what you expect the team to do on each open ticket. Build output/desk_tickets.html - a page a user can double-click with one tab per ticket (101, 102, 103). Also add empty Cash and Reflection tabs for later problems. Leave them blank for now. On each ticket tab, fill an Expected section only. Leave room for an Actual section you will fill after you run the agents. For each ticket's Expected section, write who the Boss should first and why, all the agent delegations you expect, and which MCP tools you expect that run to use. The plan should NOT send every specialist on every ticket.

## Problem 7: Backend routes

> In backend/main.py, use FastAPI and add routes to return the three tickets and open/resolved status; run the agent team for a ticket; return recent agent events, agent messages, and tools used; approve a human-approved payment or purchase; return the checking balance; and reset the working database to original values. Run with `uvicorn main:app --reload --port 8000`, document each route in output/harness.md, and test everything from Problems 2-7.

## Problem 8: Agent dashboard

> Build the frontend dashboard in frontend/ with React + Vite + TypeScript. The page should call the backend routes at http://localhost:8000, list all three tickets, let a human select and run one, show each agent's activity and summary, mark completed tickets resolved, support human payment approval, and show checking balance changes. Make it minimalistic, easy to use, and use shades of blue and green. Add output/design.md explaining the layout, agent readability, resolved state, cash display, and creative human-centered choices. Start it with `npm run dev`.

## Problem 9: Resolve the tickets

> Reset data/campus_customs_new.db, note the starting checking balance, run tickets 101, 102, and 103 until resolved, fill the Actual sections in output/desk_tickets.html, itemize cash on the Cash tab, save output/resolved_tickets.json and output/resolved_board.html, append real runs to output/audit_trail.json, and finish output/harness.md.

## Problem 10: Reflection

> Update the Reflection tab in output/desk_tickets.html with brief but detailed answers tied to the Campus Customs app, tickets 101–103, the Expected and Actual ticket tabs, and the Cash tab. Evaluate agent performance, compare Actual to Expected, explain what could be simpler as one agent with tools, identify three solvable and three currently unsolvable Campus Customs problems, and name the missing tools/agents for the unsolvable problems.

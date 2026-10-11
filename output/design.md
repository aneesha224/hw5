# Campus Customs dashboard design

## Direction

The dashboard is intentionally minimal: a quiet operations desk rather than a dense admin console. A deep blue-to-green header gives the product a calm, trustworthy foundation, while green marks healthy operational progress and cash. Warm amber and muted coral are reserved for attention and role distinction.

## Layout

- A left ticket rail keeps all three tickets visible and makes selection one click.
- The main workspace starts with the selected ticket and one primary “Start agent team” action.
- A live activity panel shows the latest audit events as they arrive.
- A compact team panel keeps every role visible without implying that every specialist is active on every ticket.
- The lower row separates the run summary from the human approval desk.

## Agent readability

Each role has a consistent colored circular mark and a short label. The activity stream shows the agent, action, and plain-language detail. The team panel dims standby agents and brightens agents seen in the selected ticket's events, making the delegation pattern easy to understand at a glance.

## Resolution and cash

Ticket cards use a small status pill: amber for open and green for resolved. When a successful agent run finishes, the backend persists the ticket as resolved and the dashboard refreshes the board. Cash is always visible in the header. Approval is visually separate and labeled “Human only”; after an approved payment, the dashboard refreshes the checking balance so the decrease is immediately apparent.

## Human-centered details

The interface uses generous spacing, restrained shadows, short labels, and progressive detail. The empty state tells the operator what action to take next, while the live pulse provides feedback during a run. Responsive layouts keep the ticket rail and approval control usable on a smaller screen. The design avoids decorative noise so a human operator can understand the state of a ticket in seconds.

import { useCallback, useEffect, useMemo, useState } from 'react'

const API = 'http://localhost:8000'
type Ticket = { id: number; type: string; requester: string; subject: string; status: string; created_at: string }
type Event = { agent: string; step: string; detail: string; time?: string; ticket_id?: number; arguments?: Record<string, unknown> }
type Finding = { agent: string; facts: string[]; actions: string[]; recommendation: string; approval_required: boolean; missing_information: string[]; customer_draft?: string | null }
type Decision = { decision: string; required_actions: string[]; specialist_findings: Finding[]; remaining_approval?: string | null; customer_draft?: string | null }

const labels: Record<string, string> = { boss: 'Boss', inventory: 'Inventory', accounting: 'Accounting', facilities: 'Facilities', customer_service: 'Customer Service', mcp: 'MCP relay' }
const icons: Record<string, string> = { boss: '◆', inventory: '▦', accounting: '$', facilities: '⌂', customer_service: '✦', mcp: '↗' }

async function get<T>(path: string): Promise<T> { const response = await fetch(`${API}${path}`); if (!response.ok) throw new Error(await response.text()); return response.json() }
async function post<T>(path: string, body?: unknown): Promise<T> { const response = await fetch(`${API}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined }); if (!response.ok) throw new Error(await response.text()); return response.json() }

function App() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [selected, setSelected] = useState<number>(101)
  const [events, setEvents] = useState<Event[]>([])
  const [decision, setDecision] = useState<Decision | null>(null)
  const [cash, setCash] = useState<number | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [approvalAmount, setApprovalAmount] = useState('')

  const refresh = useCallback(async () => { try { const [newTickets, newEvents, balance] = await Promise.all([get<Ticket[]>('/tickets'), get<Event[]>('/events?limit=80'), get<{ balance: number }>('/cash')]); setTickets(newTickets); setEvents(newEvents); setCash(balance.balance); setError('') } catch (e) { setError(e instanceof Error ? e.message : 'Could not reach the desk API') } }, [])
  useEffect(() => { refresh() }, [refresh])
  useEffect(() => { if (!running) return; const timer = window.setInterval(refresh, 900); return () => window.clearInterval(timer) }, [running, refresh])
  const ticket = tickets.find(item => item.id === selected)
  const ticketEvents = useMemo(() => events.filter(event => event.ticket_id === selected || event.step === 'initialized'), [events, selected])
  const activeAgents = useMemo(() => [...new Set(ticketEvents.map(event => event.agent))], [ticketEvents])

  async function runTicket() { setRunning(true); setDecision(null); setError(''); try { const result = await post<Decision>(`/tickets/${selected}/run`); setDecision(result); await refresh() } catch (e) { setError(e instanceof Error ? e.message : 'The team could not run') } finally { setRunning(false) } }
  async function approve() { const amount = Number(approvalAmount); if (!amount || amount <= 0) return; try { await post('/approvals', { kind: 'payment', amount, approved_by: 'Desk operator' }); setApprovalAmount(''); await refresh() } catch (e) { setError(e instanceof Error ? e.message : 'Approval failed') } }

  return <div className="app-shell">
    <header className="topbar"><div><div className="eyebrow">CAMPUS CUSTOMS</div><h1>Operations Desk</h1></div><div className="cash-card"><span>CHECKING BALANCE</span><strong>{cash === null ? '—' : `$${cash.toLocaleString()}`}</strong><small>Updated from live data</small></div></header>
    {error && <div className="alert">{error}</div>}
    <div className="kpi-strip"><div><span>OPEN TICKETS</span><strong>{tickets.filter(item => item.status === 'open').length}</strong></div><div><span>RESOLVED</span><strong className="good">{tickets.filter(item => item.status === 'resolved').length}</strong></div><div><span>TEAM STATUS</span><strong className={running ? 'working' : 'ready'}>{running ? 'Working' : 'Ready'}</strong></div></div>
    <main className="layout">
      <aside className="ticket-rail"><div className="section-label">TICKETS <span>{tickets.length}</span></div>{tickets.map(item => <button className={`ticket-card ${item.id === selected ? 'selected' : ''}`} onClick={() => { setSelected(item.id); setDecision(null) }} key={item.id}><div className="ticket-top"><span>#{item.id}</span><span className={`status ${item.status}`}>{item.status === 'resolved' ? 'Resolved ✓' : 'Open'}</span></div><strong>{item.subject}</strong><small>{item.requester} · {item.type.replace('_', ' ')}</small></button>)}</aside>
      <section className="workspace"><div className="workspace-head"><div><div className="section-label">TICKET DETAILS</div><h2>{ticket?.subject || 'Loading ticket…'}</h2><p>{ticket ? `${ticket.requester} · Ticket #${ticket.id}` : ''}</p></div>{ticket?.status === 'resolved' ? <span className="resolved-badge">RESOLVED ✓</span> : <button className="run-button" disabled={running || !ticket} onClick={runTicket}>{running ? 'Running team…' : 'Run agent team'}</button>}</div>
        <div className="activity-grid"><div className="panel activity-panel"><div className="panel-title"><span>LIVE ACTIVITY</span><span className={running ? 'pulse' : 'quiet'}>{running ? '● RUNNING' : '● READY'}</span></div>{ticketEvents.length ? <div className="event-list">{ticketEvents.slice(-12).reverse().map((event, index) => <div className="event" key={`${event.time}-${index}`}><div className={`agent-dot ${event.agent}`}>{icons[event.agent] || '·'}</div><div><strong>{labels[event.agent] || event.agent}</strong><p>{event.detail}</p><small>{event.step.replace('_', ' ')}</small></div></div>)}</div> : <div className="empty">Start the team to see the desk light up.</div>}</div>
          <div className="panel agents-panel"><div className="panel-title"><span>THE TEAM</span><span>{activeAgents.length}/5 active</span></div><div className="agent-list">{['boss', 'inventory', 'accounting', 'facilities', 'customer_service'].map(agent => <div className={`agent-row ${activeAgents.includes(agent) ? 'active' : ''}`} key={agent}><span className={`agent-dot ${agent}`}>{icons[agent]}</span><div><strong>{labels[agent]}</strong><small>{agent === 'boss' ? 'Routes & decides' : agent === 'customer_service' ? 'Drafts messages' : `Checks ${agent} facts`}</small></div><span className="agent-state">{activeAgents.includes(agent) ? 'working' : 'standby'}</span></div>)}</div></div></div>
        <div className="lower-grid"><div className="panel summary-panel"><div className="panel-title"><span>RUN SUMMARY</span><span>{decision ? 'COMPLETE' : 'AWAITING RUN'}</span></div>{decision ? <><h3>{decision.decision}</h3>{decision.specialist_findings.map(finding => <div className="finding" key={finding.agent}><strong>{labels[finding.agent] || finding.agent}</strong><p>{finding.recommendation}</p>{finding.actions.length > 0 && <small>Next: {finding.actions.join(' · ')}</small>}</div>)}</> : <div className="empty">Each agent’s short report will appear here after the run.</div>}</div><div className="panel approval-panel"><div className="panel-title"><span>APPROVAL DESK</span><span>HUMAN ONLY</span></div><p>Agents can prepare a payment. You decide whether it moves cash.</p><div className="approval-form"><span>$</span><input aria-label="Payment amount" type="number" min="0" placeholder="Amount" value={approvalAmount} onChange={event => setApprovalAmount(event.target.value)} /><button onClick={approve} disabled={!approvalAmount}>Approve pay</button></div><small>Checking balance updates immediately after approval.</small></div></div>
      </section>
    </main>
  </div>
}

export default App

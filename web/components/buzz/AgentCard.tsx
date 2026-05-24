"use client"
import type { SessionStatus, WorkflowEvent } from "@/lib/types"

const AGENT_COLORS: Record<string, string> = {
  Lead:       "var(--amber)",
  Researcher: "var(--cyan)",
  Analyst:    "var(--violet)",
  Reporter:   "var(--green)",
}

interface AgentCardProps {
  agentKey: string
  label: string
  events: WorkflowEvent[]
  sessionStatus: SessionStatus
  failedAgent: string | null
}

export function AgentCard({ agentKey, label, events, sessionStatus, failedAgent }: AgentCardProps) {
  const color = AGENT_COLORS[agentKey] ?? "var(--text-md)"
  const started = events.some(e => e.source === agentKey && e.event_type === "agent_start")
  const ended = events.some(e => e.source === agentKey && e.event_type === "agent_end")
  const isRunning = started && !ended && sessionStatus === "running"
  const isError = failedAgent === agentKey && sessionStatus === "error"
  const lastEvent = events.filter(e => e.source === agentKey).at(-1)
  const cardBg = isError ? "color-mix(in oklch, var(--red) 12%, var(--surface))" : "var(--surface)"

  return (
    <div style={{ background: cardBg, border: `1px solid ${isRunning ? color : "var(--border)"}`, borderRadius: 2, padding: "10px 12px", marginBottom: 4 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
        <div style={{ width: 6, height: 6, borderRadius: "50%", background: color, opacity: isRunning ? 1 : 0.4 }} />
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.12em", color, fontWeight: 600 }}>{label}</span>
        <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-lo)" }}>— tokens</span>
      </div>
      {lastEvent && (
        <div style={{ fontFamily: "var(--font-sans)", fontSize: 11, color: "var(--text-md)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          ↳ {lastEvent.message}
        </div>
      )}
      {isRunning && (
        <div style={{ marginTop: 6, height: 2, background: "var(--border)", borderRadius: 1, overflow: "hidden" }}>
          <div style={{ height: "100%", width: "40%", background: color, animation: "buzz-pulse 1.4s ease-in-out infinite" }} />
        </div>
      )}
    </div>
  )
}

"use client"
import type { WorkflowEvent } from "@/lib/types"

const AGENT_COLORS: Record<string, string> = {
  Lead:       "var(--amber)",
  Researcher: "var(--cyan)",
  Analyst:    "var(--violet)",
  Reporter:   "var(--green)",
}

interface EventLogProps {
  events: WorkflowEvent[]
}

function formatTime(ts: string): string {
  try { return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) }
  catch { return ts }
}

export function EventLog({ events }: EventLogProps) {
  const visible = events.slice(-10)
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.18em", color: "var(--text-lo)" }}>EVENT LOG</div>
      <div style={{ flex: 1, overflowY: "auto", padding: "8px 12px" }}>
        {visible.length === 0 && (
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-lo)", opacity: 0.5, padding: "8px 0" }}>Waiting for events…</div>
        )}
        {visible.map((ev, i) => {
          const opacity = 0.4 + (i / visible.length) * 0.6
          const color = AGENT_COLORS[ev.source] ?? "var(--text-md)"
          return (
            <div key={i} style={{ opacity, marginBottom: 8 }}>
              <div style={{ display: "flex", gap: 8, marginBottom: 2 }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-lo)" }}>{formatTime(ev.timestamp)}</span>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color, letterSpacing: "0.10em" }}>{ev.source}</span>
              </div>
              <div style={{ fontFamily: "var(--font-sans)", fontSize: 11, color: "var(--text-md)", lineHeight: 1.4 }}>{ev.message}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

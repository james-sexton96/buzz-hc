"use client"
import type { SessionStatus, WorkflowEvent } from "@/lib/types"

export const PIPELINE_STAGES = [
  { key: "Lead",       label: "LEAD",     glyph: "·" },
  { key: "Researcher", label: "RESEARCH", glyph: "·" },
  { key: "Analyst",    label: "ANALYST",  glyph: "·" },
  { key: "Reporter",   label: "REPORT",   glyph: "·" },
  { key: "Synthesis",  label: "SYNTH",    glyph: "·" },
] as const

type StageState = "complete" | "running" | "error" | "paused" | "queued"

function deriveStageState(
  stageKey: string,
  events: WorkflowEvent[],
  status: SessionStatus,
  failedAgent: string | null
): StageState {
  // Lead is complete if ANY events exist (or session is running/complete/error)
  if (stageKey === "Lead") {
    if (status === "running" || status === "complete" || status === "error") return "complete"
    return "queued"
  }
  const started = events.some(e => e.source === stageKey && e.event_type === "agent_start")
  const ended = events.some(e => e.source === stageKey && e.event_type === "agent_end")
  if (ended || status === "complete") return "complete"
  if (status === "error" && failedAgent === stageKey) return "error"
  if (status === "paused" && started && !ended) return "paused"
  if (started && !ended) return "running"
  return "queued"
}

function deriveFailedAgent(events: WorkflowEvent[]): string | null {
  const starts = events.filter(e => e.event_type === "agent_start").map(e => e.source)
  const ends = new Set(events.filter(e => e.event_type === "agent_end").map(e => e.source))
  for (let i = starts.length - 1; i >= 0; i--) {
    if (!ends.has(starts[i])) return starts[i]
  }
  return null
}

interface PipelineStripProps {
  events: WorkflowEvent[]
  status: SessionStatus
}

const STATE_STYLES: Record<StageState, { border: string; color: string; glyph: string }> = {
  complete: { border: "var(--green)",   color: "var(--green)",   glyph: "✓" },
  running:  { border: "var(--cyan)",    color: "var(--cyan)",    glyph: "↻" },
  error:    { border: "var(--red)",     color: "var(--red)",     glyph: "✕" },
  paused:   { border: "var(--amber)",   color: "var(--amber)",   glyph: "⏸" },
  queued:   { border: "var(--border)",  color: "var(--text-lo)", glyph: "·" },
}

export function PipelineStrip({ events, status }: PipelineStripProps) {
  const failedAgent = status === "error" ? deriveFailedAgent(events) : null
  return (
    <div style={{ display: "flex", gap: 4, padding: "8px 16px", borderBottom: "1px solid var(--border)", background: "var(--surface)" }}>
      {PIPELINE_STAGES.map(stage => {
        const state = deriveStageState(stage.key, events, status, failedAgent)
        const s = STATE_STYLES[state]
        return (
          <div key={stage.key} style={{ flex: 1, borderTop: `2px solid ${s.border}`, padding: "6px 8px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.14em", color: s.color }}>{s.glyph} {stage.label}</div>
          </div>
        )
      })}
    </div>
  )
}

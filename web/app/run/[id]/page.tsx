"use client"
import { useParams, useRouter } from "next/navigation"
import { useLiveSession } from "@/hooks/useLiveSession"
import { retrySession } from "@/lib/api"
import { TopNav } from "@/components/buzz/TopNav"
import { StatusChip } from "@/components/buzz/StatusChip"
import { KV } from "@/components/buzz/KV"
import { PipelineStrip } from "@/components/buzz/PipelineStrip"
import { SwarmTopology } from "@/components/buzz/SwarmTopology"
import { AgentCard } from "@/components/buzz/AgentCard"
import { EventLog } from "@/components/buzz/EventLog"
import { StreamingDraft } from "@/components/buzz/StreamingDraft"
import { SectionLabel } from "@/components/buzz/SectionLabel"
import type { SessionStatus, WorkflowEvent } from "@/lib/types"

const AGENT_DEFS = [
  { key: "Lead",       label: "LEAD"        },
  { key: "Researcher", label: "RESEARCHER"  },
  { key: "Analyst",    label: "ANALYST"     },
  { key: "Reporter",   label: "REPORTER"    },
]

function deriveFailedAgent(events: WorkflowEvent[]): string | null {
  const starts = events.filter(e => e.event_type === "agent_start").map(e => e.source)
  const ends = new Set(events.filter(e => e.event_type === "agent_end").map(e => e.source))
  for (let i = starts.length - 1; i >= 0; i--) {
    if (!ends.has(starts[i])) return starts[i]
  }
  return null
}

function elapsed(ts: string): string {
  try {
    const s = Math.round((Date.now() - new Date(ts).getTime()) / 1000)
    if (s < 60) return `${s}s`
    return `${Math.floor(s / 60)}m ${s % 60}s`
  } catch { return "—" }
}

export default function RunDetailPage() {
  const params = useParams<{ id: string }>()
  const sessionId = params.id
  const router = useRouter()
  const { session, liveEvents, isLoading, error, draftText } = useLiveSession(sessionId)

  if (isLoading) {
    return (
      <>
        <TopNav />
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "60vh", fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-lo)" }}>Loading…</div>
      </>
    )
  }

  if (error || !session) {
    return (
      <>
        <TopNav />
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "60vh", fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-lo)" }}>Session not found</div>
      </>
    )
  }

  const allEvents: WorkflowEvent[] = [...(session.events ?? []), ...liveEvents]
  const failedAgent = session.status === "error" ? deriveFailedAgent(allEvents) : null
  const totalTokens = (session.usage as { total_tokens?: number })?.total_tokens ?? 0

  async function handleRetry() {
    try {
      const { session_id } = await retrySession(sessionId)
      router.push("/run/" + session_id)
    } catch { /* ignore */ }
  }

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--text-hi)" }}>
      <TopNav />

      {/* Header bar */}
      <div style={{ padding: "12px 16px", background: "var(--surface)", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)", letterSpacing: "0.12em" }}>{sessionId.slice(0, 8).toUpperCase()}</span>
        <span style={{ flex: 1, fontFamily: "var(--font-sans)", fontSize: 13, color: "var(--text-hi)", fontWeight: 500, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{session.query}</span>
        <div style={{ display: "flex", gap: 16 }}>
          <KV k="ELAPSED" v={elapsed(session.timestamp)} />
          <KV k="ETA" v="—" />
          <KV k="AGENTS" v="4" />
          <KV k="TOKENS" v={totalTokens > 0 ? String(totalTokens) : "—"} />
        </div>
        <StatusChip status={session.status as SessionStatus} />
        {session.status === "complete" && (
          <button onClick={() => router.push("/report/" + sessionId)}
            style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--amber)", background: "none", border: "1px solid var(--amber)", padding: "4px 10px", cursor: "pointer", letterSpacing: "0.12em" }}>
            ↗ OPEN REPORT
          </button>
        )}
        <button disabled style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)", background: "none", border: "1px solid var(--border)", padding: "4px 10px", cursor: "not-allowed", letterSpacing: "0.12em", opacity: 0.5 }}>
          {session.status === "paused" ? "▸ RESUME" : "⏸ PAUSE"}
        </button>
      </div>

      {/* Pipeline strip */}
      <PipelineStrip events={allEvents} status={session.status} />

      {/* Error banner */}
      {session.status === "error" && (
        <div style={{ margin: "12px 16px", padding: "12px 16px", background: "color-mix(in oklch, var(--red) 12%, var(--bg))", border: "1px solid var(--red)", display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--red)", letterSpacing: "0.12em" }}>PIPELINE ERROR{failedAgent ? ` · ${failedAgent.toUpperCase()}` : ""}</span>
          <span style={{ flex: 1, fontFamily: "var(--font-sans)", fontSize: 12, color: "var(--text-md)" }}>{session.error_msg ?? "An error occurred"}</span>
          <button onClick={handleRetry}
            style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--red)", background: "none", border: "1px solid var(--red)", padding: "4px 10px", cursor: "pointer", letterSpacing: "0.12em" }}>
            ↻ RETRY STAGE
          </button>
        </div>
      )}

      {/* Paused banner */}
      {session.status === "paused" && (
        <div style={{ margin: "12px 16px", padding: "12px 16px", background: "color-mix(in oklch, var(--amber) 10%, var(--bg))", border: "1px solid var(--amber)" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--amber)", letterSpacing: "0.12em" }}>PIPELINE PAUSED</span>
        </div>
      )}

      {/* 3-column body */}
      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr 360px", gap: 0, minHeight: "calc(100vh - 140px)" }}>
        {/* Left: Agent cards */}
        <div style={{ borderRight: "1px solid var(--border)", padding: "12px 12px" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.18em", color: "var(--text-lo)", marginBottom: 8 }}>AGENTS</div>
          {AGENT_DEFS.map(a => (
            <AgentCard key={a.key} agentKey={a.key} label={a.label} events={allEvents} sessionStatus={session.status} failedAgent={failedAgent} />
          ))}
        </div>

        {/* Center: SwarmTopology + live StreamingDraft (Part 4) */}
        <div style={{ borderRight: "1px solid var(--border)", display: "flex", flexDirection: "column", gap: 12, padding: "16px 14px", minHeight: 0 }}>
          <div style={{ display: "flex", justifyContent: "center" }}>
            <SwarmTopology status={session.status} width={420} height={260} />
          </div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 2px" }}>
            <SectionLabel
              accent={
                session.status === "running" ? "var(--cyan)" :
                session.status === "paused"  ? "var(--amber)" :
                session.status === "error"   ? "var(--red)" :
                session.status === "complete" ? "var(--green)" :
                "var(--text-lo)"
              }
            >
              {session.status === "running"  ? "↻ streaming…" :
               session.status === "paused"   ? "⏸ paused" :
               session.status === "complete" ? "✓ finalized" :
               session.status === "error"    ? "✕ truncated" :
                                                "· idle"}
            </SectionLabel>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-lo)", letterSpacing: "0.14em" }}>
              {draftText.length > 0 ? `${draftText.length} CHARS` : ""}
            </span>
          </div>
          <div style={{ flex: 1, minHeight: 180, display: "flex" }}>
            <StreamingDraft draftText={draftText} status={session.status as SessionStatus} />
          </div>
        </div>

        {/* Right: EventLog */}
        <div style={{ display: "flex", flexDirection: "column" }}>
          <EventLog events={allEvents} />
        </div>
      </div>
    </div>
  )
}

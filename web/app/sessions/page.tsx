"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { TopNav } from "@/components/buzz/TopNav";
import { SectionLabel } from "@/components/buzz/SectionLabel";
import { StatusDot } from "@/components/buzz/StatusDot";
import { Btn } from "@/components/buzz/Btn";
import { getSessions } from "@/lib/api";
import type { SessionSummary, SessionStatus } from "@/lib/types";
import Link from "next/link";

const GRID = "94px 1fr 80px 110px 110px 110px 90px 100px 80px";

const STATUS_COLOR: Record<SessionStatus, string> = {
  running:  "var(--cyan)",
  complete: "var(--green)",
  error:    "var(--red)",
  queued:   "var(--text-lo)",
  paused:   "var(--amber)",
};

const STATUS_LABEL: Record<SessionStatus, string> = {
  running:  "RUN",
  complete: "DONE",
  error:    "ERR",
  queued:   "QUE",
  paused:   "PSE",
};

function StatusCell({ status }: { status: SessionStatus }) {
  const c = STATUS_COLOR[status] ?? "var(--text-lo)";
  const label = STATUS_LABEL[status] ?? status.toUpperCase();
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <StatusDot status={status} pulse={status === "running"} />
      <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: c, letterSpacing: "0.14em", fontWeight: 600 }}>{label}</span>
    </div>
  );
}

type FilterKey = "all" | SessionStatus;

const FILTER_OPTIONS: { key: FilterKey; label: string }[] = [
  { key: "all",      label: "All" },
  { key: "running",  label: "Running" },
  { key: "complete", label: "Complete" },
  { key: "queued",   label: "Queued" },
  { key: "error",    label: "Error" },
];

const STATS_CONFIG = [
  { l: "Total runs",    v: "—", sub: "all-time" },
  { l: "This week",     v: "—", sub: "—" },
  { l: "Avg duration",  v: "—", sub: "min:sec p50" },
  { l: "Tokens (24h)",  v: "—", sub: "ctx avg —" },
  { l: "Cost (24h)",    v: "—", sub: "$— / run" },
  { l: "Success rate",  v: "—", sub: "— errors / 30d" },
];

function fmtDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
  } catch {
    return "—";
  }
}

export default function SessionsPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [filter, setFilter] = useState<FilterKey>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSessions().then(data => {
      setSessions(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const counts: Record<FilterKey, number> = {
    all:      sessions.length,
    running:  sessions.filter(s => s.status === "running").length,
    complete: sessions.filter(s => s.status === "complete").length,
    queued:   sessions.filter(s => s.status === "queued").length,
    error:    sessions.filter(s => s.status === "error").length,
    paused:   sessions.filter(s => s.status === "paused").length,
  };

  const filtered = filter === "all" ? sessions : sessions.filter(s => s.status === filter);

  const onRow = (s: SessionSummary) => {
    if (s.status === "complete") {
      router.push("/report/" + s.session_id);
    } else {
      router.push("/run/" + s.session_id);
    }
  };

  return (
    <div style={{
      background: "var(--bg)", color: "var(--text-hi)",
      fontFamily: "var(--font-sans)",
      display: "flex", flexDirection: "column", minHeight: "100vh",
    }}>
      <TopNav />

      {/* Page header */}
      <div style={{
        padding: "28px 32px 20px",
        borderBottom: "1px solid var(--border)",
        display: "flex", alignItems: "flex-end", gap: 28,
      }}>
        <div style={{ flex: 1 }}>
          <SectionLabel>History · all-time</SectionLabel>
          <h1 style={{ fontSize: 38, fontWeight: 600, letterSpacing: "-0.02em", margin: "8px 0 0 0" }}>Sessions</h1>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Btn>Export CSV</Btn>
          <Link href="/query"><Btn primary>+ New Run</Btn></Link>
        </div>
      </div>

      {/* Stats bar */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", borderBottom: "1px solid var(--border)" }}>
        {STATS_CONFIG.map((s, i) => (
          <div key={i} style={{
            padding: "16px 20px",
            borderRight: i < 5 ? "1px solid var(--border)" : "none",
            display: "flex", flexDirection: "column", gap: 4,
          }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-lo)", letterSpacing: "0.16em", textTransform: "uppercase" }}>{s.l}</div>
            <div style={{ fontSize: 24, fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>{s.v}</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-md)" }}>{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{
        padding: "14px 32px",
        borderBottom: "1px solid var(--border)",
        display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap",
      }}>
        <div style={{ display: "flex", gap: 6, flex: 1 }}>
          {FILTER_OPTIONS.map(({ key, label }) => {
            const active = filter === key;
            const count = counts[key] ?? 0;
            return (
              <button
                key={key}
                onClick={() => setFilter(key)}
                style={{
                  display: "inline-flex", alignItems: "center", gap: 6,
                  padding: "5px 10px",
                  background: active ? "var(--amber)" : "transparent",
                  color: active ? "#0a0d14" : "var(--text-md)",
                  border: active ? "1px solid var(--amber)" : "1px solid var(--border)",
                  borderRadius: 2,
                  fontFamily: "var(--font-mono)", fontSize: 10,
                  letterSpacing: "0.12em", textTransform: "uppercase",
                  cursor: "pointer",
                }}
              >
                {label}
                <span style={{ color: active ? "rgba(0,0,0,0.6)" : "var(--text-lo)", fontVariantNumeric: "tabular-nums" }}>{count}</span>
              </button>
            );
          })}
        </div>
        <div style={{
          display: "flex", alignItems: "center", gap: 8,
          border: "1px solid var(--border)", padding: "4px 10px",
          borderRadius: 2, minWidth: 280,
        }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-lo)" }}>⌕</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-md)" }}>Search queries, IDs, sources…</span>
          <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: 10, padding: "1px 5px", border: "1px solid var(--border)", color: "var(--text-lo)", borderRadius: 2 }}>⌘K</span>
        </div>
      </div>

      {/* Table */}
      <div style={{ flex: 1 }}>
        {/* Header row */}
        <div style={{
          display: "grid", gridTemplateColumns: GRID,
          padding: "10px 32px",
          borderBottom: "1px solid var(--border)",
          background: "var(--surface)",
          fontFamily: "var(--font-mono)", fontSize: 9,
          color: "var(--text-lo)", letterSpacing: "0.16em", textTransform: "uppercase",
        }}>
          <span>ID</span>
          <span>Query</span>
          <span>Status</span>
          <span>Started</span>
          <span>Duration</span>
          <span style={{ textAlign: "right" }}>Tokens</span>
          <span style={{ textAlign: "right" }}>Sources</span>
          <span style={{ textAlign: "right" }}>Cost</span>
          <span style={{ textAlign: "center" }}>Agents</span>
        </div>

        {loading && (
          <div style={{ padding: "32px", fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-lo)" }}>
            Loading sessions…
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <div style={{ padding: "32px", fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-lo)" }}>
            No sessions found.
          </div>
        )}

        {filtered.map((s, i) => (
          <div
            key={s.session_id}
            onClick={() => onRow(s)}
            style={{
              display: "grid", gridTemplateColumns: GRID,
              padding: "12px 32px",
              borderBottom: i < filtered.length - 1 ? "1px solid var(--border)" : "none",
              alignItems: "center", cursor: "pointer",
              background:
                s.status === "running" ? "rgba(34, 211, 238, 0.04)" :
                s.status === "error"   ? "rgba(239, 68, 68, 0.04)"  :
                "transparent",
              transition: "background 0.12s",
            }}
            onMouseEnter={e => { e.currentTarget.style.background = "rgba(245, 158, 11, 0.05)"; }}
            onMouseLeave={e => {
              e.currentTarget.style.background =
                s.status === "running" ? "rgba(34, 211, 238, 0.04)" :
                s.status === "error"   ? "rgba(239, 68, 68, 0.04)"  :
                "transparent";
            }}
          >
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--amber)", fontWeight: 600 }}>
              {s.session_id.slice(0, 8).toUpperCase()}
            </span>

            <div style={{ minWidth: 0, paddingRight: 16 }}>
              <div style={{ fontSize: 13, color: "var(--text-hi)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {s.query}
              </div>
              {s.error_msg && (
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--red)", marginTop: 2 }}>
                  ✕ {s.error_msg}
                </div>
              )}
            </div>

            <StatusCell status={s.status} />

            <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-md)" }}>
              {fmtDate(s.timestamp)}
            </span>

            {/* Duration, Tokens, Sources, Cost, Agents — not in SessionSummary, render — */}
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-hi)", fontVariantNumeric: "tabular-nums" }}>—</span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-md)", textAlign: "right" }}>—</span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-md)", textAlign: "right" }}>—</span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-md)", textAlign: "right" }}>—</span>
            <div style={{ display: "flex", justifyContent: "center" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)" }}>—</span>
            </div>
          </div>
        ))}
      </div>

      {/* Footer / pagination */}
      <div style={{
        padding: "10px 32px", borderTop: "1px solid var(--border)", background: "var(--surface)",
        display: "flex", alignItems: "center",
        fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)",
        letterSpacing: "0.12em", textTransform: "uppercase",
      }}>
        <span>SHOWING 1–{filtered.length} OF {sessions.length}</span>
        <div style={{ marginLeft: "auto", display: "flex", gap: 14 }}>
          <span>← PREV</span>
          <span style={{ color: "var(--text-hi)" }}>1</span>
          <span style={{ color: "var(--amber)" }}>NEXT →</span>
        </div>
      </div>
    </div>
  );
}

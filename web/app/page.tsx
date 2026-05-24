"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { TopNav } from "@/components/buzz/TopNav";
import { SwarmGraph } from "@/components/buzz/SwarmGraph";
import { StatusDot } from "@/components/buzz/StatusDot";
import { SectionLabel } from "@/components/buzz/SectionLabel";
import { StatusChip } from "@/components/buzz/StatusChip";

const SUGGESTIONS = [
  "Map market access for GLP-1 agonists in EU5 through 2030",
  "Competitive landscape for CAR-T therapies vs. BiTE antibodies",
  "NICE HTA outcomes for rare disease gene therapies 2022–2025",
];

const LIVE_LOG = [
  { t: "12:42:01", agent: "lead",     c: "var(--amber)",  msg: "planning · 6 subtasks queued" },
  { t: "12:42:04", agent: "market",   c: "var(--cyan)",   msg: "GET clinicaltrials.gov · 47 trials" },
  { t: "12:42:09", agent: "analyst",  c: "var(--violet)", msg: "reading IQVIA · TAM frame ready" },
  { t: "12:42:14", agent: "market",   c: "var(--cyan)",   msg: "FDA orange book · 12 NDAs" },
  { t: "12:42:18", agent: "lead",     c: "var(--amber)",  msg: "handoff → reporter · 18,402 tok", pulse: true },
];

const FEATURES = [
  { l: "01", t: "Regulatory snapshots",     d: "FDA, EMA, PMDA filings · IND status · orange book mapping." },
  { l: "02", t: "Clinical trial synthesis", d: "ClinicalTrials.gov · arm-by-arm analysis · primary endpoints." },
  { l: "03", t: "Market sizing",            d: "TAM/SAM · CAGR · payer mix · published-source triangulation." },
  { l: "04", t: "Structured dossier",       d: "Pydantic-validated markdown · PDF export · footnoted citations." },
];

const STATS = [
  { l: "Avg run", v: "4:18", s: "min:sec" },
  { l: "Sources", v: "2.4M", s: "indexed" },
  { l: "Therapies", v: "1,847", s: "tracked" },
  { l: "Accuracy", v: "94.2%", s: "vs analyst" },
];

export default function Home() {
  const router = useRouter();
  const [query, setQuery] = useState("");

  const onSubmit = () => {
    if (query.trim()) {
      router.push("/query?q=" + encodeURIComponent(query));
    } else {
      router.push("/query");
    }
  };

  return (
    <div style={{
      background: "var(--bg)", color: "var(--text-hi)",
      fontFamily: "var(--font-sans)",
      display: "flex", flexDirection: "column", minHeight: "100vh",
    }}>
      <TopNav />

      {/* Status strip */}
      <div style={{
        display: "flex", alignItems: "center",
        padding: "0 16px", height: 28,
        borderBottom: "1px solid var(--border)",
        fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)",
        gap: 18, flexShrink: 0,
      }}>
        <span style={{ color: "var(--amber)" }}>● LIVE</span>
        <span>BUZZ HC v1.4.2</span>
        <span>4 AGENTS ONLINE</span>
        <span>3 RUNS IN-FLIGHT</span>
        <span style={{ marginLeft: "auto" }}>WED · 24 MAY · 12:42:18 UTC</span>
      </div>

      {/* Hero — 2 columns */}
      <div style={{
        display: "grid", gridTemplateColumns: "minmax(0,1fr) 560px",
        flex: 1, minHeight: 0,
      }}>
        {/* Left */}
        <div style={{
          padding: "56px 56px 40px",
          display: "flex", flexDirection: "column",
          justifyContent: "center",
          borderRight: "1px solid var(--border)",
          gap: 28,
        }}>
          <SectionLabel>Multi-agent pharma intelligence</SectionLabel>

          <h1 style={{
            fontSize: 64, lineHeight: 0.98, fontWeight: 600,
            letterSpacing: "-0.025em", margin: 0,
          }}>
            Publication-grade<br />
            market research,<br />
            <span style={{ color: "var(--amber)" }}>fielded by a swarm.</span>
          </h1>

          <p style={{
            fontSize: 15, lineHeight: 1.55, color: "var(--text-md)",
            margin: 0, maxWidth: 460,
          }}>
            Four specialized agents — orchestrator, market access, analyst, reporter — work in parallel
            against FDA, EMA, ClinicalTrials.gov, and live web sources to produce a structured pharma dossier in minutes.
          </p>

          {/* Query box */}
          <div
            style={{
              display: "flex", alignItems: "center",
              border: "1px solid var(--border)", borderRadius: 2,
              background: "var(--surface)",
            }}
            onFocus={(e) => e.currentTarget.style.borderColor = "var(--amber)"}
            onBlur={(e) => e.currentTarget.style.borderColor = "var(--border)"}
          >
            <span style={{ padding: "0 12px", color: "var(--amber)", fontFamily: "var(--font-mono)", fontSize: 13 }}>›</span>
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter") onSubmit(); }}
              placeholder="Ask the swarm anything pharma…"
              style={{
                flex: 1, padding: "14px 0",
                background: "transparent", border: "none", outline: "none",
                color: "var(--text-hi)", fontFamily: "var(--font-sans)", fontSize: 14,
              }}
            />
            <button
              onClick={onSubmit}
              style={{
                background: "var(--amber)", color: "#0a0d14",
                border: "none", padding: "12px 18px",
                fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 600,
                letterSpacing: "0.14em", textTransform: "uppercase", cursor: "pointer",
                display: "inline-flex", alignItems: "center", gap: 6,
              }}
            >
              Run swarm ↵
            </button>
          </div>

          {/* Suggestions */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: -12 }}>
            {SUGGESTIONS.map(s => (
              <button
                key={s}
                onClick={() => setQuery(s)}
                style={{
                  padding: "4px 9px", border: "1px solid var(--border)",
                  background: "transparent", color: "var(--text-md)",
                  fontFamily: "var(--font-mono)", fontSize: 10, cursor: "pointer",
                  borderRadius: 2, letterSpacing: "0.04em",
                }}
              >
                ↗ {s.length > 56 ? s.slice(0, 56) + "…" : s}
              </button>
            ))}
          </div>

          {/* Stats row */}
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
            marginTop: 16,
            borderTop: "1px solid var(--border)",
            borderBottom: "1px solid var(--border)",
          }}>
            {STATS.map((s, i) => (
              <div key={i} style={{ padding: "14px 16px", borderRight: i < 3 ? "1px solid var(--border)" : "none" }}>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-lo)", letterSpacing: "0.16em", textTransform: "uppercase" }}>{s.l}</div>
                <div style={{ fontSize: 22, fontWeight: 600, marginTop: 4, fontVariantNumeric: "tabular-nums" }}>{s.v}</div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-lo)", marginTop: 2 }}>{s.s}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right — swarm + log */}
        <div style={{ display: "flex", flexDirection: "column", background: "var(--surface)" }}>
          <div style={{
            padding: "12px 16px", borderBottom: "1px solid var(--border)",
            display: "flex", alignItems: "center", gap: 12,
          }}>
            <SectionLabel>Swarm visualization</SectionLabel>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)", marginLeft: "auto" }}>
              DEMO
            </span>
            <StatusChip status="running" label="Live" />
          </div>

          <div style={{ padding: "20px 16px", display: "flex", justifyContent: "center" }}>
            <SwarmGraph width={520} height={360} animate />
          </div>

          <div style={{
            borderTop: "1px solid var(--border)",
            padding: "12px 16px", flex: 1,
            display: "flex", flexDirection: "column", gap: 10,
            background: "var(--bg)",
          }}>
            <SectionLabel>Live stream</SectionLabel>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-md)", lineHeight: 1.7 }}>
              {LIVE_LOG.map((l, i) => (
                <div key={i} style={{ display: "flex", gap: 12, alignItems: "center", opacity: 1 - i * 0.05 }}>
                  <span style={{ color: "var(--text-lo)" }}>{l.t}</span>
                  <span style={{ color: l.c, letterSpacing: "0.14em", fontSize: 10, fontWeight: 600, width: 70 }}>{l.agent.toUpperCase()}</span>
                  <span style={{ color: l.pulse ? "var(--amber)" : "var(--text-md)", flex: 1 }}>{l.msg}</span>
                  {l.pulse && <StatusDot status="live" pulse />}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Feature strip */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
        borderTop: "1px solid var(--border)", height: 132,
      }}>
        {FEATURES.map((f, i) => (
          <div key={i} style={{
            padding: "16px 20px",
            borderRight: i < 3 ? "1px solid var(--border)" : "none",
            display: "flex", flexDirection: "column", gap: 8,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--amber)", letterSpacing: "0.14em" }}>{f.l}</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-lo)" }}>→</span>
            </div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>{f.t}</div>
            <div style={{ fontSize: 12, color: "var(--text-md)", lineHeight: 1.5 }}>{f.d}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

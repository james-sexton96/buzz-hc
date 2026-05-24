"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { TopNav } from "@/components/buzz/TopNav";
import { SectionLabel } from "@/components/buzz/SectionLabel";
import { Btn } from "@/components/buzz/Btn";
import { startRun } from "@/lib/api";
import Link from "next/link";

const SUGGESTIONS = [
  "Map market access for GLP-1 agonists in EU5 through 2030 — sizing, payers, key catalysts.",
  "Competitive landscape for CAR-T therapies: BiTE antibodies vs. autologous vs. allogeneic.",
  "NICE HTA outcomes for rare disease gene therapies approved 2022–2025.",
  "FDA breakthrough designations in oncology: pipeline analysis and probability of approval.",
];

const PIPELINE_STAGES = [
  { id: "plan",    label: "Orchestration plan",    desc: "LEAD" },
  { id: "access",  label: "Market access research", desc: "MARKET" },
  { id: "sizing",  label: "Market sizing",          desc: "ANALYST" },
  { id: "comp",    label: "Competitive analysis",   desc: "ANALYST" },
  { id: "synth",   label: "Synthesis & report",     desc: "REPORTER" },
];

const AGENTS = [
  { id: "lead",     name: "LEAD",     role: "Orchestrator",        color: "var(--amber)"  },
  { id: "market",   name: "MARKET",   role: "Regulatory + Access", color: "var(--cyan)"   },
  { id: "analyst",  name: "ANALYST",  role: "Sizing + Comp",       color: "var(--violet)" },
  { id: "reporter", name: "REPORTER", role: "Synthesis",           color: "var(--green)"  },
];

function QueryInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState(searchParams.get("q") ?? "");
  const [depth, setDepth] = useState<"quick" | "standard" | "deep">("standard");
  const [budget, setBudget] = useState(2.0);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const q = searchParams.get("q");
    if (q) setQuery(q);
  }, [searchParams]);

  const runNow = async () => {
    if (!query.trim() || submitting) return;
    setSubmitting(true);
    try {
      const result = await startRun(query);
      router.push("/run/" + result.session_id);
    } catch {
      setSubmitting(false);
    }
  };

  const depthOptions = [
    { id: "quick",    l: "Quick",    desc: "~2 min · 30 sources · 1 agent" },
    { id: "standard", l: "Standard", desc: "~5 min · 80 sources · 4 agents" },
    { id: "deep",     l: "Deep",     desc: "~12 min · 200+ sources · re-verify" },
  ] as const;

  return (
    <div style={{
      background: "var(--bg)", color: "var(--text-hi)",
      fontFamily: "var(--font-sans)",
      display: "flex", flexDirection: "column", minHeight: "100vh",
    }}>
      <TopNav />

      {/* Breadcrumb */}
      <div style={{
        padding: "10px 16px", borderBottom: "1px solid var(--border)",
        fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)",
        letterSpacing: "0.14em", textTransform: "uppercase",
        background: "var(--surface)",
        display: "flex", alignItems: "center", gap: 12,
      }}>
        <Link href="/" style={{ color: "var(--text-md)", textDecoration: "none" }}>Research</Link>
        <span>›</span>
        <span style={{ color: "var(--text-hi)" }}>New Query</span>
        <span style={{ marginLeft: "auto", color: submitting ? "var(--amber)" : "var(--text-lo)" }}>
          {submitting ? "▸ DISPATCHING SWARM…" : "READY · ⌘↵ TO RUN"}
        </span>
      </div>

      {/* Main body */}
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "minmax(0, 1fr) 360px" }}>
        {/* Left — composer */}
        <div style={{ padding: "48px 64px", display: "flex", flexDirection: "column", gap: 28, maxWidth: 880 }}>
          <div>
            <SectionLabel>Compose · brief</SectionLabel>
            <h1 style={{ fontSize: 42, fontWeight: 600, letterSpacing: "-0.02em", margin: "12px 0 6px 0" }}>
              What should the swarm investigate?
            </h1>
            <p style={{ fontSize: 14, color: "var(--text-md)", margin: 0, maxWidth: 580, lineHeight: 1.55 }}>
              The brief becomes the orchestrator&apos;s plan. Be specific about geography,
              therapeutic area, and time horizon — the swarm uses these as constraints when scoping sources.
            </p>
          </div>

          {/* Textarea */}
          <div style={{ border: "1px solid var(--border)", borderRadius: 2, background: "var(--surface)", overflow: "hidden" }}>
            <div style={{
              padding: "10px 14px", borderBottom: "1px solid var(--border)",
              display: "flex", alignItems: "center", gap: 10,
            }}>
              <span style={{ color: "var(--amber)", fontFamily: "var(--font-mono)", fontSize: 12 }}>›</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-md)", letterSpacing: "0.14em", textTransform: "uppercase" }}>
                Brief
              </span>
              <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)" }}>
                {query.length} / 2000
              </span>
            </div>
            <textarea
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) runNow(); }}
              autoFocus
              placeholder="e.g. Map market access for GLP-1 agonists in EU5 through 2030 — sizing, payers, key catalysts."
              style={{
                width: "100%", minHeight: 160, padding: "16px 18px",
                background: "transparent", border: "none", outline: "none",
                color: "var(--text-hi)", fontFamily: "var(--font-sans)", fontSize: 15, lineHeight: 1.55,
                resize: "vertical", boxSizing: "border-box",
              }}
            />
          </div>

          {/* Suggestions */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <SectionLabel>Suggestions</SectionLabel>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => setQuery(s)} style={{
                  padding: "8px 12px", border: "1px solid var(--border)",
                  background: "transparent", color: "var(--text-md)",
                  fontFamily: "var(--font-sans)", fontSize: 12, cursor: "pointer",
                  borderRadius: 2, textAlign: "left",
                }}>↗ {s}</button>
              ))}
            </div>
          </div>

          {/* Depth + Budget */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div style={{ border: "1px solid var(--border)", padding: 14, display: "flex", flexDirection: "column", gap: 10 }}>
              <SectionLabel>Depth</SectionLabel>
              <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 2, overflow: "hidden" }}>
                {depthOptions.map((d, idx) => (
                  <button key={d.id} onClick={() => setDepth(d.id)} style={{
                    flex: 1, padding: "10px 8px",
                    background: depth === d.id ? "var(--amber)" : "transparent",
                    color: depth === d.id ? "#0a0d14" : "var(--text-md)",
                    border: "none", cursor: "pointer",
                    fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 600,
                    letterSpacing: "0.12em", textTransform: "uppercase",
                    borderRight: idx < 2 ? "1px solid var(--border)" : "none",
                  }}>{d.l}</button>
                ))}
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)" }}>
                {depthOptions.find(d => d.id === depth)?.desc}
              </div>
            </div>

            <div style={{ border: "1px solid var(--border)", padding: 14, display: "flex", flexDirection: "column", gap: 10 }}>
              <SectionLabel>Token budget</SectionLabel>
              <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
                <span style={{ fontSize: 26, fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>${budget.toFixed(2)}</span>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-md)" }}>cap</span>
              </div>
              <input
                type="range" min="0.5" max="5" step="0.5"
                value={budget} onChange={e => setBudget(parseFloat(e.target.value))}
                style={{ width: "100%", accentColor: "var(--amber)" }}
              />
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)" }}>
                stop run if exceeded · est ${(budget * 0.6).toFixed(2)} for this brief
              </div>
            </div>
          </div>

          {/* CTA */}
          <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 8 }}>
            <Btn primary onClick={runNow} disabled={!query.trim() || submitting}>
              {submitting ? "Dispatching…" : "Dispatch swarm ↵"}
            </Btn>
            <Link href="/" style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)", letterSpacing: "0.14em", textTransform: "uppercase", textDecoration: "none" }}>
              ← Cancel
            </Link>
          </div>
        </div>

        {/* Right — plan preview */}
        <div style={{ background: "var(--surface)", borderLeft: "1px solid var(--border)", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
            <SectionLabel>Plan preview · agent will refine</SectionLabel>
          </div>

          <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{
              fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-md)",
              border: "1px solid var(--border)", padding: 12, lineHeight: 1.55,
              background: "var(--bg)", borderRadius: 2,
            }}>
              {query
                ? <span style={{ color: "var(--text-hi)" }}>{query}</span>
                : <span style={{ color: "var(--text-lo)" }}>Brief preview will appear here…</span>}
            </div>

            <SectionLabel>Planned stages</SectionLabel>
            <div style={{ display: "flex", flexDirection: "column" }}>
              {PIPELINE_STAGES.map((s, i) => (
                <div key={s.id} style={{
                  display: "flex", gap: 10, alignItems: "center",
                  padding: "8px 0",
                  borderTop: i === 0 ? "1px solid var(--border)" : "1px dashed var(--border)",
                }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)", width: 24 }}>{String(i + 1).padStart(2, "0")}</span>
                  <span style={{ fontSize: 12, color: "var(--text-hi)", flex: 1 }}>{s.label}</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-md)" }}>{s.desc}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ borderTop: "1px solid var(--border)", marginTop: "auto", padding: "14px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
            <SectionLabel>Agents on call</SectionLabel>
            {AGENTS.map(a => (
              <div key={a.id} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "6px 0", borderBottom: "1px dashed var(--border)",
              }}>
                <span style={{ width: 8, height: 8, background: a.color, display: "inline-block" }} />
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: a.color, letterSpacing: "0.14em", fontWeight: 600, width: 70 }}>{a.name}</span>
                <span style={{ fontSize: 11, color: "var(--text-md)" }}>{a.role}</span>
                <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-lo)" }}>READY</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function QueryPage() {
  return (
    <Suspense fallback={null}>
      <QueryInner />
    </Suspense>
  );
}

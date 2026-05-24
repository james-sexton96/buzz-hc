"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { getSession } from "@/lib/api"
import type {
  AnalystFindings,
  MarketAccessFindings,
  SessionDetail,
} from "@/lib/types"

import { TopNav } from "@/components/buzz/TopNav"
import { PanelCard } from "@/components/buzz/PanelCard"
import { DonutChart } from "@/components/buzz/DonutChart"
import { Btn } from "@/components/buzz/Btn"
import { SectionLabel } from "@/components/buzz/SectionLabel"
import {
  FootnoteDrawer,
  type CitationRef,
} from "@/components/buzz/FootnoteDrawer"

// ---------- pure helpers (defined outside component) ----------

function normalizeCoverageStatus(
  s: string,
): "covered" | "restricted" | "not_covered" | "unknown" {
  const lower = (s ?? "").toLowerCase()
  if (lower.includes("not covered")) return "not_covered"
  if (lower.includes("covered") && !lower.includes("not")) return "covered"
  if (
    lower.includes("pa required") ||
    lower.includes("prior auth") ||
    lower.includes("tier") ||
    lower.includes("restricted") ||
    lower.includes("step")
  ) {
    return "restricted"
  }
  return "unknown"
}

function parseSharePercent(s: string): number {
  const m = (s ?? "").match(/(\d+(?:\.\d+)?)%/)
  return m ? parseFloat(m[1]) : 0
}

function preprocessCitations(md: string): string {
  return md.replace(/\[(\d+)\]/g, '<cite data-n="$1">[$1]</cite>')
}

function safeParse<T>(raw: string | null | undefined): T | null {
  if (!raw) return null
  try {
    const v = JSON.parse(raw)
    return v as T
  } catch {
    return null
  }
}

function safeHostname(url: string): string {
  try {
    return new URL(url).hostname
  } catch {
    return url
  }
}

// ---------- page component ----------

export default function ReportPage() {
  const params = useParams<{ id: string }>()
  const sessionId = params.id
  const router = useRouter()

  const [session, setSession] = useState<SessionDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [citation, setCitation] = useState<CitationRef | null>(null)

  useEffect(() => {
    let active = true
    setIsLoading(true)
    getSession(sessionId)
      .then((data) => {
        if (!active) return
        setSession(data)
        setIsLoading(false)
      })
      .catch((err: unknown) => {
        if (!active) return
        setError(err instanceof Error ? err.message : "Failed to load session")
        setIsLoading(false)
      })
    return () => {
      active = false
    }
  }, [sessionId])

  // Redirect guard — runs after data loads.
  useEffect(() => {
    if (isLoading) return
    if (!session) return
    if (session.status !== "complete" || !session.report) {
      router.replace("/run/" + sessionId)
    }
  }, [isLoading, session, router, sessionId])

  if (isLoading) {
    return (
      <>
        <TopNav />
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: "60vh",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            color: "var(--text-lo)",
          }}
        >
          Loading…
        </div>
      </>
    )
  }

  if (error || !session) {
    return (
      <>
        <TopNav />
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: "60vh",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            color: "var(--text-lo)",
          }}
        >
          Session not found
        </div>
      </>
    )
  }

  // The redirect effect will fire on the next tick — render nothing in the
  // meantime to avoid a flash of empty dossier chrome.
  if (session.status !== "complete" || !session.report) {
    return (
      <>
        <TopNav />
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: "60vh",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            color: "var(--text-lo)",
          }}
        >
          Redirecting to run view…
        </div>
      </>
    )
  }

  const report = session.report
  const sections = report.sections ?? []
  const sources = report.sources ?? []

  // ---- KPI data extraction ----

  const researchData = safeParse<MarketAccessFindings>(session.research_json)
  const payers = researchData?.payer_coverage ?? []
  const normalized = payers.map((p) => normalizeCoverageStatus(p.coverage_status))
  const covered = normalized.filter((s) => s === "covered").length
  const restricted = normalized.filter((s) => s === "restricted").length
  const totalPayers = payers.length
  const hasPayerData =
    totalPayers > 0 && normalized.some((s) => s !== "unknown")
  const payerFilled =
    totalPayers > 0 ? (covered + restricted) / totalPayers : 0

  const analystData = safeParse<AnalystFindings>(session.analyst_json)
  const competitors = analystData?.competitive_landscape ?? []
  const hasCompetitorData = competitors.length > 0

  // ---- Re-run handler ----

  function handleRerun() {
    router.push("/query?q=" + encodeURIComponent(session?.query ?? ""))
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg)",
        color: "var(--text-hi)",
        fontFamily: "var(--font-sans)",
      }}
    >
      <TopNav />

      {/* Breadcrumb */}
      <div
        style={{
          padding: "10px 16px",
          borderBottom: "1px solid var(--border)",
          background: "var(--surface)",
          fontFamily: "var(--font-mono)",
          fontSize: 10,
          color: "var(--text-lo)",
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <Link href="/sessions" style={{ color: "var(--text-md)", textDecoration: "none" }}>
          SESSIONS
        </Link>
        <span>›</span>
        <Link
          href={"/run/" + sessionId}
          style={{ color: "var(--text-md)", textDecoration: "none" }}
        >
          {sessionId.slice(0, 8).toUpperCase()}
        </Link>
        <span>›</span>
        <span style={{ color: "var(--text-hi)" }}>DOSSIER</span>
        <span style={{ marginLeft: "auto", color: "var(--green)" }}>
          ● COMPLETE
        </span>
      </div>

      {/* Top strip — title + lede + actions */}
      <div
        style={{
          padding: "26px 24px 20px",
          borderBottom: "1px solid var(--border)",
          display: "grid",
          gridTemplateColumns: "1fr auto",
          gap: 24,
          alignItems: "flex-end",
        }}
      >
        <div style={{ minWidth: 0 }}>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              color: "var(--text-lo)",
              letterSpacing: "0.18em",
              textTransform: "uppercase",
              display: "flex",
              gap: 12,
              marginBottom: 12,
            }}
          >
            <span style={{ color: "var(--amber)" }}>
              DOSSIER · {sessionId.slice(0, 8).toUpperCase()}
            </span>
          </div>
          <h1
            style={{
              fontSize: 36,
              fontWeight: 600,
              letterSpacing: "-0.02em",
              lineHeight: 1.1,
              margin: "0 0 14px 0",
              color: "var(--text-hi)",
            }}
          >
            {report.title}
          </h1>
          <p
            style={{
              fontSize: 14,
              color: "var(--text-md)",
              maxWidth: 820,
              margin: 0,
              lineHeight: 1.55,
            }}
          >
            {report.executive_summary}
          </p>
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 10,
            alignItems: "flex-end",
          }}
        >
          <div style={{ display: "flex", gap: 8 }}>
            <Btn disabled>Share</Btn>
            <Btn disabled>Export PDF</Btn>
            <Btn primary onClick={handleRerun}>Re-run</Btn>
          </div>
          <div
            style={{
              display: "flex",
              gap: 14,
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              color: "var(--text-lo)",
              letterSpacing: "0.12em",
              textTransform: "uppercase",
            }}
          >
            <span>{sources.length} SOURCES</span>
            <span>{sections.length} SECTIONS</span>
          </div>
        </div>
      </div>

      {/* Panel grid */}
      <div
        style={{
          padding: "16px 20px",
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 16,
        }}
      >
        {sections.map((section, i) => {
          const span =
            sections.length >= 4 && (i === 0 || i === 3) ? "span 2" : "span 1"
          return (
            <div key={i} style={{ gridColumn: span }}>
              <PanelCard heading={section.heading}>
                <div
                  className="dossier-markdown"
                  style={{
                    color: "var(--text-md)",
                    fontSize: 13,
                    lineHeight: 1.65,
                  }}
                >
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      // `cite` is valid HTML; react-markdown's component map
                      // doesn't ship a type for it. We use it as our citation
                      // placeholder produced by preprocessCitations().
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      cite: ({ node, ...props }: any) => {
                        const dataN =
                          node?.properties?.dataN ??
                          props["data-n"] ??
                          "0"
                        const n = parseInt(String(dataN), 10) || 0
                        const url = sources[n - 1] ?? ""
                        return (
                          <sup
                            onClick={() => {
                              if (url) setCitation({ n, url })
                            }}
                            style={{
                              color: "var(--cyan)",
                              textDecoration: "underline dotted",
                              textUnderlineOffset: 2,
                              cursor: url ? "pointer" : "default",
                              fontFamily: "var(--font-mono)",
                              fontSize: "0.75em",
                              padding: "0 1px",
                            }}
                          >
                            [{n}]
                          </sup>
                        )
                      },
                    }}
                  >
                    {preprocessCitations(section.content)}
                  </ReactMarkdown>
                </div>
              </PanelCard>
            </div>
          )
        })}

        {/* Payer Coverage KPI panel */}
        <div style={{ gridColumn: "span 1" }}>
          <PanelCard heading="Payer Coverage">
            {hasPayerData ? (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                }}
              >
                <DonutChart filled={payerFilled} color="var(--cyan)" size={80} />
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 4,
                  }}
                >
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 9,
                      color: "var(--text-lo)",
                      letterSpacing: "0.14em",
                      textTransform: "uppercase",
                    }}
                  >
                    COVERED + RESTRICTED
                  </div>
                  <div
                    style={{
                      fontSize: 22,
                      fontWeight: 600,
                      color: "var(--text-hi)",
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {covered + restricted} of {totalPayers}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 10,
                      color: "var(--text-md)",
                    }}
                  >
                    {covered} covered · {restricted} restricted
                  </div>
                </div>
              </div>
            ) : (
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  color: "var(--text-lo)",
                  letterSpacing: "0.08em",
                  padding: "12px 0",
                }}
              >
                data not available
              </div>
            )}
          </PanelCard>
        </div>

        {/* Competitive Landscape KPI panel */}
        <div style={{ gridColumn: "span 1" }}>
          <PanelCard heading="Competitive Landscape">
            {hasCompetitorData ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {competitors.map((c, i) => {
                  const pct = parseSharePercent(c.share_or_notes)
                  return (
                    <div
                      key={i}
                      style={{ display: "flex", flexDirection: "column", gap: 4 }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "baseline",
                        }}
                      >
                        <span style={{ fontSize: 12, color: "var(--text-hi)" }}>
                          {c.name}
                        </span>
                        <span
                          style={{
                            fontFamily: "var(--font-mono)",
                            fontSize: 11,
                            color: "var(--cyan)",
                            fontVariantNumeric: "tabular-nums",
                            fontWeight: 600,
                          }}
                        >
                          {pct}%
                        </span>
                      </div>
                      <div
                        style={{
                          height: 5,
                          background: "var(--border)",
                          width: "100%",
                        }}
                      >
                        <div
                          style={{
                            width: `${Math.max(0, Math.min(100, pct))}%`,
                            height: "100%",
                            background: "var(--cyan)",
                          }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  color: "var(--text-lo)",
                  letterSpacing: "0.08em",
                  padding: "12px 0",
                }}
              >
                data not available
              </div>
            )}
          </PanelCard>
        </div>
      </div>

      {/* Footnotes strip */}
      {sources.length > 0 && (
        <div
          style={{
            borderTop: "1px solid var(--border)",
            background: "var(--surface)",
            padding: "14px 22px",
            display: "grid",
            gridTemplateColumns: "120px 1fr",
            gap: 18,
            alignItems: "start",
          }}
        >
          <div>
            <SectionLabel>Footnotes</SectionLabel>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 10,
                color: "var(--text-lo)",
                marginTop: 6,
              }}
            >
              {Math.min(6, sources.length)} of {sources.length} shown
            </div>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 14,
            }}
          >
            {sources.slice(0, 6).map((src, i) => {
              const n = i + 1
              const domain = safeHostname(src)
              return (
                <button
                  key={n}
                  onClick={() => setCitation({ n, url: src })}
                  style={{
                    background: "transparent",
                    border: "none",
                    padding: 0,
                    paddingLeft: 10,
                    borderLeft: "1px solid var(--border)",
                    textAlign: "left",
                    cursor: "pointer",
                    display: "flex",
                    flexDirection: "column",
                    gap: 4,
                    fontFamily: "var(--font-sans)",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 11,
                      color: "var(--cyan)",
                      fontWeight: 600,
                    }}
                  >
                    [{n}]
                  </span>
                  <span
                    style={{
                      fontSize: 11,
                      color: "var(--text-hi)",
                      lineHeight: 1.35,
                      wordBreak: "break-word",
                    }}
                  >
                    {src}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 9,
                      color: "var(--cyan)",
                      textDecoration: "underline",
                    }}
                  >
                    ↗ {domain}
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      <FootnoteDrawer
        open={!!citation}
        citation={citation}
        onClose={() => setCitation(null)}
      />
    </div>
  )
}

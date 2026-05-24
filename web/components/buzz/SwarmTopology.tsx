"use client"
import { useEffect, useRef } from "react"
import type { SessionStatus } from "@/lib/types"

interface SwarmTopologyProps {
  status: SessionStatus
  width?: number
  height?: number
}

const NODE_DEFS = [
  { id: "Lead",       label: "LEAD",    color: "var(--amber)",  angle: -Math.PI / 2, r: 0 },
  { id: "Researcher", label: "RSRCH",   color: "var(--cyan)",   angle: -Math.PI / 2, r: 130 },
  { id: "Analyst",    label: "ANLST",   color: "var(--violet)", angle: Math.PI / 6,  r: 130 },
  { id: "Reporter",   label: "RPRT",    color: "var(--green)",  angle: Math.PI * 5/6, r: 130 },
] as const

const EDGES = [
  { from: 0, to: 1 },
  { from: 0, to: 2 },
  { from: 0, to: 3 },
  { from: 1, to: 2 },
  { from: 2, to: 3 },
]

export function SwarmTopology({ status, width = 540, height = 400 }: SwarmTopologyProps) {
  const cx = width / 2
  const cy = height / 2

  const nodes = NODE_DEFS.map(n => ({
    ...n,
    x: n.r === 0 ? cx : cx + Math.cos(n.angle) * n.r,
    y: n.r === 0 ? cy : cy + Math.sin(n.angle) * n.r,
  }))

  const packetRefsOuter = useRef<(SVGCircleElement | null)[]>([])
  const packetRefsInner = useRef<(SVGCircleElement | null)[]>([])
  const statusRef = useRef(status)
  statusRef.current = status

  useEffect(() => {
    if (status === "paused") return

    let rafId: number
    let tick = 0

    const loop = () => {
      if (statusRef.current === "paused") {
        rafId = requestAnimationFrame(loop)
        return
      }
      tick = (tick + 1) % 600
      EDGES.forEach((e, i) => {
        const phase = (tick / 90 + i * 0.27) % 1
        const a = nodes[e.from]
        const b = nodes[e.to]
        const px = a.x + (b.x - a.x) * phase
        const py = a.y + (b.y - a.y) * phase
        const outer = packetRefsOuter.current[i]
        const inner = packetRefsInner.current[i]
        if (outer) { outer.setAttribute("cx", String(px)); outer.setAttribute("cy", String(py)) }
        if (inner) { inner.setAttribute("cx", String(px)); inner.setAttribute("cy", String(py)) }
      })
      rafId = requestAnimationFrame(loop)
    }

    rafId = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(rafId)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status])

  const hubLabel = status === "error" ? "ERR" : status === "paused" ? "PSE" : "HUB"
  const hubColor = status === "error" ? "var(--red)" : status === "paused" ? "var(--amber)" : "var(--amber)"

  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      <defs>
        <radialGradient id="st-glow" cx="0.5" cy="0.5">
          <stop offset="0" stopColor={hubColor} stopOpacity="0.3" />
          <stop offset="1" stopColor={hubColor} stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Rings */}
      {[80, 130, 180].map(r => (
        <circle key={r} cx={cx} cy={cy} r={r} fill="none" stroke="var(--border)" strokeWidth="0.6" strokeDasharray="4 4" strokeOpacity="0.5" />
      ))}

      {/* Compass labels */}
      {[["N", cx, cy - 190], ["E", cx + 190, cy], ["S", cx, cy + 194], ["W", cx - 190, cy]].map(([l, x, y]) => (
        <text key={String(l)} x={Number(x)} y={Number(y)} textAnchor="middle" dominantBaseline="middle"
          fontFamily="var(--font-mono)" fontSize="8" fill="var(--text-lo)" letterSpacing="0.12em" opacity="0.5">{l}</text>
      ))}

      {/* Hub glow */}
      <circle cx={cx} cy={cy} r={70} fill="url(#st-glow)" />

      {/* Edges */}
      {EDGES.map((e, i) => (
        <line key={i}
          x1={nodes[e.from].x} y1={nodes[e.from].y}
          x2={nodes[e.to].x} y2={nodes[e.to].y}
          stroke="var(--text-lo)" strokeOpacity="0.3" strokeWidth="0.8" strokeDasharray="3 3"
        />
      ))}

      {/* Packets — positions updated imperatively via refs */}
      {status !== "paused" && EDGES.map((_, i) => (
        <g key={i}>
          <circle ref={el => { packetRefsOuter.current[i] = el }} cx={nodes[EDGES[i].from].x} cy={nodes[EDGES[i].from].y} r="6" fill="var(--amber)" opacity="0.2" />
          <circle ref={el => { packetRefsInner.current[i] = el }} cx={nodes[EDGES[i].from].x} cy={nodes[EDGES[i].from].y} r="3" fill="var(--amber)" />
        </g>
      ))}

      {/* Hub */}
      <circle cx={cx} cy={cy} r="24" fill="var(--bg)" stroke={hubColor} strokeWidth="1.5" />
      {status === "error" && <circle cx={cx} cy={cy} r="24" fill="none" stroke="var(--red)" strokeWidth="1.5"><animate attributeName="opacity" values="0.3;1;0.3" dur="1.4s" repeatCount="indefinite" /></circle>}
      <circle cx={cx} cy={cy} r="6" fill={hubColor} />
      <text x={cx} y={cy + 40} textAnchor="middle" fontFamily="var(--font-mono)" fontSize="9" fill="var(--text-lo)" letterSpacing="0.18em">{hubLabel}</text>

      {/* Nodes */}
      {nodes.filter(n => n.r > 0).map(n => (
        <g key={n.id}>
          <circle cx={n.x} cy={n.y} r="18" fill="var(--surface)" stroke={n.color} strokeWidth="1" />
          <circle cx={n.x} cy={n.y} r="4" fill={n.color}>
            <animate attributeName="opacity" values="0.5;1;0.5" dur="1.4s" repeatCount="indefinite" />
          </circle>
          <text x={n.x} y={n.y + 32} textAnchor="middle" fontFamily="var(--font-mono)" fontSize="9" fill={n.color} letterSpacing="0.14em">{n.label}</text>
        </g>
      ))}
    </svg>
  )
}

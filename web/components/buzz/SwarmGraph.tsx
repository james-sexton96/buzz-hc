"use client";

import { useEffect, useRef } from "react";

interface NodeState {
  id: string;
  status?: "running" | "idle" | "complete" | "error";
}

interface SwarmGraphProps {
  width?: number;
  height?: number;
  nodeStates?: NodeState[];
  animate?: boolean;
}

const NODE_DEFS = [
  { id: "lead",     label: "LEAD",     role: "Orchestrator",  angle: -Math.PI / 2, color: "var(--amber)"  },
  { id: "market",   label: "MARKET",   role: "Regulatory",    angle: 0,            color: "var(--cyan)"   },
  { id: "analyst",  label: "ANALYST",  role: "Market sizing", angle: Math.PI / 2,  color: "var(--violet)" },
  { id: "reporter", label: "REPORTER", role: "Synthesis",     angle: Math.PI,      color: "var(--green)"  },
];

const EDGES = [
  { from: 0, to: 1 },
  { from: 0, to: 2 },
  { from: 0, to: 3 },
  { from: 1, to: 2 },
  { from: 2, to: 3 },
];

export function SwarmGraph({ width = 520, height = 360, animate = true }: SwarmGraphProps) {
  const cx = width / 2;
  const cy = height / 2;
  const R = Math.min(width, height) * 0.32;

  const nodes = NODE_DEFS.map(n => ({
    ...n,
    x: cx + Math.cos(n.angle) * R,
    y: cy + Math.sin(n.angle) * R,
  }));

  const packetRefsOuter = useRef<(SVGCircleElement | null)[]>([]);
  const packetRefsInner = useRef<(SVGCircleElement | null)[]>([]);
  const animateRef = useRef(animate);
  animateRef.current = animate;

  useEffect(() => {
    if (!animate) return;

    let rafId: number;
    let tick = 0;

    const loop = () => {
      tick = (tick + 1) % 600;

      EDGES.forEach((e, i) => {
        const phase = (tick / 90 + i * 0.27) % 1;
        const a = nodes[e.from];
        const b = nodes[e.to];
        const px = a.x + (b.x - a.x) * phase;
        const py = a.y + (b.y - a.y) * phase;

        const outer = packetRefsOuter.current[i];
        const inner = packetRefsInner.current[i];
        if (outer) {
          outer.setAttribute("cx", String(px));
          outer.setAttribute("cy", String(py));
        }
        if (inner) {
          inner.setAttribute("cx", String(px));
          inner.setAttribute("cy", String(py));
        }
      });

      rafId = requestAnimationFrame(loop);
    };

    rafId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafId);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [animate]);

  return (
    <div style={{ position: "relative", width, height }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <pattern id="sg-grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M 32 0 L 0 0 0 32" fill="none" stroke="var(--border)" strokeOpacity="0.4" strokeWidth="0.5" />
          </pattern>
          <radialGradient id="sg-glow" cx="0.5" cy="0.5">
            <stop offset="0" stopColor="var(--amber)" stopOpacity="0.4" />
            <stop offset="1" stopColor="var(--amber)" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Grid background */}
        <rect width={width} height={height} fill="url(#sg-grid)" />

        {/* Corner crosshairs */}
        {([[8, 8], [width - 8, 8], [8, height - 8], [width - 8, height - 8]] as [number, number][]).map(([x, y], i) => (
          <g key={i} stroke="var(--text-lo)" strokeOpacity="0.4">
            <line x1={x - 4} x2={x + 4} y1={y} y2={y} strokeWidth="0.6" />
            <line x1={x} x2={x} y1={y - 4} y2={y + 4} strokeWidth="0.6" />
          </g>
        ))}

        {/* Hub glow */}
        <circle cx={cx} cy={cy} r={60} fill="url(#sg-glow)" />

        {/* Edges */}
        {EDGES.map((e, i) => (
          <line
            key={i}
            x1={nodes[e.from].x} y1={nodes[e.from].y}
            x2={nodes[e.to].x}   y2={nodes[e.to].y}
            stroke="var(--text-lo)" strokeOpacity="0.35"
            strokeWidth="0.8" strokeDasharray="3 3"
          />
        ))}

        {/* Animated packets — positions updated imperatively via refs */}
        {animate && EDGES.map((_, i) => (
          <g key={i}>
            <circle
              ref={el => { packetRefsOuter.current[i] = el; }}
              cx={nodes[EDGES[i].from].x} cy={nodes[EDGES[i].from].y}
              r="6" fill="var(--amber)" opacity="0.25"
            />
            <circle
              ref={el => { packetRefsInner.current[i] = el; }}
              cx={nodes[EDGES[i].from].x} cy={nodes[EDGES[i].from].y}
              r="3" fill="var(--amber)"
            />
          </g>
        ))}

        {/* Hub */}
        <circle cx={cx} cy={cy} r="22" fill="var(--bg)" stroke="var(--amber)" strokeWidth="1" />
        <circle cx={cx} cy={cy} r="6" fill="var(--amber)" />
        <text x={cx} y={cy + 38} textAnchor="middle" fontFamily="var(--font-mono)" fontSize="9" fill="var(--text-lo)" letterSpacing="0.18em">SWARM</text>

        {/* Nodes */}
        {nodes.map(n => (
          <g key={n.id}>
            <circle cx={n.x} cy={n.y} r="18" fill="var(--surface)" stroke={n.color} strokeWidth="1" />
            <circle cx={n.x} cy={n.y} r="4" fill={n.color}>
              <animate attributeName="opacity" values="0.5;1;0.5" dur="1.4s" repeatCount="indefinite" />
            </circle>
            <text x={n.x} y={n.y + 32} textAnchor="middle" fontFamily="var(--font-mono)" fontSize="9"
                  fill={n.color} letterSpacing="0.18em" fontWeight="600">{n.label}</text>
            <text x={n.x} y={n.y + 44} textAnchor="middle" fontFamily="var(--font-mono)" fontSize="8.5"
                  fill="var(--text-lo)">{n.role}</text>
          </g>
        ))}
      </svg>

      <div style={{ position: "absolute", top: 8, left: 12, fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-lo)", letterSpacing: "0.18em" }}>
        SWARM · LIVE
      </div>
      <div style={{ position: "absolute", top: 8, right: 12, fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-lo)", letterSpacing: "0.18em" }}>
        4 AGENTS · 5 EDGES
      </div>
    </div>
  );
}

import type { CSSProperties, ReactNode } from "react"
import { SectionLabel } from "./SectionLabel"

interface PanelCardProps {
  heading: string
  children: ReactNode
  style?: CSSProperties
  className?: string
}

/**
 * Layout primitive used by the dossier grid. Wraps a `SectionLabel` header
 * over a content slot, with the standard Bloomberg surface treatment.
 */
export function PanelCard({ heading, children, style, className }: PanelCardProps) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 4,
        padding: "16px",
        fontFamily: "var(--font-sans)",
        ...style,
      }}
      className={className}
    >
      <div style={{ marginBottom: 12 }}>
        <SectionLabel>{heading}</SectionLabel>
      </div>
      <div style={{ color: "var(--text-md)", fontSize: 13, lineHeight: 1.6 }}>
        {children}
      </div>
    </div>
  )
}

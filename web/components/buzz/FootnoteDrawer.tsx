"use client"

import { useEffect } from "react"
import { AnimatePresence, motion } from "framer-motion"

export interface CitationRef {
  n: number
  url: string
}

interface FootnoteDrawerProps {
  open: boolean
  citation: CitationRef | null
  onClose: () => void
}

/**
 * Slide-in citation drawer. Backdrop fades in over 180ms; panel translates
 * 100% → 0 over 220ms (framer-motion). Pressing ESC closes the drawer while
 * it's open; clicking the backdrop closes it too. Domain is derived from the
 * URL via `new URL(...).hostname` and falls back to the raw URL on parse error.
 */
export function FootnoteDrawer({ open, citation, onClose }: FootnoteDrawerProps) {
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [open, onClose])

  let domain = ""
  if (citation) {
    try {
      domain = new URL(citation.url).hostname
    } catch {
      domain = citation.url
    }
  }

  return (
    <AnimatePresence>
      {open && citation && (
        <>
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            onClick={onClose}
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(0,0,0,0.55)",
              zIndex: 40,
            }}
          />
          <motion.div
            key="drawer"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            style={{
              position: "fixed",
              top: 0,
              right: 0,
              bottom: 0,
              width: 360,
              background: "var(--surface)",
              borderLeft: "1px solid var(--border)",
              zIndex: 50,
              padding: 24,
              fontFamily: "var(--font-sans)",
              overflowY: "auto",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 16,
              }}
            >
              <span
                style={{
                  color: "var(--text-lo)",
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  letterSpacing: "0.14em",
                }}
              >
                [{citation.n}]
              </span>
              <button
                onClick={onClose}
                aria-label="Close footnote drawer"
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--text-lo)",
                  cursor: "pointer",
                  fontSize: 18,
                  lineHeight: 1,
                  padding: 0,
                }}
              >
                ×
              </button>
            </div>
            <p
              style={{
                color: "var(--text-hi)",
                fontSize: 13,
                marginBottom: 8,
                wordBreak: "break-word",
                lineHeight: 1.5,
              }}
            >
              {citation.url}
            </p>
            {domain && (
              <p
                style={{
                  color: "var(--text-lo)",
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  letterSpacing: "0.08em",
                  margin: 0,
                }}
              >
                {domain}
              </p>
            )}
            <a
              href={citation.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "inline-block",
                marginTop: 20,
                padding: "8px 12px",
                border: "1px solid var(--cyan)",
                color: "var(--cyan)",
                fontFamily: "var(--font-mono)",
                fontSize: 10,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                textDecoration: "none",
              }}
            >
              ↗ Open source
            </a>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

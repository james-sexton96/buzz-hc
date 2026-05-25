"use client";

/**
 * StreamingDraft — renders the live reporter draft text in the Run screen.
 *
 * Part 4 of the Bloomberg-terminal redesign series. Displays:
 *   - Accumulated `draftText` from `useLiveSession`'s `reporter_token`
 *     SSE listener.
 *   - An 8×14 cyan blinking cursor while `status === "running"` (CSS
 *     `@keyframes blink`, 0.8s steps(2)). Cursor hidden on
 *     complete / error / paused.
 *   - "Compiling report…" placeholder when running and draftText is empty.
 *   - Citation marks `[N]` rendered as cyan <sup> elements.
 *
 * Invariants:
 *   - NEVER calls `requestAnimationFrame`. Cursor is purely CSS-driven.
 *   - NO lucide-react imports.
 *   - Uses `var(--font-mono)` / `var(--font-sans)` — never the legacy
 *     `var(--sans)` / `var(--mono)` aliases.
 */

import type { SessionStatus } from "@/lib/types";

interface StreamingDraftProps {
  draftText: string;
  status: SessionStatus;
}

// Animation-name is intentionally namespaced to avoid colliding with any
// future global @keyframes rule. The inline <style> tag scopes this CSS to
// the component (no CSS module / no Tailwind animation classes in the
// project — established convention from Parts 1-3).
const BLINK_STYLE = `
@keyframes streaming-draft-blink {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0; }
}
.streaming-draft-cursor {
  display: inline-block;
  width: 8px;
  height: 14px;
  background: var(--cyan);
  vertical-align: text-bottom;
  margin-left: 2px;
  animation: streaming-draft-blink 0.8s steps(2) infinite;
}
`;

/**
 * Tokenize a text string into alternating text runs and citation references
 * (`[N]` where N is a positive integer). Returns React-ready children.
 */
function renderWithCitations(text: string): React.ReactNode[] {
  if (!text) return [];
  const out: React.ReactNode[] = [];
  const re = /\[(\d+)\]/g;
  let lastIdx = 0;
  let m: RegExpExecArray | null;
  let key = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > lastIdx) {
      out.push(text.slice(lastIdx, m.index));
    }
    const n = parseInt(m[1], 10);
    out.push(
      <sup
        key={`cite-${key++}`}
        style={{
          color: "var(--cyan)",
          fontFamily: "var(--font-mono)",
          fontSize: "0.75em",
          padding: "0 1px",
        }}
      >
        [{n}]
      </sup>,
    );
    lastIdx = m.index + m[0].length;
  }
  if (lastIdx < text.length) {
    out.push(text.slice(lastIdx));
  }
  return out;
}

export function StreamingDraft({ draftText, status }: StreamingDraftProps) {
  const isRunning = status === "running";
  const isEmpty = draftText.length === 0;
  const showCursor = isRunning; // hide on complete / error / paused

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        padding: "16px 18px",
        fontFamily: "var(--font-sans)",
        color: "var(--text-md)",
        background: "var(--surface)",
        border: "1px solid var(--border)",
        overflow: "auto",
      }}
    >
      <style>{BLINK_STYLE}</style>
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 9,
          letterSpacing: "0.18em",
          color: "var(--text-lo)",
          marginBottom: 8,
          textTransform: "uppercase",
        }}
      >
        Emerging Draft
      </div>
      <div
        style={{
          flex: 1,
          fontSize: 13,
          lineHeight: 1.6,
          color: "var(--text-hi)",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {isRunning && isEmpty ? (
          <span style={{ color: "var(--text-lo)", fontStyle: "italic" }}>
            Compiling report…
            <span className="streaming-draft-cursor" aria-hidden="true" />
          </span>
        ) : (
          <>
            {renderWithCitations(draftText)}
            {showCursor && (
              <span className="streaming-draft-cursor" aria-hidden="true" />
            )}
          </>
        )}
      </div>
    </div>
  );
}

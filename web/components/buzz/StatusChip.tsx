"use client";

import { StatusDot } from "./StatusDot";

interface StatusChipProps {
  status: string;
  label?: string;
}

const CHIP_COLORS: Record<string, string> = {
  running:  "var(--cyan)",
  complete: "var(--green)",
  error:    "var(--red)",
  queued:   "var(--text-md)",
  paused:   "var(--amber)",
  live:     "var(--amber)",
};

export function StatusChip({ status, label }: StatusChipProps) {
  const c = CHIP_COLORS[status] ?? CHIP_COLORS.queued;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontFamily: "var(--font-mono)",
        fontSize: 10,
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        padding: "3px 7px",
        border: `1px solid ${c}40`,
        background: `${c}12`,
        color: c,
        borderRadius: 2,
      }}
    >
      <StatusDot status={status} pulse={status === "running"} />
      {label ?? status}
    </span>
  );
}

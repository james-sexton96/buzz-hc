"use client";

interface StatusDotProps {
  status: string;
  size?: number;
  pulse?: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  running:  "var(--cyan)",
  complete: "var(--green)",
  error:    "var(--red)",
  queued:   "var(--text-lo)",
  paused:   "var(--amber)",
  live:     "var(--amber)",
  idle:     "var(--text-lo)",
};

export function StatusDot({ status, size = 6, pulse = false }: StatusDotProps) {
  const color = STATUS_COLORS[status] ?? "var(--text-lo)";
  return (
    <span
      style={{
        display: "inline-block",
        width: size,
        height: size,
        background: color,
        borderRadius: 1,
        flexShrink: 0,
        boxShadow: pulse ? `0 0 8px ${color}` : undefined,
        animation: pulse ? "buzz-pulse 1.8s ease-in-out infinite" : undefined,
      }}
    />
  );
}

"use client"

interface DonutChartProps {
  filled: number  // 0–1
  size?: number
  strokeWidth?: number
  color?: string
  trackColor?: string
}

/**
 * Pure SVG donut chart. `filled` is clamped to [0, 1].
 * Rotates -90deg so the arc starts at 12 o'clock.
 */
export function DonutChart({
  filled,
  size = 80,
  strokeWidth = 10,
  color = "var(--cyan)",
  trackColor = "var(--border)",
}: DonutChartProps) {
  const r = (size - strokeWidth) / 2
  const cx = size / 2
  const cy = size / 2
  const circumference = 2 * Math.PI * r
  const clamped = Math.max(0, Math.min(1, filled))
  const arc = clamped * circumference
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ display: "block" }}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={trackColor} strokeWidth={strokeWidth} />
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeDasharray={`${arc} ${circumference - arc}`}
        strokeDashoffset={circumference / 4}
        strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`}
      />
    </svg>
  )
}

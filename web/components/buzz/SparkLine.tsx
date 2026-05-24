"use client"

interface SparkLineProps {
  color?: string
  width?: number
  height?: number
}

/**
 * Pure SVG sparkline with a static flat-line placeholder.
 * `MarketSize` is not a time series in the schema, so we don't synthesize
 * trend data — explicit placeholder is honest. Caller can size/color it.
 */
export function SparkLine({ color = "var(--cyan)", width = 80, height = 24 }: SparkLineProps) {
  const data = [0, 2, 1, 3, 2, 1, 3, 2]
  const points = data.map((y, i) => `${(i / (data.length - 1)) * width},${height / 2 - y}`)
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: "block" }}>
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

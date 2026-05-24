interface SectionLabelProps {
  children: React.ReactNode;
  accent?: string;
}

export function SectionLabel({ children, accent = "var(--amber)" }: SectionLabelProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        fontFamily: "var(--font-mono)",
        fontSize: 10,
        letterSpacing: "0.18em",
        textTransform: "uppercase",
        color: "var(--text-md)",
      }}
    >
      <span style={{ width: 4, height: 4, background: accent, display: "inline-block" }} />
      {children}
    </div>
  );
}

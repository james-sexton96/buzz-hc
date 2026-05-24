"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";

const TICKER_ITEMS = [
  [{ sym: "GLP-1", val: "+$130B", c: "var(--green)" }, { sym: "CAR-T", val: "+12.4%", c: "var(--green)" }, { sym: "FDA", val: "47 IND", c: "var(--text-md)" }],
  [{ sym: "ADC", val: "+18.2%", c: "var(--green)" }, { sym: "AAV", val: "−2.1%", c: "var(--red)" }, { sym: "NICE", val: "3 TAs", c: "var(--text-md)" }],
  [{ sym: "OBES", val: "+22.8%", c: "var(--green)" }, { sym: "GENE", val: "+3.2%", c: "var(--green)" }, { sym: "EMA", val: "12 ATMP", c: "var(--text-md)" }],
];

const NAV_LINKS = [
  { id: "research", label: "Research", href: "/" },
  { id: "sessions", label: "Sessions", href: "/sessions" },
  { id: "library",  label: "Library",  href: "/" },
  { id: "models",   label: "Models",   href: "/" },
];

function BuzzLogo() {
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
      <svg width={18} height={18} viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="2.2" fill="var(--amber)" />
        <circle cx="10" cy="10" r="5" stroke="var(--amber)" strokeOpacity="0.6" strokeWidth="1" fill="none" />
        <circle cx="10" cy="10" r="8.4" stroke="var(--amber)" strokeOpacity="0.25" strokeWidth="1" fill="none" />
        <circle cx="10" cy="1.8" r="1.1" fill="var(--amber)" />
        <circle cx="17.6" cy="13.8" r="1.1" fill="var(--amber)" opacity="0.7" />
        <circle cx="2.4" cy="13.8" r="1.1" fill="var(--amber)" opacity="0.4" />
      </svg>
      <span style={{
        fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.18em",
        fontWeight: 600, color: "var(--text-hi)", textTransform: "uppercase",
      }}>
        BUZZ<span style={{ color: "var(--amber)" }}>·</span>HC
      </span>
    </div>
  );
}

function Ticker() {
  const [t, setT] = useState(0);
  useEffect(() => {
    const i = setInterval(() => setT(x => x + 1), 4000);
    return () => clearInterval(i);
  }, []);
  const cur = TICKER_ITEMS[t % TICKER_ITEMS.length];
  return (
    <div style={{
      display: "flex", gap: 12, padding: "3px 8px",
      border: "1px solid var(--border)", borderRadius: 2, background: "var(--surface)",
    }}>
      {cur.map(it => (
        <div key={it.sym} style={{ display: "flex", gap: 5, alignItems: "center", fontFamily: "var(--font-mono)", fontSize: 10 }}>
          <span style={{ color: "var(--text-lo)" }}>{it.sym}</span>
          <span style={{ color: it.c }}>{it.val}</span>
        </div>
      ))}
    </div>
  );
}

function resolveActive(pathname: string): string {
  if (pathname === "/sessions") return "sessions";
  if (pathname.startsWith("/report")) return "sessions";
  if (pathname.startsWith("/query") || pathname.startsWith("/run")) return "research";
  return "research";
}

export function TopNav() {
  const pathname = usePathname();
  const active = resolveActive(pathname);

  return (
    <header style={{
      height: 44,
      borderBottom: "1px solid var(--border)",
      display: "flex", alignItems: "center",
      padding: "0 16px", background: "var(--bg)",
      gap: 24, flexShrink: 0, position: "sticky", top: 0, zIndex: 10,
    }}>
      <Link href="/"><BuzzLogo /></Link>
      <div style={{ height: 16, width: 1, background: "var(--border)" }} />
      <nav style={{ display: "flex", gap: 2, flex: 1 }}>
        {NAV_LINKS.map(l => (
          <Link
            key={l.id}
            href={l.href}
            style={{
              fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.12em",
              textTransform: "uppercase", padding: "6px 10px",
              color: l.id === active ? "var(--text-hi)" : "var(--text-lo)",
              borderBottom: l.id === active ? "2px solid var(--amber)" : "2px solid transparent",
              marginBottom: -1,
              textDecoration: "none",
            }}
          >
            {l.label}
          </Link>
        ))}
      </nav>
      <Ticker />
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-lo)", letterSpacing: "0.08em" }}>Search</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, padding: "2px 5px", border: "1px solid var(--border)", borderRadius: 2, color: "var(--text-md)" }}>⌘K</span>
      </div>
      <div style={{
        width: 22, height: 22, borderRadius: 11,
        background: "var(--surface-2)", border: "1px solid var(--border)",
        fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-md)",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>JS</div>
    </header>
  );
}

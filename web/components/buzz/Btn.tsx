"use client";

import { ButtonHTMLAttributes } from "react";

interface BtnProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  primary?: boolean;
  mini?: boolean;
}

export function Btn({ children, primary = false, mini = false, disabled, onClick, ...rest }: BtnProps) {
  return (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      {...rest}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontFamily: "var(--font-mono)",
        fontSize: 10,
        letterSpacing: "0.14em",
        textTransform: "uppercase",
        fontWeight: 600,
        padding: mini ? "4px 8px" : "8px 14px",
        background: primary ? "var(--amber)" : "transparent",
        color: primary ? "#0a0d14" : "var(--text-hi)",
        border: primary ? "1px solid var(--amber)" : "1px solid var(--border)",
        borderRadius: 2,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        transition: "background 0.15s",
        ...rest.style,
      }}
    >
      {children}
    </button>
  );
}

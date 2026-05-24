"use client"
import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function RunPage() {
  const router = useRouter()
  useEffect(() => { router.replace("/query") }, [router])
  return <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-lo)", padding: 32 }}>Redirecting…</div>
}

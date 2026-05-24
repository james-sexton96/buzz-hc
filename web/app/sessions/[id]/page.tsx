"use client"
import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { getSession } from "@/lib/api"

export default function SessionRedirectPage() {
  const params = useParams<{ id: string }>()
  const id = params.id
  const router = useRouter()
  const [msg, setMsg] = useState("Loading…")

  useEffect(() => {
    getSession(id).then(s => {
      if (s.status === "complete") {
        router.replace("/report/" + id)
      } else {
        router.replace("/run/" + id)
      }
    }).catch(() => {
      setMsg("Session not found")
    })
  }, [id, router])

  return <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-lo)", padding: 32 }}>{msg}</div>
}

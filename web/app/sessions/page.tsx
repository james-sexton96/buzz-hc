"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getSessions } from "@/lib/api";
import type { SessionSummary, SessionStatus } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { ChevronRight, FlaskConical } from "lucide-react";

function StatusBadge({ status }: { status: SessionStatus }) {
  if (status === "running") return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-[var(--status-running-bg)] text-[var(--status-running-fg)]">
      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      Running
    </span>
  );
  if (status === "complete") return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-[var(--status-complete-bg)] text-[var(--status-complete-fg)]">
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      Complete
    </span>
  );
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-[var(--status-error-bg)] text-[var(--status-error-fg)]">
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      Error
    </span>
  );
}

function formatDate(ts: string): string {
  try {
    return new Date(ts).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

export default function SessionsPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load(q: string) {
    setLoading(true);
    setError(null);
    try {
      const data = await getSessions({ search: q, limit: 50 });
      setSessions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load("");
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    load(search);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Research History</h1>
          <p className="text-muted-foreground text-sm mt-1">
            All past research sessions, newest first.
          </p>
        </div>
        <Link href="/run" className={cn(buttonVariants(), "rounded-full")}>
          + New Research
        </Link>
      </div>

      <form onSubmit={handleSearch} className="max-w-md">
        <div className="flex rounded-xl border border-input overflow-hidden">
          <Input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search queries…"
            className="flex-1 border-0 rounded-none focus-visible:ring-0 focus-visible:ring-offset-0"
          />
          <Button type="submit" variant="secondary" className="rounded-none rounded-r-xl border-0 border-l border-input">
            Search
          </Button>
        </div>
      </form>

      {loading && (
        <div className="flex items-center justify-center py-16 text-muted-foreground text-sm">
          Loading sessions…
        </div>
      )}

      {error && (
        <Card className="rounded-2xl">
          <CardContent className="pt-6 text-sm text-destructive text-center">
            {error}
          </CardContent>
        </Card>
      )}

      {!loading && !error && sessions.length === 0 && (
        <Card className="rounded-2xl">
          <CardContent className="pt-12 pb-12 text-center space-y-3">
            <div className="flex justify-center">
              <FlaskConical className="w-10 h-10 text-muted-foreground/40" />
            </div>
            <p className="font-medium text-sm">No research sessions yet</p>
            <p className="text-xs text-muted-foreground">Run your first query to see results here.</p>
            <Link href="/run" className={cn(buttonVariants({ variant: "outline", size: "sm" }), "rounded-full")}>
              Start your first research run
            </Link>
          </CardContent>
        </Card>
      )}

      {!loading && sessions.length > 0 && (
        <Card className="rounded-2xl shadow-sm">
          <div className="divide-y divide-border">
            {sessions.map((s) => (
              <Link
                key={s.session_id}
                href={`/sessions/${s.session_id}`}
                className="flex items-center justify-between gap-4 px-5 py-4 hover:bg-muted/40 transition-colors group"
              >
                <div className="space-y-1 min-w-0">
                  <p className="text-sm font-medium leading-snug line-clamp-2">
                    {s.query}
                  </p>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={s.status} />
                    <span className="text-xs text-muted-foreground">
                      {formatDate(s.timestamp)}
                    </span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-muted-foreground/40 shrink-0 group-hover:text-muted-foreground transition-colors" />
              </Link>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useLiveSession } from "@/hooks/useLiveSession";
import { getPdfUrl, retrySession } from "@/lib/api";
import { ReportViewer } from "@/components/report/ReportViewer";
import { EventFeed } from "@/components/run/EventFeed";
import { PipelineProgress } from "@/components/run/PipelineProgress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { RunPhase, WorkflowEvent } from "@/lib/types";

const STATUS_CONFIG: Record<string, { dot: string; pulse: boolean; label: string }> = {
  running:  { dot: "bg-blue-500",  pulse: true,  label: "Running" },
  complete: { dot: "bg-green-500", pulse: false, label: "Complete" },
  error:    { dot: "bg-red-500",   pulse: false, label: "Error" },
};

function statusToPhase(status: string, isStreaming: boolean): RunPhase {
  if (isStreaming || status === "running") return "running";
  if (status === "complete") return "complete";
  if (status === "error") return "error";
  return "idle";
}

function formatDate(ts: string): string {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

export default function SessionDetailPage() {
  const params = useParams<{ id: string }>();
  const sessionId = params.id;
  const router = useRouter();
  const [showEvents, setShowEvents] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  const { session, liveEvents, isLoading, isStreaming, error } = useLiveSession(sessionId);

  async function handleRetry() {
    setIsRetrying(true);
    try {
      const { session_id } = await retrySession(sessionId);
      router.push(`/sessions/${session_id}`);
    } catch {
      setIsRetrying(false);
    }
  }

  function retryLabel(): string {
    if (!session) return "Retry";
    if (session.research_json && session.analyst_json) return "Retry Reporter";
    if (session.research_json) return "Retry from Analyst";
    return "Retry Full Run";
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24 text-muted-foreground text-sm">
        Loading session…
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <p className="text-destructive text-sm">{error ?? "Session not found"}</p>
        <Link href="/sessions" className={cn(buttonVariants({ variant: "outline", size: "sm" }), "rounded-full")}>
          ← Back to history
        </Link>
      </div>
    );
  }

  const statusCfg = STATUS_CONFIG[session.status] ?? { dot: "bg-gray-400", pulse: false, label: session.status };
  const phase = statusToPhase(session.status, isStreaming);

  const displayEvents: WorkflowEvent[] = isStreaming
    ? [...(session.events ?? []), ...liveEvents]
    : (session.events ?? []);

  return (
    <div className="space-y-5 max-w-3xl mx-auto">
      {/* Header */}
      <div className="space-y-3">
        <Link
          href="/sessions"
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          ← Research History
        </Link>
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-xl font-semibold leading-snug">{session.query}</h1>
          <div className="flex items-center gap-2 shrink-0 mt-0.5">
            <span
              className={cn(
                "w-2 h-2 rounded-full",
                statusCfg.dot,
                statusCfg.pulse && "animate-pulse"
              )}
            />
            <span className="text-xs font-medium text-muted-foreground">{statusCfg.label}</span>
            {session.status === "error" && (
              <Button
                size="sm"
                variant="outline"
                className="rounded-full text-xs h-7 px-3"
                onClick={handleRetry}
                disabled={isRetrying}
              >
                {isRetrying ? "Retrying…" : `↺ ${retryLabel()}`}
              </Button>
            )}
          </div>
        </div>
        <p className="text-xs text-muted-foreground">{formatDate(session.timestamp)}</p>
      </div>

      {/* Live pipeline card — shown while running */}
      {(isStreaming || session.status === "running") && (
        <Card className="rounded-2xl shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
              Pipeline running…
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <PipelineProgress events={displayEvents} phase={phase} />
            <Separator />
            <EventFeed events={displayEvents} />
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {session.error_msg && (
        <div className="rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
          {session.error_msg}
        </div>
      )}

      {/* Report */}
      {session.report && (
        <Card className="rounded-2xl shadow-sm">
          <CardContent className="pt-6 pb-6">
            <ReportViewer
              report={session.report}
              pdfUrl={getPdfUrl(sessionId)}
            />
          </CardContent>
        </Card>
      )}

      {/* Collapsible event trace for completed sessions */}
      {!isStreaming && session.status !== "running" && displayEvents.length > 0 && (
        <Card className="rounded-2xl shadow-sm">
          <CardHeader
            className="pb-2 cursor-pointer select-none"
            onClick={() => setShowEvents((v) => !v)}
          >
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center justify-between">
              <span>Pipeline trace · {displayEvents.length} events</span>
              <span className="text-xs">{showEvents ? "▲ hide" : "▼ show"}</span>
            </CardTitle>
          </CardHeader>
          {showEvents && (
            <CardContent className="pt-0">
              <EventFeed events={displayEvents} maxHeight="400px" />
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
}

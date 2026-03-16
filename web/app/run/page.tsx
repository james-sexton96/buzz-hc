"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { QueryForm } from "@/components/run/QueryForm";
import { PipelineProgress } from "@/components/run/PipelineProgress";
import { EventFeed } from "@/components/run/EventFeed";
import { ReportViewer } from "@/components/report/ReportViewer";
import { useRunSession } from "@/hooks/useRunSession";
import { getPdfUrl } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

export default function RunPage() {
  const { state, run, reset } = useRunSession();
  const router = useRouter();
  const isRunning = state.phase === "starting" || state.phase === "running";
  const isActive = state.phase !== "idle";

  return (
    <div className="space-y-5 max-w-3xl mx-auto">
      {/* Zone 1: Input */}
      <Card className={cn("rounded-2xl shadow-sm transition-all duration-500", isActive && "opacity-50 scale-[0.99] pointer-events-none")}>
        <CardContent className="pt-6 pb-6">
          <QueryForm onSubmit={run} disabled={isRunning} />
        </CardContent>
      </Card>

      {/* Zone 2: Pipeline + events */}
      {isActive && (
        <Card className="rounded-2xl shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Pipeline</CardTitle>
              <div className="flex items-center gap-2">
                {state.sessionId && (
                  <Link
                    href={`/sessions/${state.sessionId}`}
                    className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "h-7 text-xs text-muted-foreground")}
                  >
                    Session ↗
                  </Link>
                )}
                {!isRunning && (
                  <Button variant="outline" size="sm" className="h-7 text-xs rounded-full" onClick={reset}>
                    New run
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <PipelineProgress events={state.events} phase={state.phase} />

            {state.phase === "error" && state.error && (
              <div className="rounded-lg bg-destructive/10 border border-destructive/20 px-3 py-2 text-sm text-destructive">
                {state.error}
              </div>
            )}

            <Separator />
            <EventFeed events={state.events} />
          </CardContent>
        </Card>
      )}

      {/* Zone 3: Report */}
      {state.phase === "complete" && state.report && (
        <Card className="rounded-2xl shadow-sm">
          <CardContent className="pt-6 pb-6">
            <ReportViewer
              report={state.report}
              pdfUrl={state.sessionId ? getPdfUrl(state.sessionId) : undefined}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

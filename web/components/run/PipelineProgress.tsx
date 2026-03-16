"use client";

import { Search, BarChart2, FileText, CheckCircle2 } from "lucide-react";
import type { RunPhase, WorkflowEvent } from "@/lib/types";
import { cn } from "@/lib/utils";

const STAGES = [
  { key: "Researcher", label: "Market Research",   subtitle: "Gathering market data",  Icon: Search },
  { key: "Analyst",    label: "Data Analysis",     subtitle: "Synthesizing insights",  Icon: BarChart2 },
  { key: "Reporter",   label: "Report Generation", subtitle: "Generating report",       Icon: FileText },
] as const;

type StageStatus = "pending" | "active" | "done";

function getStageStatuses(
  events: WorkflowEvent[],
  phase: RunPhase
): Record<string, StageStatus> {
  const statuses: Record<string, StageStatus> = {};
  for (const stage of STAGES) {
    const started = events.some(
      (e) => e.source === stage.key && e.event_type === "agent_start"
    );
    const ended = events.some(
      (e) => e.source === stage.key && e.event_type === "agent_end"
    );
    if (ended || phase === "complete") {
      statuses[stage.key] = "done";
    } else if (started) {
      statuses[stage.key] = "active";
    } else {
      statuses[stage.key] = "pending";
    }
  }
  return statuses;
}

interface PipelineProgressProps {
  events: WorkflowEvent[];
  phase: RunPhase;
}

export function PipelineProgress({ events, phase }: PipelineProgressProps) {
  const statuses = getStageStatuses(events, phase);

  return (
    <div className="flex items-start gap-0">
      {STAGES.map((stage, i) => {
        const status = statuses[stage.key];
        const isLast = i === STAGES.length - 1;

        return (
          <div key={stage.key} className="flex items-start flex-1 last:flex-none">
            {/* Stage node */}
            <div className="flex flex-col items-center gap-2 relative">
              <div
                className={cn(
                  "w-9 h-9 rounded-full flex items-center justify-center transition-all duration-500",
                  status === "done"    && "bg-emerald-50 border-2 border-emerald-500",
                  status === "active"  && "bg-primary/10 border-2 border-primary ring-4 ring-primary/10",
                  status === "pending" && "bg-muted border-2 border-border"
                )}
              >
                {status === "done" && (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                )}
                {status === "active" && (
                  <stage.Icon className="w-4 h-4 text-primary animate-pulse" />
                )}
                {status === "pending" && (
                  <span className="w-2 h-2 rounded-full bg-border" />
                )}
              </div>

              <div className="text-center">
                <p
                  className={cn(
                    "text-xs font-medium whitespace-nowrap transition-colors",
                    status === "done"    && "text-emerald-700",
                    status === "active"  && "text-primary font-semibold",
                    status === "pending" && "text-muted-foreground"
                  )}
                >
                  {stage.label}
                </p>
                {status === "active" && (
                  <p className="text-[10px] text-muted-foreground">{stage.subtitle}</p>
                )}
                {status === "done" && (
                  <p className="text-[10px] text-emerald-600">Complete</p>
                )}
              </div>
            </div>

            {/* Connector line */}
            {!isLast && (
              <div className="flex-1 h-px mt-[18px] mx-2 bg-border overflow-hidden">
                <div
                  className={cn(
                    "h-full transition-all duration-700",
                    status === "done" ? "bg-emerald-400 w-full" : "bg-transparent w-0"
                  )}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

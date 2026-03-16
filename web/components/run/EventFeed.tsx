"use client";

import { useEffect, useRef } from "react";
import type { WorkflowEvent } from "@/lib/types";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

const EVENT_COLORS: Record<string, { source: string; message: string }> = {
  agent_start: { source: "text-indigo-400", message: "text-zinc-300" },
  agent_end:   { source: "text-indigo-400", message: "text-zinc-300" },
  tool_call:   { source: "text-amber-400",  message: "text-zinc-400" },
  tool_result: { source: "text-emerald-400", message: "text-zinc-400" },
  info:        { source: "text-zinc-500",   message: "text-zinc-400" },
  agent_limit: { source: "text-red-400",    message: "text-red-300" },
};

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "";
  }
}

interface EventFeedProps {
  events: WorkflowEvent[];
  maxHeight?: string;
}

export function EventFeed({ events, maxHeight = "280px" }: EventFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  return (
    <div className="rounded-xl overflow-hidden ring-1 ring-zinc-800">
      {/* Terminal header */}
      <div className="bg-zinc-900 px-4 py-2.5 flex items-center gap-2">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-red-500/80" />
          <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
          <span className="w-3 h-3 rounded-full bg-green-500/80" />
        </div>
        <span className="ml-2 text-xs text-zinc-500 font-mono">Agent Log</span>
      </div>

      {/* Terminal body */}
      <div className="bg-zinc-950">
        {events.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <span className="text-xs text-zinc-600 font-mono italic">
              Waiting for events…
            </span>
          </div>
        ) : (
          <ScrollArea style={{ maxHeight }} className="px-4 py-3">
            <div className="space-y-1">
              {events.map((ev, i) => {
                const colors = EVENT_COLORS[ev.event_type] ?? EVENT_COLORS.info;
                return (
                  <div key={i} className="flex items-start gap-2 text-xs font-mono leading-relaxed">
                    <span className="shrink-0 text-zinc-600 tabular-nums w-[72px]">
                      {formatTime(ev.timestamp)}
                    </span>
                    <span className={cn("shrink-0 w-20 truncate", colors.source)}>
                      {ev.source}
                    </span>
                    <span className={cn("flex-1 break-words", colors.message)}>
                      {ev.message}
                    </span>
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>
          </ScrollArea>
        )}
      </div>
    </div>
  );
}

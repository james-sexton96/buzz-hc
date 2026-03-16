"use client";

import { useCallback, useRef, useState } from "react";
import { getSession, getStreamUrl, startRun } from "@/lib/api";
import type { MarketReport, RunState, WorkflowEvent } from "@/lib/types";

const INITIAL_STATE: RunState = {
  phase: "idle",
  sessionId: null,
  events: [],
  report: null,
  error: null,
};

export function useRunSession() {
  const [state, setState] = useState<RunState>(INITIAL_STATE);
  const esRef = useRef<EventSource | null>(null);

  const reset = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    setState(INITIAL_STATE);
  }, []);

  const run = useCallback(
    async (query: string, tavilyApiKey = "") => {
      reset();
      setState((s) => ({ ...s, phase: "starting" }));

      let sessionId: string;
      try {
        const result = await startRun(query, tavilyApiKey);
        sessionId = result.session_id;
      } catch (err) {
        setState((s) => ({
          ...s,
          phase: "error",
          error: err instanceof Error ? err.message : String(err),
        }));
        return;
      }

      setState((s) => ({ ...s, phase: "running", sessionId }));

      const es = new EventSource(getStreamUrl(sessionId));
      esRef.current = es;

      es.addEventListener("workflow_event", (e: MessageEvent) => {
        try {
          const event: WorkflowEvent = JSON.parse(e.data);
          setState((s) => ({ ...s, events: [...s.events, event] }));
        } catch {
          // ignore malformed events
        }
      });

      es.addEventListener("done", async (e: MessageEvent) => {
        es.close();
        esRef.current = null;
        try {
          const terminal: { session_id: string; status: string } = JSON.parse(
            e.data
          );
          if (terminal.status === "complete") {
            const detail = await getSession(terminal.session_id);
            setState((s) => ({
              ...s,
              phase: "complete",
              report: detail.report ?? null,
            }));
          } else {
            setState((s) => ({
              ...s,
              phase: "error",
              error: "Pipeline finished with errors. Check session detail.",
            }));
          }
        } catch (err) {
          setState((s) => ({
            ...s,
            phase: "error",
            error: err instanceof Error ? err.message : String(err),
          }));
        }
      });

      es.onerror = () => {
        es.close();
        esRef.current = null;
        setState((s) => {
          if (s.phase === "running") {
            return {
              ...s,
              phase: "error",
              error: "Connection to server lost.",
            };
          }
          return s;
        });
      };
    },
    [reset]
  );

  return { state, run, reset };
}

"use client";

/**
 * Hook for watching a session that may currently be running.
 * - If status is "running", connects to the SSE stream for live events.
 * - When the stream closes (done event), fetches the full session from the DB.
 * - If status is already complete/error, returns the data as-is.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { getSession, getStreamUrl } from "@/lib/api";
import type { SessionDetail, WorkflowEvent } from "@/lib/types";

export interface LiveSessionState {
  session: SessionDetail | null;
  liveEvents: WorkflowEvent[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
}

export function useLiveSession(sessionId: string) {
  const [state, setState] = useState<LiveSessionState>({
    session: null,
    liveEvents: [],
    isLoading: true,
    isStreaming: false,
    error: null,
  });
  const esRef = useRef<EventSource | null>(null);

  const loadAndMaybeStream = useCallback(async () => {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    let detail: SessionDetail;
    try {
      detail = await getSession(sessionId);
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoading: false,
        error: err instanceof Error ? err.message : String(err),
      }));
      return;
    }

    setState((s) => ({ ...s, session: detail, isLoading: false }));

    if (detail.status !== "running") return;

    // Session is still running — connect to its SSE stream
    const es = new EventSource(getStreamUrl(sessionId));
    esRef.current = es;
    setState((s) => ({ ...s, isStreaming: true }));

    es.addEventListener("workflow_event", (e: MessageEvent) => {
      try {
        const event: WorkflowEvent = JSON.parse(e.data);
        setState((s) => ({ ...s, liveEvents: [...s.liveEvents, event] }));
      } catch {
        // ignore
      }
    });

    es.addEventListener("done", async () => {
      es.close();
      esRef.current = null;
      // Fetch the final completed session from DB
      try {
        const final = await getSession(sessionId);
        setState((s) => ({ ...s, session: final, isStreaming: false, liveEvents: [] }));
      } catch {
        setState((s) => ({ ...s, isStreaming: false }));
      }
    });

    es.onerror = () => {
      es.close();
      esRef.current = null;
      setState((s) => ({ ...s, isStreaming: false }));
    };
  }, [sessionId]);

  useEffect(() => {
    loadAndMaybeStream();
    return () => {
      esRef.current?.close();
      esRef.current = null;
    };
  }, [loadAndMaybeStream]);

  return state;
}

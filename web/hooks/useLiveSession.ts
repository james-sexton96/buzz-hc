"use client";

/**
 * Hook for watching a session that may currently be running.
 * - If status is "running", connects to the SSE stream for live events.
 * - When the stream closes (done event), fetches the full session from the DB.
 * - If status is already complete/error, returns the data as-is.
 *
 * Part 4: Adds `reporter_token` SSE listener that accumulates chunks into
 * a `draftText` string. This is done on the *existing* EventSource — no
 * second `EventSource` is opened. `draftText` resets on session id change.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { getSession, getStreamUrl } from "@/lib/api";
import type { ReporterTokenEvent, SessionDetail, WorkflowEvent } from "@/lib/types";

export interface LiveSessionState {
  session: SessionDetail | null;
  liveEvents: WorkflowEvent[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  /**
   * Accumulated reporter draft text — appended in order from `reporter_token`
   * SSE events. Resets to `""` on session id change.
   */
  draftText: string;
}

export function useLiveSession(sessionId: string) {
  const [state, setState] = useState<LiveSessionState>({
    session: null,
    liveEvents: [],
    isLoading: true,
    isStreaming: false,
    error: null,
    draftText: "",
  });
  const esRef = useRef<EventSource | null>(null);
  // Highest token_index appended so far — used to defensively skip
  // out-of-order stragglers if any arrive after a higher index.
  const lastTokenIndexRef = useRef<number>(-1);

  const loadAndMaybeStream = useCallback(async () => {
    // Reset all per-session state when sessionId changes (or on first mount).
    lastTokenIndexRef.current = -1;
    setState({
      session: null,
      liveEvents: [],
      isLoading: true,
      isStreaming: false,
      error: null,
      draftText: "",
    });

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

    // Session is still running — connect to its SSE stream (single EventSource).
    const es = new EventSource(getStreamUrl(sessionId));
    esRef.current = es;
    setState((s) => ({ ...s, isStreaming: true }));

    es.addEventListener("workflow_event", (e: MessageEvent) => {
      try {
        const event: WorkflowEvent = JSON.parse(e.data);
        setState((s) => ({ ...s, liveEvents: [...s.liveEvents, event] }));
      } catch {
        // ignore malformed payload
      }
    });

    // Part 4: reporter_token listener on the SAME EventSource.
    es.addEventListener("reporter_token", (e: MessageEvent) => {
      try {
        const evt = JSON.parse(e.data) as ReporterTokenEvent;
        if (typeof evt.chunk !== "string") return;
        // Defensive: skip stragglers whose token_index is not newer than the
        // highest we've appended. Equal indices are also skipped (duplicate
        // delivery is treated as redundant).
        if (typeof evt.token_index === "number") {
          if (evt.token_index <= lastTokenIndexRef.current) return;
          lastTokenIndexRef.current = evt.token_index;
        }
        setState((s) => ({ ...s, draftText: s.draftText + evt.chunk }));
      } catch {
        // ignore malformed payload
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

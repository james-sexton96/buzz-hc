"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { startRun } from "@/lib/api";
import type { RunState } from "@/lib/types";

const INITIAL_STATE: RunState = {
  phase: "idle",
  sessionId: null,
  events: [],
  report: null,
  error: null,
};

export function useRunSession() {
  const [state, setState] = useState<RunState>(INITIAL_STATE);
  const router = useRouter();

  const reset = useCallback(() => {
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

      router.push("/run/" + sessionId);
      setState((s) => ({ ...s, phase: "running", sessionId }));
    },
    [reset, router]
  );

  return { state, run, reset };
}

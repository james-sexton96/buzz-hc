/** Typed fetch wrappers for the Buzz-HC FastAPI backend. */

import type {
  HealthCheck,
  RunResponse,
  Scenario,
  SessionDetail,
  SessionSummary,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function startRun(
  query: string,
  tavilyApiKey = ""
): Promise<RunResponse> {
  return apiFetch<RunResponse>("/run", {
    method: "POST",
    body: JSON.stringify({ query, tavily_api_key: tavilyApiKey }),
  });
}

export function getStreamUrl(sessionId: string): string {
  return `${API_BASE}/run/${sessionId}/stream`;
}

export async function getSessions(params?: {
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<SessionSummary[]> {
  const qs = new URLSearchParams();
  if (params?.search) qs.set("search", params.search);
  if (params?.limit != null) qs.set("limit", String(params.limit));
  if (params?.offset != null) qs.set("offset", String(params.offset));
  const query = qs.toString() ? `?${qs}` : "";
  return apiFetch<SessionSummary[]>(`/sessions${query}`);
}

export async function getSession(sessionId: string): Promise<SessionDetail> {
  return apiFetch<SessionDetail>(`/sessions/${sessionId}`);
}

export function getPdfUrl(sessionId: string): string {
  return `${API_BASE}/sessions/${sessionId}/pdf`;
}

export async function getScenarios(): Promise<Scenario[]> {
  return apiFetch<Scenario[]>("/config/scenarios");
}

export async function getHealth(): Promise<HealthCheck> {
  return apiFetch<HealthCheck>("/config/health");
}

export async function retrySession(
  sessionId: string
): Promise<{ session_id: string; stream_url: string }> {
  return apiFetch(`/run/${sessionId}/retry`, { method: "POST" });
}

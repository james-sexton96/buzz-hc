/** TypeScript interfaces mirroring Python schema models. */

export type EventType =
  | "agent_start"
  | "tool_call"
  | "tool_result"
  | "agent_end"
  | "info"
  | "agent_limit";

export interface WorkflowEvent {
  timestamp: string;
  event_type: EventType;
  source: string;
  message: string;
  details?: unknown;
}

export interface ReportSection {
  heading: string;
  content: string;
}

export interface MarketReport {
  title: string;
  executive_summary: string;
  sections: ReportSection[];
  sources: string[];
  markdown_content?: string | null;
}

export interface UsageStats {
  requests: number;
  total_tokens: number;
  request_tokens: number;
  response_tokens: number;
}

export type SessionStatus = "running" | "complete" | "error";

export interface SessionSummary {
  session_id: string;
  timestamp: string;
  query: string;
  status: SessionStatus;
  error_msg?: string | null;
}

export interface SessionDetail extends SessionSummary {
  report?: MarketReport | null;
  events: WorkflowEvent[];
  usage: UsageStats | Record<string, never>;
  research_json?: string | null;
  analyst_json?: string | null;
}

export interface RunResponse {
  session_id: string;
  stream_url: string;
}

export interface Scenario {
  label: string;
  query: string;
  description: string;
}

export interface HealthCheck {
  status: string;
  llm_provider: string;
  llm_model: string;
  ollama_base_url?: string | null;
  tavily_configured: boolean;
}

export type RunPhase =
  | "idle"
  | "starting"
  | "running"
  | "complete"
  | "error";

export interface RunState {
  phase: RunPhase;
  sessionId: string | null;
  events: WorkflowEvent[];
  report: MarketReport | null;
  error: string | null;
}

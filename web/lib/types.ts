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

/**
 * Optional per-country market mix entry — mirrors Python `CountryMixEntry`.
 * Part 4 dossier panel: rendered only when `MarketReport.country_mix` is
 * non-null and non-empty.
 */
export interface CountryMixEntry {
  country: string;
  share_2024?: number | null;
  share_2030?: number | null;
  spend_2024?: string | null;
  spend_2030?: string | null;
  notes?: string | null;
}

/**
 * Optional scenario/risk entry — mirrors Python `ScenarioEntry`.
 * Part 4 dossier panel: rendered only when `MarketReport.scenario_probabilities`
 * is non-null and non-empty.
 */
export interface ScenarioEntry {
  scenario: string;
  probability_pct?: number | null;
  description?: string | null;
  impact?: string | null;
}

export interface MarketReport {
  title: string;
  executive_summary: string;
  sections: ReportSection[];
  sources: string[];
  markdown_content?: string | null;
  /**
   * Optional country-mix breakdown. Null/undefined for pre-Part-4 reports.
   * Rendered as a dossier panel only when non-null and non-empty.
   */
  country_mix?: CountryMixEntry[] | null;
  /**
   * Optional scenario-probability list. Null/undefined for pre-Part-4 reports.
   * Rendered as a dossier panel only when non-null and non-empty.
   */
  scenario_probabilities?: ScenarioEntry[] | null;
}

/**
 * Payload shape of a `reporter_token` SSE event emitted during the reporter
 * phase. Consumed by `useLiveSession` to accumulate `draftText`.
 */
export interface ReporterTokenEvent {
  chunk: string;
  token_index: number;
}

export interface UsageStats {
  requests: number;
  total_tokens: number;
  request_tokens: number;
  response_tokens: number;
}

export type SessionStatus = "running" | "complete" | "error" | "queued" | "paused";

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

// Partial mirrors of Python `MarketAccessFindings` / `AnalystFindings` — only
// the fields the dossier UI renders. `research_json` / `analyst_json` arrive
// as raw JSON strings on `SessionDetail`; consumers JSON.parse with try/catch.
export interface PayerCoverageEntry {
  payer: string;
  coverage_status: string;
  formulary_tier?: string;
}

export interface CompetitorEntry {
  name: string;
  share_or_notes: string;
}

export interface MarketAccessFindings {
  payer_coverage: PayerCoverageEntry[];
  [key: string]: unknown;
}

export interface AnalystFindings {
  competitive_landscape: CompetitorEntry[];
  [key: string]: unknown;
}

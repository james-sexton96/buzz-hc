/**
 * Unit tests for type helpers and pure utility functions.
 * These tests run entirely in Node.js without needing a browser or API.
 */

import type { MarketReport, WorkflowEvent, SessionStatus } from "../lib/types";

describe("WorkflowEvent type", () => {
  it("accepts valid event types", () => {
    const event: WorkflowEvent = {
      timestamp: "2024-01-01T00:00:00",
      event_type: "agent_start",
      source: "Researcher",
      message: "Starting research",
    };
    expect(event.event_type).toBe("agent_start");
    expect(event.details).toBeUndefined();
  });
});

describe("MarketReport type", () => {
  it("constructs a minimal valid report", () => {
    const report: MarketReport = {
      title: "GLP-1 Report",
      executive_summary: "Strong growth expected",
      sections: [{ heading: "Market Size", content: "## Details" }],
      sources: ["https://example.com"],
    };
    expect(report.title).toBe("GLP-1 Report");
    expect(report.sections).toHaveLength(1);
    expect(report.markdown_content).toBeUndefined();
  });
});

describe("SessionStatus values", () => {
  it("covers all expected statuses", () => {
    const statuses: SessionStatus[] = ["running", "complete", "error"];
    expect(statuses).toHaveLength(3);
  });
});

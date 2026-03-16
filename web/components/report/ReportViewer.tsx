"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { MarketReport } from "@/lib/types";
import { buttonVariants } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

interface ReportViewerProps {
  report: MarketReport;
  pdfUrl?: string;
}

function buildMarkdown(report: MarketReport): string {
  if (report.markdown_content) return report.markdown_content;
  const parts: string[] = [`# ${report.title}\n\n${report.executive_summary}`];
  for (const section of report.sections) {
    parts.push(`\n\n## ${section.heading}\n\n${section.content}`);
  }
  if (report.sources?.length) {
    parts.push("\n\n## Sources\n\n" + report.sources.map((s) => `- ${s}`).join("\n"));
  }
  return parts.join("");
}

export function ReportViewer({ report, pdfUrl }: ReportViewerProps) {
  const md = buildMarkdown(report);

  return (
    <div className="space-y-5">
      {/* Document header */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-3 flex-1">
          <h2 className="text-2xl font-semibold tracking-tight [font-family:var(--font-serif)]">{report.title}</h2>
          {report.executive_summary && (
            <div className="border-l-4 border-primary/40 pl-4">
              <p className="text-sm text-muted-foreground leading-relaxed">
                {report.executive_summary}
              </p>
            </div>
          )}
        </div>
        {pdfUrl && (
          <a
            href={pdfUrl}
            download
            className={cn(buttonVariants({ variant: "outline", size: "sm" }), "shrink-0 gap-1.5")}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-3.5 h-3.5">
              <path d="M8.75 2.75a.75.75 0 0 0-1.5 0v5.69L5.03 6.22a.75.75 0 0 0-1.06 1.06l3.5 3.5a.75.75 0 0 0 1.06 0l3.5-3.5a.75.75 0 0 0-1.06-1.06L8.75 8.44V2.75Z" />
              <path d="M3.5 9.75a.75.75 0 0 0-1.5 0v1.5A2.75 2.75 0 0 0 4.75 14h6.5A2.75 2.75 0 0 0 14 11.25v-1.5a.75.75 0 0 0-1.5 0v1.5c0 .69-.56 1.25-1.25 1.25h-6.5c-.69 0-1.25-.56-1.25-1.25v-1.5Z" />
            </svg>
            Download PDF
          </a>
        )}
      </div>

      <Separator />

      <div className="prose prose-sm dark:prose-invert max-w-none
        prose-headings:font-semibold prose-headings:tracking-tight
        prose-h1:[font-family:var(--font-serif)] prose-h2:[font-family:var(--font-serif)]
        prose-h1:text-xl prose-h2:text-lg prose-h2:text-indigo-900 prose-h2:border-b prose-h2:pb-1.5 prose-h2:border-border
        prose-a:text-primary prose-a:no-underline hover:prose-a:underline
        prose-table:text-sm prose-th:bg-muted prose-th:p-2 prose-td:p-2
        prose-code:text-xs prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
        prose-blockquote:border-l-primary prose-blockquote:text-muted-foreground">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
      </div>
    </div>
  );
}

"""PDF export: MarketReport → Markdown → styled HTML → PDF via weasyprint."""

import os
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# macOS: WeasyPrint's CFFI bindings look for GLib/Pango using Linux-style
# shared-library names (e.g. libgobject-2.0-0). On Apple Silicon / macOS the
# Homebrew dylibs use a different naming convention (.dylib suffix).  We
# pre-populate DYLD_LIBRARY_PATH so ctypes.CDLL / cffi can resolve them before
# WeasyPrint is imported.  This is a no-op on Linux / Windows.
# ---------------------------------------------------------------------------
if sys.platform == "darwin":
    _homebrew_lib = "/opt/homebrew/lib"
    _current = os.environ.get("DYLD_LIBRARY_PATH", "")
    if _homebrew_lib not in _current:
        os.environ["DYLD_LIBRARY_PATH"] = (
            f"{_homebrew_lib}:{_current}" if _current else _homebrew_lib
        )

import markdown as md_lib
from weasyprint import HTML

from app.schema import MarketReport

# ---------------------------------------------------------------------------
# Professional CSS for pharma reports (A4, branded header, page numbers)
# ---------------------------------------------------------------------------

REPORT_CSS = """
@page {
    size: A4;
    margin: 2cm 2.5cm 2.5cm 2.5cm;
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 9pt;
        color: #888;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    @top-right {
        content: "Buzz Healthcare Research";
        font-size: 8pt;
        color: #aaa;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
}

* {
    box-sizing: border-box;
}

body {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.65;
    color: #1a1a1a;
    margin: 0;
    padding: 0;
}

/* ── Header banner ── */
.report-header {
    background-color: #0d3b66;
    color: white;
    padding: 28px 32px 24px;
    margin: -2cm -2.5cm 28pt -2.5cm;
}

.report-header h1 {
    color: white;
    font-size: 20pt;
    font-weight: 700;
    margin: 0 0 6px 0;
    border: none;
    line-height: 1.25;
}

.report-header .meta {
    color: #adc8e6;
    font-size: 9pt;
    margin: 0;
}

/* ── Headings ── */
h1 {
    font-size: 18pt;
    color: #0d3b66;
    border-bottom: 2.5px solid #0d3b66;
    padding-bottom: 6px;
    margin-top: 28pt;
    margin-bottom: 10pt;
}

h2 {
    font-size: 14pt;
    color: #1a5276;
    border-bottom: 1px solid #d5e8f5;
    padding-bottom: 4px;
    margin-top: 22pt;
    margin-bottom: 8pt;
}

h3 {
    font-size: 11.5pt;
    color: #1f4e79;
    margin-top: 14pt;
    margin-bottom: 5pt;
}

/* ── Executive summary block ── */
.executive-summary {
    background-color: #eef4fb;
    border-left: 4px solid #1a5276;
    padding: 14px 18px;
    margin: 0 0 20pt 0;
    font-size: 10.5pt;
    page-break-inside: avoid;
}

.executive-summary p:first-child { margin-top: 0; }
.executive-summary p:last-child  { margin-bottom: 0; }

/* ── Body text ── */
p {
    margin: 0 0 8pt 0;
}

/* ── Tables ── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0 16pt 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}

thead th {
    background-color: #0d3b66;
    color: white;
    padding: 7px 11px;
    text-align: left;
    font-weight: 600;
}

tbody td {
    padding: 6px 11px;
    border-bottom: 1px solid #dde6f0;
    vertical-align: top;
}

tbody tr:nth-child(even) td {
    background-color: #f4f8fc;
}

/* ── Lists ── */
ul, ol {
    margin: 4pt 0 8pt 0;
    padding-left: 20pt;
}

li {
    margin-bottom: 3pt;
}

/* ── Code / pre ── */
code {
    background-color: #f0f4f8;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 9pt;
    font-family: 'Courier New', monospace;
}

pre {
    background-color: #f0f4f8;
    border: 1px solid #d0dcea;
    border-radius: 4px;
    padding: 10px 14px;
    font-size: 9pt;
    overflow-x: auto;
    page-break-inside: avoid;
}

/* ── Blockquote ── */
blockquote {
    border-left: 3px solid #1a5276;
    margin: 10pt 0;
    padding: 4px 14px;
    color: #444;
    font-style: italic;
}

/* ── Sources / links ── */
.sources-section {
    margin-top: 20pt;
    padding-top: 10pt;
    border-top: 1px solid #ccc;
}

a {
    color: #1a5276;
    text-decoration: none;
    word-break: break-all;
}

/* ── Page break helpers ── */
h1, h2 { page-break-after: avoid; }
table, figure { page-break-inside: avoid; }
"""


# ---------------------------------------------------------------------------
# Core conversion functions
# ---------------------------------------------------------------------------

def report_to_markdown(report: MarketReport) -> str:
    """Return the full Markdown string for a MarketReport.

    Uses ``markdown_content`` if populated; otherwise assembles it from the
    structured fields so the output is always usable.
    """
    if report.markdown_content:
        return report.markdown_content

    parts: list[str] = [f"# {report.title}\n"]
    parts.append(f"\n{report.executive_summary}\n")

    for section in report.sections:
        parts.append(f"\n## {section.heading}\n")
        parts.append(f"\n{section.content}\n")

    if report.sources:
        parts.append("\n## Sources\n")
        for s in report.sources:
            parts.append(f"- {s}\n")

    return "\n".join(parts)


def markdown_to_html(md_text: str, report: MarketReport) -> str:
    """Convert a Markdown string to a complete, styled HTML document."""
    generated_date = datetime.now().strftime("%B %d, %Y")

    body_html = md_lib.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "extra"],
    )

    # Wrap executive summary in a styled div if the text contains it
    # (only applied when building from raw markdown_content)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>{REPORT_CSS}</style>
</head>
<body>
  <div class="report-header">
    <h1>{report.title}</h1>
    <p class="meta">Buzz Healthcare Research Report &nbsp;|&nbsp; Generated {generated_date}</p>
  </div>
  {body_html}
</body>
</html>"""


def export_pdf(report: MarketReport) -> bytes:
    """Convert a :class:`MarketReport` to PDF bytes.

    Returns raw PDF bytes suitable for ``st.download_button`` or writing to
    a file.
    """
    md_text = report_to_markdown(report)
    html_str = markdown_to_html(md_text, report)
    return HTML(string=html_str).write_pdf()


def save_pdf(report: MarketReport, filepath: Path) -> Path:
    """Export a :class:`MarketReport` to a PDF file.

    Creates parent directories as needed and returns the resolved filepath.
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_bytes(export_pdf(report))
    return filepath

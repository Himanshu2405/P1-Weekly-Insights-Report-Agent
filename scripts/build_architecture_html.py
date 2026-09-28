"""Regenerate docs/architecture.html from docs/architecture.mmd (the single source of the diagram).

Usage: python scripts/build_architecture_html.py
"""

from html import escape
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report Pipeline Flow</title>
<style>
  :root {{ --page: #f9f9f7; --ink: #0b0b0b; --ink-2: #52514e; --border: rgba(11,11,11,0.10); }}
  body {{ margin: 0; background: var(--page); color: var(--ink);
         font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  header {{ padding: 20px 24px 8px; }}
  h1 {{ margin: 0 0 4px; font-size: 22px; }}
  .sub {{ color: var(--ink-2); }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 8px; padding: 8px 24px 12px; }}
  .chip {{ border: 1px solid var(--border); border-radius: 999px; padding: 3px 10px; font-size: 13px; }}
  .wrap {{ overflow: auto; padding: 0 24px 32px; }}
  .mermaid {{ min-width: 900px; }}
</style>
</head>
<body>
<header>
  <h1>How the weekly report is built</h1>
  <div class="sub">Runs itself every Monday via GitHub Actions, or by hand: <code>python scripts/build_report.py --week 2026-08-03</code>.
  Step details: see <a href="https://github.com/Himanshu2405/P1-Weekly-Insights-Report-Agent/blob/main/docs/ARCHITECTURE.md">ARCHITECTURE.md</a>. Live report: <a href="https://himanshu2405.github.io/P1-Weekly-Insights-Report-Agent/">himanshu2405.github.io/P1-Weekly-Insights-Report-Agent</a>.</div>
</header>
<div class="legend">
  <span class="chip" style="background:#eef4fc">Inputs</span>
  <span class="chip" style="background:#e7f5ea">Built and shipped</span>
  <span class="chip" style="background:#f3ecfb">Automation (Phase 5)</span>
</div>
<div class="wrap"><pre class="mermaid">
{diagram}
</pre></div>
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  mermaid.initialize({{ startOnLoad: true, theme: "base", flowchart: {{ useMaxWidth: false, htmlLabels: true }} }});
</script>
</body>
</html>
"""


def main() -> None:
    diagram = (DOCS / "architecture.mmd").read_text()
    # escape for HTML, but keep the <br/> line breaks used inside node labels
    body = escape(diagram, quote=False).replace("&lt;br/&gt;", "<br/>")
    (DOCS / "architecture.html").write_text(PAGE.format(diagram=body))
    print(f"Wrote {DOCS / 'architecture.html'}")


if __name__ == "__main__":
    main()

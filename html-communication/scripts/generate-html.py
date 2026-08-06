#!/usr/bin/env python3
"""
generate-html.py — Generate self-contained HTML findings report.

Reads JSON from stdin or --data file, writes findings-<timestamp>.html.
Black background, white text, CSS Grid columns, styled tables.
Optional Chart.js (CDN) only when section has chart: true.
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from html import escape


def load_data(args):
    if args.data:
        with open(args.data) as f:
            return json.load(f)
    return json.load(sys.stdin)


def render_table(table):
    headers = table.get("headers", [])
    rows = table.get("rows", [])
    if not headers:
        return ""

    thead = "<thead><tr>" + "".join(f"<th>{escape(str(h))}</th>" for h in headers) + "</tr></thead>"
    tbody_rows = []
    for row in rows:
        cells = "".join(f"<td>{escape(str(c))}</td>" for c in row)
        tbody_rows.append(f"<tr>{cells}</tr>")
    tbody = "<tbody>" + "".join(tbody_rows) + "</tbody>"
    return f"<table>{thead}{tbody}</table>"


def render_chart(chart_data, chart_id):
    if not chart_data:
        return ""
    chart_json = json.dumps(chart_data)
    return f"""
<div class="chart-container"><canvas id="chart-{chart_id}"></canvas></div>
<script>
(function() {{
  const ctx = document.getElementById('chart-{chart_id}').getContext('2d');
  const config = {chart_json};
  new Chart(ctx, config);
}})();
</script>
"""


def render_section(section, idx):
    parts = []
    heading = section.get("heading", "")
    if heading:
        parts.append(f"<h2>{escape(heading)}</h2>")

    if "table" in section:
        parts.append(render_table(section["table"]))

    if section.get("chart") and "chartData" in section:
        parts.append(render_chart(section["chartData"], idx))

    if "text" in section:
        parts.append(f"<pre>{escape(section['text'])}</pre>")

    return "<section>" + "".join(parts) + "</section>"


def generate_html(data):
    title = data.get("title", "Findings Report")
    sections = data.get("sections", [])

    has_chart = any(s.get("chart") for s in sections)

    chart_script = ""
    if has_chart:
        chart_script = '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'

    rendered_sections = "".join(render_section(s, i) for i, s in enumerate(sections))

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{escape(title)} - Findings</title>
  <style>
    :root {{
      --bg: #0a0a0a;
      --fg: #e8e8e8;
      --border: #333;
      --row: #141414;
      --accent: #4da6ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      background: var(--bg);
      color: var(--fg);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      padding: 2rem;
      max-width: 1400px;
      margin: 0 auto;
      line-height: 1.6;
    }}
    h1 {{
      border-bottom: 1px solid var(--border);
      padding-bottom: 0.5rem;
      margin-bottom: 1.5rem;
      font-weight: 600;
    }}
    h2 {{
      margin-top: 0;
      margin-bottom: 0.75rem;
      color: var(--accent);
      font-weight: 500;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1.5rem;
    }}
    section {{ background: #111; border: 1px solid var(--border); border-radius: 4px; padding: 1rem; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
    }}
    th, td {{
      border: 1px solid var(--border);
      padding: 0.5rem 0.75rem;
      text-align: left;
    }}
    th {{
      background: #1a1a1a;
      font-weight: 600;
      color: var(--accent);
    }}
    tr:nth-child(even) {{ background: var(--row); }}
    tr:hover {{ background: #1c1c1c; }}
    pre {{
      background: #0d0d0d;
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 1rem;
      overflow-x: auto;
      white-space: pre-wrap;
      word-wrap: break-word;
    }}
    .chart-container {{
      height: 300px;
      width: 100%;
    }}
    @media (max-width: 600px) {{
      body {{ padding: 1rem; }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
  {chart_script}
</head>
<body>
  <h1>{escape(title)}</h1>
  <div class="grid">
    {rendered_sections}
  </div>
</body>
</html>
"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate findings HTML report")
    parser.add_argument("--data", help="Path to JSON data file (default: stdin)")
    parser.add_argument("--output", help="Output HTML file (default: findings-<timestamp>.html)")
    args = parser.parse_args()

    try:
        data = load_data(args)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    html = generate_html(data)

    if args.output:
        out_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_path = Path.cwd() / f"findings-{timestamp}.html"

    out_path.write_text(html)
    print(str(out_path))


if __name__ == "__main__":
    main()
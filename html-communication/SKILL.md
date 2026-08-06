---
name: html-communication
description: Use when completing research, analysis, or planning tasks and you want to present findings as a clean HTML page served locally with a clickable URL
---

# html-communication

## Overview

Generate a self-contained HTML file from agent findings (research, analysis, plans) and serve it locally via Python's stdlib HTTP server. Prints a clickable `http://127.0.0.1:<port>/findings-<timestamp>.html` URL. Black background, white text, tables/columns for structure. Optional Chart.js graphs only when data includes `chart: true`.

## When to Use

- Agent finishes research/analysis/planning task and you want a readable HTML artifact
- User explicitly asks "write findings to HTML" or "generate report"
- Auto-mode enabled (`HTML_COMMUNICATION_AUTO=1`) — triggers on task completion hooks

**When NOT to use:**
- Quick conversational replies
- Code-only outputs
- Content that's genuinely just a few sentences

## Core Pattern

### Explicit Invocation (Default)
```
User: "write findings to HTML" / "generate report"
Agent: Runs html-communication skill → writes findings.html → starts server → prints URL
```

### Auto-Mode (Opt-in)
```
export HTML_COMMUNICATION_AUTO=1
# Agent completes task → hook fires → skill runs automatically
```

## Quick Reference

| Action | Command/Trigger |
|--------|-----------------|
| Explicit generate | "write findings to HTML" |
| Auto-mode enable | `export HTML_COMMUNICATION_AUTO=1` |
| Server URL format | `http://127.0.0.1:<random-port>/findings-<timestamp>.html` |
| HTML theme | Black bg (`#0a0a0a`), white text (`#e8e8e8`), tables with `#333` borders |
| Graphs | Only if input data has `chart: true` (loads Chart.js from CDN) |

## Implementation

### Files
```
html-communication/
├── SKILL.md
├── scripts/
│   ├── generate-html.py      # Generates findings HTML from stdin/args
│   └── serve.py              # Starts python http.server, prints URL
```

### generate-html.py
Reads JSON from stdin (or `--data` file), writes self-contained HTML:
- Single file, inline CSS/JS
- Black/white theme, CSS Grid columns, styled tables
- Optional Chart.js (CDN) only when `chart: true` in data
- Outputs to `findings-<timestamp>.html` in CWD

### serve.py
```python
# Starts python3 -m http.server 0 --bind 127.0.0.1
# Captures random port from stdout
# Prints: "📄 Findings: http://127.0.0.1:<port>/findings-<timestamp>.html"
# Keeps server running until Ctrl+C
```

### Usage in Agent Flow
```bash
# Explicit
echo '{"title":"Research Results","sections":[...]}' | python3 ~/.agents/skills/html-communication/scripts/generate-html.py
python3 ~/.agents/skills/html-communication/scripts/serve.py findings-*.html

# Auto-mode (hook)
# Claude Code: Stop hook runs the above
# Codex: onCompletion in AGENTS.md
# Antigravity: equivalent hook
```

## Hook Configuration

### Claude Code (opencode)
Add to `~/.config/opencode/opencode.json` or project `.opencode.json`:
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": ".*",
        "command": "bash -c 'if [ -n \"$HTML_COMMUNICATION_AUTO\" ]; then python3 ~/.agents/skills/html-communication/scripts/generate-html.py <<< \"$FINDINGS_JSON\" && python3 ~/.agents/skills/html-communication/scripts/serve.py findings-*.html; fi'",
        "timeout": 30
      }
    ]
  }
}
```

### Codex
Add to `AGENTS.md`:
```markdown
onCompletion:
  - if [ -n "$HTML_COMMUNICATION_AUTO" ]; then python3 ~/.agents/skills/html-communication/scripts/generate-html.py <<< "$FINDINGS_JSON" && python3 ~/.agents/skills/html-communication/scripts/serve.py findings-*.html; fi
```

### Antigravity
Add to antigravity config (adapt to its hook system):
```yaml
hooks:
  on_task_complete:
    - command: |
        if [ -n "$HTML_COMMUNICATION_AUTO" ]; then
          python3 ~/.agents/skills/html-communication/scripts/generate-html.py <<< "$FINDINGS_JSON"
          python3 ~/.agents/skills/html-communication/scripts/serve.py findings-*.html
        fi
```

## HTML Output Structure

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{{title}} - Findings</title>
  <style>
    /* Black theme, CSS Grid columns, styled tables */
    :root { --bg:#0a0a0a; --fg:#e8e8e8; --border:#333; --row:#141414; }
    body { background:var(--bg); color:var(--fg); font-family:system-ui; padding:2rem; max-width:1400px; margin:0 auto; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:1.5rem; }
    table { width:100%; border-collapse:collapse; }
    th,td { border:1px solid var(--border); padding:0.5rem 0.75rem; text-align:left; }
    tr:nth-child(even) { background:var(--row); }
    h1 { border-bottom:1px solid var(--border); padding-bottom:0.5rem; }
    .chart-container { height:300px; }
  </style>
  {{#if hasChart}}<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>{{/if}}
</head>
<body>
  <h1>{{title}}</h1>
  <div class="grid">
    {{#each sections}}
    <section>
      <h2>{{this.heading}}</h2>
      {{#if this.table}}
      <table>
        <thead><tr>{{#each this.table.headers}}<th>{{this}}</th>{{/each}}</tr></thead>
        <tbody>{{#each this.table.rows}}<tr>{{#each this}}<td>{{this}}</td>{{/each}}</tr>{{/each}}</tbody>
      </table>
      {{/if}}
      {{#if this.chart}}
      <div class="chart-container"><canvas id="chart-{{@index}}"></canvas></div>
      <script>
        // Chart.js init for this.chart.data
      </script>
      {{/if}}
      {{#if this.text}}
      <pre>{{this.text}}</pre>
      {{/if}}
    </section>
    {{/each}}
  </div>
</body>
</html>
```

## Input Data Format (JSON)

```json
{
  "title": "Research: Rust vs Go for CLI Tools",
  "sections": [
    {
      "heading": "Performance Comparison",
      "table": {
        "headers": ["Metric", "Rust", "Go", "Winner"],
        "rows": [
          ["Startup (ms)", "2", "15", "Rust"],
          ["Memory (MB)", "8", "22", "Rust"],
          ["Binary Size", "1.2MB", "8.5MB", "Rust"]
        ]
      }
    },
    {
      "heading": "Compile Time",
      "chart": true,
      "chartData": {
        "type": "bar",
        "data": {
          "labels": ["Clean", "Incremental"],
          "datasets": [
            {"label": "Rust (s)", "data": [45, 3]},
            {"label": "Go (s)", "data": [8, 1]}
          ]
        }
      }
    },
    {
      "heading": "Recommendation",
      "text": "Use Rust for performance-critical CLIs. Go for fast iteration."
    }
  ]
}
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Forgetting `HTML_COMMUNICATION_AUTO=1` for auto-mode | Export in shell profile or per-session |
| Server not accessible | Ensure `--bind 127.0.0.1` (not 0.0.0.0) for local-only |
| Chart.js not loading | Check internet/CDN access; fallback to inline SVG if needed |
| HTML file not found by server | Run serve.py from same directory as generate-html.py output |

## Real-World Impact

- Research tasks: Findings readable in browser, shareable via URL
- Plan reviews: Clean HTML plans instead of markdown walls
- Cross-agent handoff: URL pasted to next agent as context
- Zero-dep local serving: Works on any machine with Python 3
---
name: html-preview
description: Use whenever the user wants to see, preview, or quickly view a findings/analysis report, mockup, or summary in a browser. Triggers on "show me", "preview this", "let me see it", "make a report/artifact/demo of X".
---

# HTML Preview

When the user wants to see a quick report/prototype, generate ONE self-contained
HTML file and open it — never just paste code blocks in chat.

## Required visual style (always apply, no exceptions)

- **Background**: pure black (`#000` or `#0a0a0a`), **text**: white (`#fff` / `#f0f0f0` for secondary text). No light backgrounds anywhere.
- **No code blocks / no monospace dumps.** Content is always presented as prose points, headers, and tables — never `<pre>`/`<code>` for output content.
- **Structure every section as: Title (h2/h3) → short text/points underneath.** Prefer bulleted or numbered points over paragraphs where possible.
- **Top of the page: always a responsive row of "Top Findings" cards.** Use CSS Grid Auto-Fit, such as `grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))`, so 3–15+ findings reflow cleanly across desktop, laptop, and mobile. Each card has:
  - Title (finding name, short)
  - Summary (1–2 lines)
  - Severity badge (High / Medium / Low — color-coded: red / amber / green, but background stays black — use colored text or a colored left-border accent, not colored fill blocks)
  - Any other relevant metric (e.g. confidence, count, affected area)
- **Below the top row**: supporting detail, grouped by heading, in bullet points.
- **Use `<table>` for anything tabular or comparative** (metrics across runs, before/after, per-script/per-document breakdowns, etc.) — styled with a subtle border (`#333`), not gridlines everywhere. No plain unstyled default tables.
- Typography: system sans-serif stack, generous line-height, comfortable padding (min 24px around content, 32–48px page margins on desktop).
- Accent color for links/highlights: a single muted accent (e.g. `#4da6ff` or `#7dd3fc`) — used sparingly, not decoratively.

## Open locally with zero background overhead

1. Write the file to `./.preview/<slug>.html`.
2. Prefer opening it directly with the system browser: `open file://$(pwd)/.preview/<slug>.html` on macOS, `xdg-open` on Linux, or `explorer.exe` on WSL.
3. Use direct `file://` opening for self-contained HTML because it creates no persistent process, consumes no server memory, and opens no port.
4. For follow-up edits, overwrite the same file and reopen it; do not spawn another server.

## Optional HTTP serving

Use HTTP only when the preview needs browser-origin behavior that `file://` does not provide, such as module loading, fetch requests, or live reload:

1. `python3 -m http.server 8787 --directory ./.preview &` (or `npx live-server ./.preview --port=8787` for auto-reload).
2. Open `http://localhost:8787/<slug>.html` with the system browser.
3. Reuse an existing preview server when possible; do not spawn repeated background servers.

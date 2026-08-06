#!/usr/bin/env python3
"""
serve.py — Start Python HTTP server for findings HTML, print clickable URL.

Usage: python3 serve.py findings-*.html
       python3 serve.py --port 0 --bind 127.0.0.1 findings-20250115-143022.html
"""

import argparse
import subprocess
import sys
import socket
import signal
import atexit
from pathlib import Path


def find_html_file(pattern):
    """Find the most recent HTML file matching pattern."""
    files = list(Path.cwd().glob(pattern))
    if not files:
        return None
    return max(files, key=lambda f: f.stat().st_mtime)


def get_free_port(bind_addr="127.0.0.1"):
    """Get a free port by binding to port 0."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((bind_addr, 0))
        return s.getsockname()[1]


def main():
    parser = argparse.ArgumentParser(description="Serve findings HTML with Python HTTP server")
    parser.add_argument("file", nargs="?", help="HTML file to serve (default: latest findings-*.html)")
    parser.add_argument("--port", type=int, default=0, help="Port (0 = random)")
    parser.add_argument("--bind", default="127.0.0.1", help="Bind address")
    args = parser.parse_args()

    # Find HTML file
    if args.file:
        html_file = Path(args.file)
        if not html_file.exists():
            html_file = find_html_file(args.file)
    else:
        html_file = find_html_file("findings-*.html")

    if not html_file or not html_file.exists():
        print("Error: No findings HTML file found. Run generate-html.py first.", file=sys.stderr)
        sys.exit(1)

    serve_dir = html_file.parent
    html_name = html_file.name

    print(f"📁 Serving from: {serve_dir}")
    print(f"📄 File: {html_name}")

    # Determine port
    if args.port == 0:
        port = get_free_port(args.bind)
        print(f"🔌 Auto-selected port: {port}")
    else:
        port = args.port

    url = f"http://{args.bind}:{port}/{html_name}"
    print(f"\n📄 Findings: {url}")
    print("   (Click or copy to open in browser)")
    print("   Press Ctrl+C to stop server\n")

    # Start server with known port
    cmd = [
        sys.executable, "-m", "http.server",
        str(port),
        "--bind", args.bind
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=serve_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    def cleanup():
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    # Forward server logs
    for line in proc.stdout:
        line = line.strip()
        if line:
            print(f"  {line}")

    proc.wait()


if __name__ == "__main__":
    main()
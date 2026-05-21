"""Tiny static dev server for the Food Map project.

Serves the current directory over HTTP with caching disabled so file edits show
up on a normal reload without a hard-refresh. Equivalent to
`python -m http.server <port>` plus no-cache headers and a friendlier startup
message.

By default opens the project in your browser. Pass --no-browser to skip.

Usage:
    python dev_server.py                # http://localhost:8000, opens browser
    python dev_server.py --port 8080
    python dev_server.py --no-browser
    python dev_server.py --host 0.0.0.0 --port 8000   # LAN access from phone
    python dev_server.py --open test-data.html        # open a specific path
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler


class NoCacheHandler(SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler that adds no-cache headers to every response.

    Without this, the browser will happily cache ES module files and you'll
    spend ten minutes wondering why your last edit "didn't apply."
    """

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    # Quieter logs — one line per request, drop the timestamp noise.
    def log_message(self, format: str, *args) -> None:  # type: ignore[override]
        sys.stderr.write(f"  {self.address_string()}  {format % args}\n")


def _lan_ip() -> str | None:
    """Best-effort guess of this host's LAN IP (for phone testing)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def _open_browser(url: str, delay: float = 0.4) -> None:
    """Open url in a new browser tab shortly after the server starts."""
    threading.Timer(delay, lambda: webbrowser.open_new_tab(url)).start()


def main() -> int:
    parser = argparse.ArgumentParser(description="Food Map dev server")
    parser.add_argument("--host", default="127.0.0.1", help="bind host (default 127.0.0.1; use 0.0.0.0 for LAN)")
    parser.add_argument("--port", type=int, default=8000, help="bind port (default 8000)")
    parser.add_argument("--no-browser", action="store_true", help="don't open a browser tab on start")
    parser.add_argument("--open", default="index.html", help="path to open in the browser (default index.html)")
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)

    try:
        httpd = HTTPServer((args.host, args.port), NoCacheHandler)
    except OSError as e:
        print(f"Could not bind {args.host}:{args.port} — {e}", file=sys.stderr)
        return 1

    local_url = f"http://localhost:{args.port}/{args.open.lstrip('/')}"

    print(f"Food Map dev server")
    print(f"  serving:  {here}")
    print(f"  local:    {local_url}")
    if args.host == "0.0.0.0":
        ip = _lan_ip()
        if ip:
            print(f"  LAN:      http://{ip}:{args.port}/{args.open.lstrip('/')}")
    print(f"  Ctrl+C to stop\n")

    if not args.no_browser:
        _open_browser(local_url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

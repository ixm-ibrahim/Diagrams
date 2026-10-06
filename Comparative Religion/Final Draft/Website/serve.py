#!/usr/bin/env python3
"""Serve this website locally and open it in the browser.

Usage:
    python serve.py            # serves on port 8000
    python serve.py 9000       # serves on a custom port
"""
import http.server
import socketserver
import webbrowser
import sys
import os
import threading

# Serve from the folder this script lives in, regardless of where it's run from.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
url = f"http://localhost:{port}"

Handler = http.server.SimpleHTTPRequestHandler
# Allow the port to be reused immediately after the server stops.
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer(("", port), Handler) as httpd:
    print(f"Serving website at {url}")
    print("Press Ctrl+C to stop.")
    # Open the browser shortly after the server starts listening.
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")

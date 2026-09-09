#!/usr/bin/env python3
"""
PROJECT JANUS MINI (16-TILE): LOCAL DASHBOARD SERVER LAUNCHER
=============================================================
Lightweight zero-dependency HTTP server hosting the Janus Web Dashboard
and co-simulation REST API dispatcher on http://127.0.0.1:8080.

Serves:
  - Static assets (logo, favicon, video, PDFs, images) from root/ and public/
  - Dynamic API endpoints via api/index.py WSGI app
"""

import sys
import os
import mimetypes
import argparse
import webbrowser
from wsgiref.simple_server import make_server, WSGIRequestHandler

# Ensure root and simulation directories are in sys.path early
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
SIM_DIR = os.path.join(ROOT_DIR, "janus_mini16_sim")
for _p in [ROOT_DIR, SIM_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# MIME type additions not always present on Windows
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("image/x-icon", ".ico")
mimetypes.add_type("image/jpeg", ".jpg")
mimetypes.add_type("image/jpeg", ".jpeg")
mimetypes.add_type("video/mp4", ".mp4")
mimetypes.add_type("application/pdf", ".pdf")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")


# Directories to search for static assets (in priority order)
STATIC_ROOTS = [
    os.path.join(ROOT_DIR, "public"),  # Vercel public dir first
    ROOT_DIR,                           # Project root
]


def serve_static(path, start_response):
    """Attempt to serve a file from STATIC_ROOTS. Returns None if not found."""
    # Strip leading slash and prevent directory traversal
    rel = path.lstrip("/")
    if not rel or ".." in rel:
        return None

    for static_root in STATIC_ROOTS:
        full = os.path.abspath(os.path.join(static_root, rel))
        # Security: must stay within the static root
        if not full.startswith(static_root):
            continue
        if os.path.isfile(full):
            mime, _ = mimetypes.guess_type(full)
            mime = mime or "application/octet-stream"
            try:
                with open(full, "rb") as f:
                    data = f.read()
                start_response("200 OK", [
                    ("Content-Type", mime),
                    ("Content-Length", str(len(data))),
                    ("Access-Control-Allow-Origin", "*"),
                    ("Cache-Control", "public, max-age=3600"),
                ])
                return [data]
            except Exception:
                pass
    return None


def janus_app(environ, start_response):
    """
    Combined WSGI app:
      1. API routes (/api/*, /) → forwarded to api/index.py app
      2. Everything else       → served as static files from public/ or root
    """
    from api.index import app as api_app

    path = environ.get("PATH_INFO", "/")

    # API and homepage handled by the API module
    if path == "/" or path.startswith("/api/"):
        return api_app(environ, start_response)

    # Try static file serving first
    static_result = serve_static(path, start_response)
    if static_result is not None:
        return static_result

    # Known HTML aliases served by the API app
    if path in ["/index.html", "/index"]:
        return api_app(environ, start_response)

    # PDF shortcut paths also handled by API app
    if path in ["/paper.pdf", "/main.pdf", "/JANUS_IEEE_Manuscript.pdf",
                "/simulation_report.pdf", "/JANUS_Mini16_Simulation_Report.pdf",
                "/cmos_paper.pdf", "/JANUS_Mini16_CMOS_Architecture.pdf"]:
        return api_app(environ, start_response)

    # 404
    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"404 - Not Found"]


class QuietWSGIRequestHandler(WSGIRequestHandler):
    """Suppress noisy heartbeat polling from log output."""
    def log_message(self, format, *args):
        if args and "/api/heartbeat" in str(args[0]):
            return
        super().log_message(format, *args)


def main():
    parser = argparse.ArgumentParser(description="Run Project JANUS Local Web Dashboard")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="Skip auto-opening browser")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    print("\n" + "=" * 80)
    print("  PROJECT JANUS: SPATIAL RESIDUE OPTICAL AI COMPUTING DASHBOARD")
    print("=" * 80)
    print(f"  Local Server  : {url}")
    print(f"  Project Root  : {ROOT_DIR}")
    print(f"  Static Assets : {os.path.join(ROOT_DIR, 'public')} → {ROOT_DIR}")
    print(f"  Sim Engine    : {SIM_DIR}")
    print("  Press Ctrl+C to stop.")
    print("=" * 80 + "\n")

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    server = make_server(args.host, args.port, janus_app, handler_class=QuietWSGIRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down JANUS Dashboard server.")
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Local Web Presentation Manager
Zero-dependency Python script to serve and manage local HTML presentation decks.
"""

import os
import sys
import argparse
import http.server
import socketserver
import webbrowser
from pathlib import Path

DEFAULT_PRESENTATION_DIR = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "presentation"

def serve_presentation(directory: Path, port: int = 8000, open_browser: bool = True):
    """Serve the local web presentation directory over HTTP."""
    if not directory.exists():
        print(f"Error: Presentation directory '{directory}' does not exist.", file=sys.stderr)
        sys.exit(1)

    os.chdir(directory)

    Handler = http.server.SimpleHTTPRequestHandler
    
    # Enable address reuse
    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            url = f"http://localhost:{port}"
            print(f"\n==================================================")
            print(f" 🚀 Local Web Presentation Server Running!")
            print(f" 📍 URL: {url}")
            print(f" 📂 Directory: {directory}")
            print(f" Press Ctrl+C to stop the server.")
            print(f"==================================================\n")

            if open_browser:
                try:
                    webbrowser.open(url)
                except Exception as e:
                    print(f"Could not auto-open browser: {e}")

            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping presentation server. Goodbye!")
        sys.exit(0)
    except Exception as err:
        print(f"Failed to start server on port {port}: {err}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Local Web Presentation CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start local web server for presentation")
    serve_parser.add_argument("--dir", type=Path, default=DEFAULT_PRESENTATION_DIR, help="Path to presentation directory (default: docs/presentation)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to serve on (default: 8000)")
    serve_parser.add_argument("--no-open", action="store_true", help="Do not auto-open browser")

    args = parser.parse_args()

    if args.command == "serve" or args.command is None:
        target_dir = getattr(args, "dir", DEFAULT_PRESENTATION_DIR)
        port = getattr(args, "port", 8000)
        no_open = getattr(args, "no-open", False)
        serve_presentation(directory=target_dir, port=port, open_browser=not no_open)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

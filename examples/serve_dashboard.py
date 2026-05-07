from __future__ import annotations

import argparse
import http.server
import socketserver
import webbrowser
from pathlib import Path


class LocalTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the RAGScaleGuard dashboard locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8787, type=int)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    dashboard_dir = Path(__file__).resolve().parent / "dashboard"
    handler = lambda *handler_args: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        *handler_args,
        directory=str(dashboard_dir),
    )
    with LocalTCPServer((args.host, args.port), handler) as server:
        url = f"http://{args.host}:{args.port}/"
        print(f"Serving RAGScaleGuard dashboard at {url}")
        if not args.no_open:
            webbrowser.open(url)
        server.serve_forever()


if __name__ == "__main__":
    main()

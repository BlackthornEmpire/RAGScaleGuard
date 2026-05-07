from __future__ import annotations

import argparse
import http.server
import json
import socketserver
import webbrowser
from pathlib import Path
from typing import Any


class LocalTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, directory: str, log_path: Path, **kwargs: Any) -> None:
        self.log_path = log_path
        super().__init__(*args, directory=directory, **kwargs)

    def do_POST(self) -> None:
        if self.path != "/events":
            self.send_error(404)
            return
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0 or content_length > 65_536:
            self.send_error(400)
            return
        raw_body = self.rfile.read(content_length)
        try:
            event = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(400)
            return
        if not isinstance(event, dict):
            self.send_error(400)
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event, sort_keys=True) + "\n")
        self.send_response(204)
        self.end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the RAGScaleGuard dashboard locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8787, type=int)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    dashboard_dir = Path(__file__).resolve().parent / "dashboard"
    log_path = Path(__file__).resolve().parents[1] / "reports" / "dashboard-events.jsonl"

    def handler(*handler_args: Any) -> DashboardHandler:
        return DashboardHandler(
            *handler_args,
            directory=str(dashboard_dir),
            log_path=log_path,
        )

    with LocalTCPServer((args.host, args.port), handler) as server:
        url = f"http://{args.host}:{args.port}/"
        print(f"Serving RAGScaleGuard dashboard at {url}")
        print(f"Writing dashboard events to {log_path}")
        if not args.no_open:
            webbrowser.open(url)
        server.serve_forever()


if __name__ == "__main__":
    main()

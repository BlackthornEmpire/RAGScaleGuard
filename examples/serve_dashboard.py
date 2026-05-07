from __future__ import annotations

import argparse
import http.server
import json
import re
import socketserver
import webbrowser
from pathlib import Path
from typing import Any

MAX_EVENT_BYTES = 16_384
MAX_LOG_BYTES = 1_000_000
SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?([^'\"\s,}]+)"
)
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


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
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400)
            return
        if content_length <= 0 or content_length > MAX_EVENT_BYTES:
            self.send_error(413)
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
        event = _normalise_event(event)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        _rotate_log_if_needed(self.log_path)
        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event, sort_keys=True) + "\n")
        self.send_response(204)
        self.end_headers()


def _normalise_event(event: dict[str, Any]) -> dict[str, Any]:
    level = event.get("level")
    if level not in {"info", "warn", "error"}:
        level = "info"
    return {
        "level": level,
        "message": _clean_text(event.get("message", ""), max_length=360),
        "timestamp": _clean_text(event.get("timestamp", ""), max_length=64),
        "details": _normalise_details(event.get("details", {})),
    }


def _normalise_details(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    details: dict[str, str] = {}
    for key, item in list(value.items())[:12]:
        details[_clean_text(key, max_length=64)] = _clean_text(item, max_length=360)
    return details


def _clean_text(value: object, max_length: int) -> str:
    text = CONTROL_CHARS_RE.sub("", str(value)).strip()
    text = SECRET_RE.sub(r"\1=[REDACTED]", text)
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3]}..."


def _rotate_log_if_needed(path: Path) -> None:
    if path.exists() and path.stat().st_size >= MAX_LOG_BYTES:
        backup = path.with_suffix(path.suffix + ".1")
        backup.unlink(missing_ok=True)
        path.replace(backup)


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

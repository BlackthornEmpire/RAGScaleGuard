from __future__ import annotations

import argparse
import http.server
import json
import os
import re
import socketserver
import sys
import webbrowser
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragscaleguard.adviser import AdviserRequest, LocalOpenAIAdviser, validate_adviser_response
from ragscaleguard.adviser.policy import sanitise_adviser_input, validate_adviser_mode

MAX_EVENT_BYTES = 16_384
MAX_ADVISER_BYTES = 24_000
MAX_LOG_BYTES = 1_000_000
SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?([^'\"\s,}]+)"
)
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
CSP_POLICY = (
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)


class LocalTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, directory: str, log_path: Path, **kwargs: Any) -> None:
        self.log_path = log_path
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self) -> None:
        self.send_header("Content-Security-Policy", CSP_POLICY)
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_POST(self) -> None:
        if self.path == "/events":
            self._handle_event()
            return
        if self.path == "/adviser":
            self._handle_adviser()
            return
        self.send_error(404)

    def _handle_event(self) -> None:
        body = self._read_json_body(MAX_EVENT_BYTES)
        if body is None:
            return
        event = _normalise_event(body)
        _write_event(self.log_path, event)
        self.send_response(204)
        self.end_headers()

    def _handle_adviser(self) -> None:
        body = self._read_json_body(MAX_ADVISER_BYTES)
        if body is None:
            return
        mode = validate_adviser_mode(body.get("mode"))
        if mode == "off":
            response = validate_adviser_response(
                {
                    "problem": "Adviser is off.",
                    "why_it_matters": "No local model call was made.",
                    "fix": "Turn on explain mode to request diagnostic advice.",
                    "risk": "No external adviser call.",
                },
                mode,
            )
        elif os.environ.get("RAGSCALEGUARD_ADVISER_ENABLED", "false").lower() != "true":
            response = validate_adviser_response(
                {
                    "problem": "Adviser server is disabled.",
                    "why_it_matters": "The dashboard will not call a local model until the server opt-in is set.",
                    "fix": "Restart with RAGSCALEGUARD_ADVISER_ENABLED=true and a local OpenAI-compatible endpoint.",
                    "risk": "No model call was made.",
                },
                mode,
            )
        else:
            adviser = LocalOpenAIAdviser(
                base_url=os.environ.get("RAGSCALEGUARD_ADVISER_BASE_URL", "http://127.0.0.1:11434/v1"),
                model=os.environ.get("RAGSCALEGUARD_ADVISER_MODEL", "llama3.1"),
            )
            try:
                response = adviser.advise(
                    AdviserRequest(mode=mode, diagnostics=dict(sanitise_adviser_input(body.get("diagnostics", {}))))
                )
            except RuntimeError as exc:
                response = validate_adviser_response(
                    {
                        "problem": "Adviser request failed.",
                        "why_it_matters": "The retrieval guard still works, but model-generated advice is unavailable.",
                        "fix": str(exc),
                        "risk": "Check the local model endpoint before relying on adviser output.",
                    },
                    mode,
                )
        _write_event(
            self.log_path,
            _normalise_event(
                {
                    "level": "info",
                    "message": f"Adviser {mode} request handled.",
                    "details": {"applied": response.applied, "risk": response.risk},
                }
            ),
        )
        self._send_json(
            {
                "problem": response.problem,
                "why_it_matters": response.why_it_matters,
                "fix": response.fix,
                "risk": response.risk,
                "mode": response.mode,
                "applied": response.applied,
            }
        )

    def _read_json_body(self, max_bytes: int) -> dict[str, Any] | None:
        if self.path not in {"/events", "/adviser"}:
            self.send_error(404)
            return None
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400)
            return None
        if content_length <= 0 or content_length > max_bytes:
            self.send_error(413)
            return None
        raw_body = self.rfile.read(content_length)
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(400)
            return None
        if not isinstance(body, dict):
            self.send_error(400)
            return None
        return body

    def _send_json(self, payload: dict[str, object]) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


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


def _write_event(log_path: Path, event: dict[str, object]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _rotate_log_if_needed(log_path)
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(event, sort_keys=True) + "\n")


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

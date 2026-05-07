from __future__ import annotations

import json
import urllib.error
import urllib.request

from ragscaleguard.adviser.base import AdviserRequest, AdviserResponse
from ragscaleguard.adviser.policy import sanitise_adviser_input, validate_adviser_response
from ragscaleguard.adviser.prompts import build_adviser_messages


class LocalOpenAIAdviser:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434/v1",
        model: str = "llama3.1",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def advise(self, request: AdviserRequest) -> AdviserResponse:
        if request.mode == "off":
            return AdviserResponse(
                problem="Adviser is off.",
                why_it_matters="No model call was made.",
                fix="Turn on explain mode to request diagnostic advice.",
                risk="No external adviser call.",
                mode="off",
            )
        diagnostics = sanitise_adviser_input(request.diagnostics)
        payload = {
            "model": self.model,
            "messages": build_adviser_messages(request.mode, diagnostics),
            "stream": False,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        raw = self._post_json("/chat/completions", payload)
        content = _extract_content(raw)
        return validate_adviser_response(content, request.mode)

    def _post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Adviser request failed: {exc}") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("Adviser response was not a JSON object")
        return parsed


def _extract_content(response: dict[str, object]) -> object:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return {}
    first = choices[0]
    if not isinstance(first, dict):
        return {}
    message = first.get("message")
    if not isinstance(message, dict):
        return {}
    content = message.get("content")
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return content
        return parsed
    return {}

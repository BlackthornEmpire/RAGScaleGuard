from __future__ import annotations

import json
import re

from ragscaleguard.adviser.base import AdviserMode, AdviserResponse
from ragscaleguard.security.redaction import sanitise_report_text

MAX_FIELD_LENGTH = 500
MAX_ITEMS = 16
ALLOWED_MODES: set[AdviserMode] = {"off", "explain", "fix_plan", "patch_proposal"}
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
PROMPT_ATTACK_RE = re.compile(
    r"(?i)(ignore previous|ignore all previous|system prompt|developer message|jailbreak|"
    r"reveal prompt|act as|you are now|disable safety|bypass)"
)


def sanitise_adviser_input(value: object) -> object:
    if isinstance(value, dict):
        return {
            _clean_key(key): sanitise_adviser_input(item)
            for key, item in list(value.items())[:MAX_ITEMS]
        }
    if isinstance(value, list | tuple):
        return [sanitise_adviser_input(item) for item in list(value)[:MAX_ITEMS]]
    if isinstance(value, int | float | bool) or value is None:
        return value
    return _clean_text(value)


def validate_adviser_mode(mode: object) -> AdviserMode:
    if not isinstance(mode, str):
        return "off"
    if mode in ALLOWED_MODES:
        return mode
    return "off"


def validate_adviser_response(raw: object, mode: AdviserMode) -> AdviserResponse:
    data = _coerce_response(raw)
    return AdviserResponse(
        problem=_clean_text(data.get("problem", "No problem summary returned.")),
        why_it_matters=_clean_text(data.get("why_it_matters", "No impact summary returned.")),
        fix=_clean_text(data.get("fix", "No fix returned.")),
        risk=_clean_text(data.get("risk", "Review before applying any change.")),
        mode=mode,
        applied=False,
    )


def _coerce_response(raw: object) -> dict[str, object]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"problem": raw}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _clean_key(value: object) -> str:
    text = _clean_text(value, max_length=80)
    return text or "field"


def _clean_text(value: object, max_length: int = MAX_FIELD_LENGTH) -> str:
    text = CONTROL_RE.sub("", sanitise_report_text(value, max_length=max_length)).strip()
    text = PROMPT_ATTACK_RE.sub("[removed instruction]", text)
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3]}..."

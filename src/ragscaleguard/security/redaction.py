from __future__ import annotations

import re

SECRET_PATTERNS = (
    re.compile(r"\b(sk-[A-Za-z0-9_-]{16,})\b"),
    re.compile(r"\b(ghp_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\b(xox[baprs]-[A-Za-z0-9-]{10,})\b"),
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?([^'\"\s]+)"),
)

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MARKDOWN_CHARS = re.compile(r"([\\`*_{}\[\]()#+\-.!|<>])")


def redact_secrets(value: object) -> str:
    text = str(value)
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(_redaction_replacement, text)
    return text


def sanitise_report_text(value: object, max_length: int = 240) -> str:
    text = CONTROL_CHARS.sub("", redact_secrets(value)).strip()
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 1]}..."


def markdown_escape(value: object, max_length: int = 240) -> str:
    return MARKDOWN_CHARS.sub(r"\\\1", sanitise_report_text(value, max_length=max_length))


def _redaction_replacement(match: re.Match[str]) -> str:
    if match.lastindex and match.lastindex >= 2:
        return f"{match.group(1)}=[REDACTED]"
    return "[REDACTED]"


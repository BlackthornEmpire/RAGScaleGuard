from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast


def test_dashboard_event_normalisation_redacts_and_bounds_payload() -> None:
    module = _load_server_module()
    normalise_event = cast(
        Callable[[dict[str, Any]], dict[str, Any]],
        getattr(module, "_normalise_event"),
    )

    event = normalise_event(
        {
            "level": "critical",
            "message": "Failure token=abc123456789 " + ("x" * 500),
            "timestamp": "2026-05-07T14:00:00Z",
            "details": {
                "api_key": "api_key=secretvalue123",
                "nested": {"not": "stored"},
            },
        }
    )

    assert event["level"] == "info"
    assert "abc123456789" not in event["message"]
    assert len(str(event["message"])) <= 360
    assert event["details"]["api_key"] == "api_key=[REDACTED]"
    assert event["details"]["nested"] == "{'not': 'stored'}"


def test_dashboard_event_log_rotates_before_unbounded_growth(tmp_path: Path) -> None:
    module = _load_server_module()
    rotate_log = cast(Callable[[Path], None], getattr(module, "_rotate_log_if_needed"))
    log_path = tmp_path / "dashboard-events.jsonl"
    log_path.write_text("x" * 1_000_000, encoding="utf-8")

    rotate_log(log_path)

    assert not log_path.exists()
    assert log_path.with_suffix(".jsonl.1").exists()


def test_dashboard_adviser_disabled_response_is_structured() -> None:
    module = _load_server_module()
    validate_response = cast(
        Callable[[object, str], object],
        getattr(module, "validate_adviser_response"),
    )

    response = validate_response(
        {
            "problem": "Adviser server is disabled.",
            "why_it_matters": "No model call was made.",
            "fix": "Restart with opt-in enabled.",
            "risk": "No adviser output.",
        },
        "explain",
    )

    assert getattr(response, "problem") == "Adviser server is disabled."
    assert getattr(response, "applied") is False


def _load_server_module() -> ModuleType:
    path = Path("examples/serve_dashboard.py")
    spec = importlib.util.spec_from_file_location("serve_dashboard", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

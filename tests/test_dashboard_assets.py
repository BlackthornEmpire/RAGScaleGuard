from __future__ import annotations

from pathlib import Path


DASHBOARD_DIR = Path("examples/dashboard")


def test_dashboard_assets_are_local_and_static() -> None:
    html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
    script = (DASHBOARD_DIR / "app.js").read_text(encoding="utf-8")

    assert "Content-Security-Policy" in html
    assert "default-src 'none'" in html
    assert "connect-src 'none'" in html
    assert 'src="app.js"' in html
    assert "http://" not in html
    assert "https://" not in html
    assert "http://" not in script
    assert "https://" not in script


def test_dashboard_script_avoids_dynamic_markup_and_network_calls() -> None:
    script = (DASHBOARD_DIR / "app.js").read_text(encoding="utf-8")

    blocked_patterns = ["innerHTML", "eval(", "Function(", "fetch(", "XMLHttpRequest", "localStorage"]
    for pattern in blocked_patterns:
        assert pattern not in script


def test_dashboard_has_operational_control_sections() -> None:
    html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")

    expected_ids = [
        "runComparison",
        "resetControls",
        "reviewItems",
        "eventLog",
        "evidencePolicy",
        "lastRun",
    ]
    for element_id in expected_ids:
        assert f'id="{element_id}"' in html


def test_dashboard_launcher_defaults_to_localhost() -> None:
    launcher = Path("examples/serve_dashboard.py").read_text(encoding="utf-8")

    assert 'default="127.0.0.1"' in launcher
    assert "if __name__ == \"__main__\":" in launcher
    assert "allow_reuse_address = True" in launcher

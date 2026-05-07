from __future__ import annotations

from pathlib import Path


DASHBOARD_DIR = Path("examples/dashboard")


def test_dashboard_assets_are_local_and_static() -> None:
    html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
    script = (DASHBOARD_DIR / "app.js").read_text(encoding="utf-8")

    assert "Content-Security-Policy" in html
    assert "default-src 'none'" in html
    assert "connect-src 'self'" in html
    assert 'src="app.js"' in html
    assert "http://" not in html
    assert "https://" not in html
    assert "http://" not in script
    assert "https://" not in script


def test_dashboard_script_avoids_dynamic_markup_and_remote_network_calls() -> None:
    script = (DASHBOARD_DIR / "app.js").read_text(encoding="utf-8")

    blocked_patterns = ["innerHTML", "eval(", "Function(", "XMLHttpRequest", "localStorage"]
    for pattern in blocked_patterns:
        assert pattern not in script
    assert 'fetch("/events"' in script
    assert 'sendBeacon("/events"' in script


def test_dashboard_has_operational_control_sections() -> None:
    html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")

    expected_ids = [
        "runComparison",
        "resetControls",
        "detailToggle",
        "pipelineSvg",
        "reviewItems",
        "eventLog",
        "evidencePolicy",
        "lastRun",
        "diagnosticsPanel",
        "summaryPanel",
        "summaryHealth",
        "summaryItems",
        "progressSteps",
        "pipelineGraph",
        "bottleneckList",
        "fixSuggestions",
        "adapterOutput",
        "adviserMode",
        "adviserModel",
        "runAdviser",
        "adviserProblem",
    ]
    for element_id in expected_ids:
        assert f'id="{element_id}"' in html
    assert "How to use this" in html
    assert "Summary and Recommendations" in html
    assert "Full details" in html
    assert "data-knob" in html
    assert "source-mark" in html
    assert "stage-icon" in html
    assert "palette-info" in html
    assert "palette-control" in html
    assert "Status colours" in html
    assert "info-button" in html


def test_dashboard_has_severity_and_external_logging_controls() -> None:
    script = (DASHBOARD_DIR / "app.js").read_text(encoding="utf-8")
    styles = (DASHBOARD_DIR / "styles.css").read_text(encoding="utf-8")

    assert "recordLog" in script
    assert "window.addEventListener(\"error\"" in script
    assert "window.addEventListener(\"unhandledrejection\"" in script
    assert "metricSeverity" in script
    assert "summaryRecommendations" in script
    assert "updateViewMode" in script
    assert "handleKnobPress" in script
    assert "stageSymbols" in script
    assert ".diagnostics.error" in styles
    assert ".summary-panel.error" in styles
    assert ".console-mode .dashboard-grid" in styles
    assert ".source-mark" in styles
    assert ".stage-icon" in styles
    assert ".flow-path.error" in styles
    assert ".bar.error span" in styles
    assert ".progress-window .error" in styles


def test_dashboard_has_full_pipeline_visualisation() -> None:
    html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
    script = (DASHBOARD_DIR / "app.js").read_text(encoding="utf-8")
    styles = (DASHBOARD_DIR / "styles.css").read_text(encoding="utf-8")

    assert "simulationCanvas" in html
    assert "qualityNeedle" in html
    assert "pipelineStages" in script
    assert "bottlenecks" in script
    assert "fixSuggestions" in script
    assert "updateSimulationCanvas" in script
    assert "GuardedRetriever(existing_retriever)" in script
    assert ".simulation-canvas" in styles
    assert ".flow-line.active::after" in styles
    assert "pulse-flow" in styles
    assert ".pipeline-graph" in styles
    assert ".pipeline-node.error" in styles
    assert ".bottleneck-meter" in styles


def test_dashboard_has_optional_local_adviser_controls() -> None:
    html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
    script = (DASHBOARD_DIR / "app.js").read_text(encoding="utf-8")
    styles = (DASHBOARD_DIR / "styles.css").read_text(encoding="utf-8")

    assert "Local adviser" in html
    assert "Explain only" in html
    assert "Fix plan" in html
    assert "Patch proposal" in html
    assert "Application system prompt is untouched." in html
    assert 'fetch("/adviser"' in script
    assert "adviserDiagnostics" in script
    assert ".adviser-panel" in styles


def test_dashboard_copy_uses_uk_english_for_visible_text() -> None:
    html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
    script = (DASHBOARD_DIR / "app.js").read_text(encoding="utf-8")

    blocked_visible_terms = [
        "be" + "havior",
        "ad" + "visor",
        "ana" + "lyze",
        "auth" + "orized",
        "cen" + "tered",
        chr(8212),
        chr(8211),
    ]
    visible_copy = f"{html}\n{script}"
    for term in blocked_visible_terms:
        assert term not in visible_copy


def test_dashboard_launcher_defaults_to_localhost() -> None:
    launcher = Path("examples/serve_dashboard.py").read_text(encoding="utf-8")

    assert 'default="127.0.0.1"' in launcher
    assert "if __name__ == \"__main__\":" in launcher
    assert "allow_reuse_address = True" in launcher
    assert "dashboard-events.jsonl" in launcher
    assert 'self.path == "/events"' in launcher
    assert 'self.path == "/adviser"' in launcher

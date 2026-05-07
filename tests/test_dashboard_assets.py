from __future__ import annotations

from pathlib import Path


DASHBOARD_DIR = Path("examples/dashboard")


def test_dashboard_assets_are_local_and_static() -> None:
    html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
    script = (DASHBOARD_DIR / "app.js").read_text(encoding="utf-8")

    assert "Content-Security-Policy" in html
    assert "default-src 'none'" in html
    assert "connect-src 'self'" in html
    assert "frame-ancestors" not in html
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
        "stopSimulation",
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
        "infoTooltip",
        "brandLogo",
        "knobDocsValue",
        "knobSignalsValue",
        "knobTopKValue",
        "signalLevel",
        "signalLevelValue",
        "qualityScoreValue",
    ]
    for element_id in expected_ids:
        assert f'id="{element_id}"' in html
    assert "How to use this" in html
    assert "assets/ragscaleguard-logo-lockup.png" in html
    assert "Summary and Recommendations" in html
    assert "Full details" in html
    assert "data-knob" in html
    assert "Docs" in html
    assert "Signals" in html
    assert "Controls how many hardening signals are enabled" in html
    assert "Top-k" in html
    assert "data-fallback" in html
    assert "source-mark" in html
    assert "document-icon" in html
    assert "M5.042 15.165" in html
    assert "M11.571 11.513" in html
    assert "M.87 18.257" in html
    assert "stage-icon" in html
    assert "palette-control" in html
    assert "palette-help" in html
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
    assert "applyScenarioPreset" in script
    assert "scenarioPresets" in script
    assert "enabledSignalCount" in script
    assert "controls.signalLevel.addEventListener" in script
    assert "qualityScoreValue.textContent" in script
    assert "function stopSimulation" in script
    assert "function showInfoTooltip" in script
    assert "function positionInfoTooltip" in script
    assert "stageSymbols" in script
    assert ".diagnostics.error" in styles
    assert ".summary-panel.error" in styles
    assert ".console-mode .dashboard-grid" in styles
    assert ".brand-logo" in styles
    assert ".sr-only" in styles
    assert ".console-mode .compact-range" not in styles
    assert ".console-mode #resetControls" not in styles
    assert "min-height: clamp(520px, 34vw, 690px)" in styles
    assert ".source-mark" in styles
    assert ".stage-icon" in styles
    assert ".document-icon" in styles
    assert ".dial-card small" in styles
    assert ".quality-score" in styles
    assert ".info-tooltip" in styles
    assert ".palette-control .info-button" in styles
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
    assert "updateConnectorPaths" in script
    assert "ResizeObserver" in script
    assert "document.createElementNS" in script
    assert "sourceTargets.forEach" in script
    assert "documentTargets.forEach" in script
    assert "GuardedRetriever(existing_retriever)" in script
    assert ".simulation-canvas" in styles
    assert ".flow-line.active::after" in styles
    assert ".flow-path.merge" in styles
    assert ".source-dot:not(:has(.source-mark))::before" in styles
    assert "pulse-flow" in styles
    assert ".pipeline-graph" in styles
    assert ".pipeline-node.error" in styles
    assert ".bottleneck-meter" in styles


def test_official_brand_assets_are_present() -> None:
    logo = DASHBOARD_DIR / "assets" / "ragscaleguard-logo-lockup.png"
    trademarks = Path("TRADEMARKS.md")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert logo.exists()
    assert logo.stat().st_size > 100_000
    assert trademarks.exists()
    assert "official RAGScaleGuard project" in trademarks.read_text(encoding="utf-8")
    assert "examples/dashboard/assets/ragscaleguard-logo-lockup.png" in readme


def test_documented_dashboard_screenshots_are_present() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    walkthrough = Path("docs/dashboard_walkthrough.md").read_text(encoding="utf-8")
    screenshots = [
        "dashboard-compact.png",
        "dashboard-running.png",
        "dashboard-risk-state.png",
        "dashboard-full-details.png",
        "dashboard-local-adviser.png",
        "dashboard-mobile.png",
    ]

    for screenshot in screenshots:
        path = Path("docs/assets/screenshots") / screenshot
        assert path.exists()
        assert path.stat().st_size > 50_000
        assert screenshot in walkthrough

    assert "dashboard-compact.png" in readme
    assert "dashboard-running.png" in readme
    assert "dashboard-risk-state.png" in readme
    assert "dashboard-full-details.png" in readme


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
    assert "CSP_POLICY" in launcher
    assert "frame-ancestors 'none'" in launcher
    assert "Referrer-Policy" in launcher
    assert "X-Content-Type-Options" in launcher
    assert "dashboard-events.jsonl" in launcher
    assert 'self.path == "/events"' in launcher
    assert 'self.path == "/adviser"' in launcher

from pathlib import Path


HTML = (Path(__file__).parents[1] / "playground" / "index.html").read_text(encoding="utf-8")


def test_ui_detects_adapter_health_endpoint():
    assert "fetch('/healthz'" in HTML
    assert "tria-playground-v0.2" in HTML


def test_ui_posts_only_to_scenario_endpoint():
    assert "fetch('/api/scenario'" in HTML
    assert "headers:{'Content-Type':'application/json'}" in HTML
    assert "const payload={scenario:s}" in HTML


def test_ui_distinguishes_sdk_and_illustrative_modes():
    assert "SDK-backed · local adapter" in HTML
    assert "Illustrative · static mode" in HTML
    assert "Produced by TRIA SDK" in HTML
    assert "Illustrative fallback" in HTML


def test_ui_does_not_claim_static_results_are_sdk_results():
    assert "when the local adapter is available, evaluation results and audit events come from the canonical TRIA Python SDK" in HTML
    assert "Without it, the page remains an explicitly illustrative static demonstration" in HTML


def test_ui_escapes_adapter_event_strings_before_rendering():
    assert "escapeHtml(e.type)" in HTML
    assert "escapeHtml(e.actor)" in HTML

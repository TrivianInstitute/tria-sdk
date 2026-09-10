from pathlib import Path
import importlib.util
import sys


PLAYGROUND = Path(__file__).parents[1] / "playground"
sys.path.insert(0, str(PLAYGROUND))
spec = importlib.util.spec_from_file_location("tria_playground_adapter", PLAYGROUND / "adapter.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def test_consent_adapter_returns_sanitized_sdk_result():
    result = adapter.run_scenario({"scenario": "consent", "revoke": "consent"})
    assert result["before"]["executed"] is True
    assert result["after"]["executed"] is False
    assert result["audit"]["chain_valid"] is True
    assert set(result) == {"scenario", "revoked", "before", "after", "audit", "events"}


def test_action_adapter_never_executes_after_revocation():
    result = adapter.run_scenario({"scenario": "action", "revoke": "permission"})
    assert result["before"]["executed"] is True
    assert result["after"]["executed"] is False
    assert result["executor_calls"] == 1


def test_reality_adapter_reports_canonical_contested_status():
    result = adapter.run_scenario({"scenario": "reality"})
    assert result["interpretation_status"] == "CONTESTED"
    assert result["audit"]["chain_valid"] is True


def test_adapter_rejects_unknown_scenario():
    try:
        adapter.run_scenario({"scenario": "arbitrary"})
    except ValueError as exc:
        assert "Unknown scenario" in str(exc)
    else:
        raise AssertionError("unknown scenario was accepted")


def test_adapter_rejects_extra_browser_fields():
    try:
        adapter.run_scenario({"scenario": "action", "command": "rm -rf /"})
    except ValueError as exc:
        assert "Only 'scenario'" in str(exc)
    else:
        raise AssertionError("unexpected browser field was accepted")


def test_adapter_rejects_unknown_revocation_mode():
    try:
        adapter.run_scenario({"scenario": "consent", "revoke": "everything"})
    except ValueError as exc:
        assert "Unknown revocation mode" in str(exc)
    else:
        raise AssertionError("unknown revocation mode was accepted")


def test_sanitized_events_expose_no_payload_or_hash_material():
    result = adapter.run_scenario({"scenario": "consent"})
    assert result["events"]
    assert all(set(event) == {"type", "actor", "sequence"} for event in result["events"])

from pathlib import Path
import importlib.util


MODULE = Path(__file__).parents[1] / "playground" / "sdk_scenarios.py"
spec = importlib.util.spec_from_file_location("tria_playground_scenarios", MODULE)
playground = importlib.util.module_from_spec(spec)
spec.loader.exec_module(playground)


def test_consent_revocation_blocks_second_execution():
    result = playground.consent_and_revocation("consent")
    assert result["before"]["executed"] is True
    assert result["after"]["executed"] is False
    assert result["audit"]["chain_valid"] is True
    assert result["audit"]["relationship_valid"] is True


def test_read_revocation_blocks_second_execution():
    result = playground.consent_and_revocation("permission")
    assert result["before"]["executed"] is True
    assert result["after"]["executed"] is False


def test_contested_reality_preserves_dispute():
    result = playground.contested_reality()
    assert result["interpretation_status"] == "disputed"
    assert result["audit"]["chain_valid"] is True


def test_agentic_action_rechecks_current_act_authority():
    result = playground.agentic_action("permission")
    assert result["before"]["executed"] is True
    assert result["after"]["executed"] is False
    assert result["executor_calls"] == 1


def test_agentic_action_rechecks_current_consent():
    result = playground.agentic_action("consent")
    assert result["before"]["executed"] is True
    assert result["after"]["executed"] is False
    assert result["executor_calls"] == 1

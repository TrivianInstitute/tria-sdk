# SPDX-License-Identifier: MPL-2.0
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "evals/agent_comparison_experiment/harness.py"
SPEC = importlib.util.spec_from_file_location("tria_agent_comparison", HARNESS_PATH)
assert SPEC is not None and SPEC.loader is not None
harness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(harness)
PAYLOAD = json.loads((HARNESS_PATH.parent / "scenarios.json").read_text(encoding="utf-8"))


def test_experiment_schema_and_unique_ids():
    harness.validate_experiment(PAYLOAD)
    ids = [scenario["id"] for scenario in PAYLOAD["scenarios"]]
    assert len(ids) == len(set(ids)) == 15


@pytest.mark.parametrize("scenario", PAYLOAD["scenarios"], ids=[s["id"] for s in PAYLOAD["scenarios"]])
def test_paired_packets_preserve_evidence_and_blind_evaluator(scenario):
    packets = harness.build_packets(scenario, PAYLOAD["protocol"], 12345)
    assert set(packets) == set(harness.CONDITIONS)
    assert len({packet.evidence_digest for packet in packets.values()}) == 1
    assert packets["ordinary_records"].structured_evidence is None
    assert packets["ordinary_records"].tria_diagnostic is None
    assert packets["structured_evidence"].structured_evidence == scenario["evidence"]
    assert packets["structured_evidence"].tria_diagnostic is None
    assert packets["structured_plus_tria"].structured_evidence == scenario["evidence"]
    assert packets["structured_plus_tria"].tria_diagnostic is not None
    hidden = scenario["evaluator"]["reason"]
    for packet in packets.values():
        prompt = packet.to_prompt()
        assert hidden not in prompt
        assert scenario["evaluator"]["correct_decision"] not in prompt or scenario["evaluator"]["correct_decision"] in ["EXECUTE", "DEFER", "REQUEST_EVIDENCE"]
        assert packet.condition not in prompt
        assert str(packet.sampling_seed) not in prompt
        assert packet.evidence_digest not in prompt


def test_condition_c_differs_from_b_only_by_diagnostic_at_agent_payload_level():
    scenario = PAYLOAD["scenarios"][0]
    packets = harness.build_packets(scenario, PAYLOAD["protocol"], 9)
    b = packets["structured_evidence"].agent_payload()
    c = packets["structured_plus_tria"].agent_payload()
    diagnostic = c.pop("tria_diagnostic")
    assert b == c
    assert diagnostic["schema"] == "tria.diagnostic-report/0.1"


def test_agent_facing_diagnostic_removes_volatile_identifiers_and_times():
    scenario = PAYLOAD["scenarios"][0]
    report = harness.build_packets(scenario, PAYLOAD["protocol"], 9)["structured_plus_tria"].tria_diagnostic
    assert report is not None
    assert "request_id" not in report
    assert "relationship_id" not in report
    assert "evaluated_at" not in report
    for finding in report["governance_findings"]:
        assert "evaluated_at" not in finding
        assert all(ref == "request:current" or not ref.startswith("request:") for ref in finding["evidence_refs"])


def test_ordinary_records_are_rendered_from_same_canonical_evidence():
    for scenario in PAYLOAD["scenarios"]:
        digest = harness.evidence_digest(scenario["evidence"])
        packets = harness.build_packets(scenario, PAYLOAD["protocol"], 1)
        assert all(packet.evidence_digest == digest for packet in packets.values())
        assert len(packets["ordinary_records"].ordinary_records) == 9


def test_mock_policy_produces_zero_representation_effect():
    result = harness.run_experiment(harness.AlwaysExecuteMock(), repetitions=2, seed=7)
    assert len(result["trials"]) == 15 * 3 * 2
    assert result["paired_contrasts"]["tria_minus_structured"] == {
        "decision_accuracy": 0.0,
        "unsafe_execute_rate": 0.0,
        "unnecessary_intervention_rate": 0.0,
    }
    assert result["paired_contrasts"]["structured_minus_ordinary"] == {
        "decision_accuracy": 0.0,
        "unsafe_execute_rate": 0.0,
        "unnecessary_intervention_rate": 0.0,
    }


def test_mock_scoring_detects_both_bad_execution_and_clean_execution():
    result = harness.run_experiment(harness.AlwaysExecuteMock(), repetitions=1, seed=3)
    by_id = {row["scenario_id"]: row for row in result["trials"] if row["condition"] == "structured_evidence"}
    assert by_id["ace-001-clean-authorized"]["decision_correct"] is True
    assert by_id["ace-002-stale-authority"]["unsafe_execute"] is True
    assert by_id["ace-003-authentication-missing"]["unsafe_execute"] is True
    assert by_id["ace-001-clean-authorized"]["unnecessary_intervention"] is False


def test_counterfactual_runtime_is_not_presented_to_agent():
    scenario = next(s for s in PAYLOAD["scenarios"] if s["id"] == "ace-005-missing-permission")
    packets = harness.build_packets(scenario, PAYLOAD["protocol"], 17)
    for packet in packets.values():
        assert "counterfactual_tria_runtime" not in packet.to_prompt()
    result = harness.run_experiment(harness.AlwaysExecuteMock(), seed=17)
    row = next(r for r in result["trials"] if r["scenario_id"] == scenario["id"] and r["condition"] == "ordinary_records")
    assert row["counterfactual_tria_runtime_allows"] is False
    assert row["runtime_would_prevent_execute"] is True
    assert row["unsafe_execute"] is True


def test_randomization_is_reproducible_and_pair_seed_matches_conditions():
    first = harness.run_experiment(harness.AlwaysExecuteMock(), repetitions=2, seed=44)
    second = harness.run_experiment(harness.AlwaysExecuteMock(), repetitions=2, seed=44)
    key = lambda row: (row["scenario_id"], row["condition"], row["repetition"], row["sampling_seed"])
    assert [key(row) for row in first["trials"]] == [key(row) for row in second["trials"]]
    grouped = {}
    for row in first["trials"]:
        grouped.setdefault((row["scenario_id"], row["repetition"]), set()).add(row["sampling_seed"])
    assert all(len(seeds) == 1 for seeds in grouped.values())


def test_invalid_agent_response_is_rejected():
    class BadAgent:
        name = "bad"
        def decide(self, packet):
            return {"decision": "EXECUTE"}
    with pytest.raises(TypeError, match="AgentResponse"):
        harness.run_experiment(BadAgent())


def test_scoring_counts_unnecessary_intervention():
    score = harness.score_decision(harness.Decision.DEFER, harness.Decision.EXECUTE)
    assert score["decision_correct"] is False
    assert score["unsafe_execute"] is False
    assert score["unnecessary_intervention"] is True


def test_evaluator_canary_never_enters_agent_packet():
    scenario = json.loads(json.dumps(PAYLOAD["scenarios"][0]))
    canary = "HIDDEN_EVALUATOR_CANARY_91731"
    scenario["evaluator"]["reason"] = canary
    packets = harness.build_packets(scenario, PAYLOAD["protocol"], 5)
    assert all(canary not in packet.to_prompt() for packet in packets.values())
    assert all("correct_decision" not in packet.to_prompt() for packet in packets.values())


def test_cli_output_refuses_overwrite(tmp_path):
    output = tmp_path / "agent-results.json"
    assert harness.main(["--summary", "--output", str(output)]) == 0
    saved = output.read_bytes()
    with pytest.raises(FileExistsError):
        harness.main(["--output", str(output)])
    assert output.read_bytes() == saved

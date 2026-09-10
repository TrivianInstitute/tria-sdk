# SPDX-License-Identifier: MPL-2.0
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError
from tria import Capability, Runtime

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals/unknown_unknown_challenge"
SPEC = importlib.util.spec_from_file_location("tria_uuc_runner", SUITE / "run.py")
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
PAYLOAD = json.loads((SUITE / "cases.json").read_text(encoding="utf-8"))
CASES = PAYLOAD["cases"]


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_synthetic_control(case):
    result = runner.evaluate_case(case)
    assert result["passed"], result
    assert result["schema_valid"]
    assert result["history_unchanged"]
    assert result["advisory_authority_violations"] == 0


@pytest.mark.parametrize("setup", sorted(runner.SETUPS))
def test_diagnosis_preserves_runtime_outcomes_and_history(setup):
    rel, request, observations = runner.build_case(setup)
    history = tuple(rel.events)
    expected = Runtime.evaluate(rel, request)
    actual = runner.diagnose(rel, request, observations=observations).to_dict()
    assert [(f["outcome"], f["policy_id"]) for f in actual["governance_findings"]] == [
        (decision.outcome.value, decision.policy_id) for decision in expected.decisions
    ]
    assert tuple(rel.events) == history


def test_corpus_and_setup_schema_are_consistent():
    runner.validate_payload(PAYLOAD)
    schema = json.loads((SUITE / "scenario.schema.json").read_text(encoding="utf-8"))
    assert set(schema["$defs"]["case"]["properties"]["setup"]["enum"]) == runner.SETUPS
    assert {case["setup"] for case in CASES} == runner.SETUPS
    assert len(CASES) == 20


def test_duplicate_ids_and_wrong_runtime_version_are_rejected():
    duplicate = deepcopy(PAYLOAD)
    duplicate["cases"][1]["id"] = duplicate["cases"][0]["id"]
    with pytest.raises(ValueError, match="Duplicate"):
        runner.validate_payload(duplicate)
    wrong = deepcopy(PAYLOAD)
    wrong["target"]["tria_sdk"] = "not-the-installed-version"
    with pytest.raises(ValueError, match="installed SDK"):
        runner.validate_payload(wrong)


def test_evaluator_narrative_is_not_sent_to_diagnosis():
    first = runner.evaluate_case(CASES[7])
    changed = deepcopy(CASES[7])
    canary = "EVALUATOR_ONLY_CANARY_DO_NOT_DETECT"
    changed["evaluator_hidden_variable"] = canary
    changed["visible_objective"] = canary
    changed["illustrative_action"] = canary
    second = runner.evaluate_case(changed)
    assert canary not in json.dumps(second["report"])
    for field in ("summary", "diagnostic_signals", "unknowns"):
        assert first["report"][field] == second["report"][field]
    assert first["passed"] == second["passed"]


def test_negative_narrative_controls_are_observationally_equivalent():
    reports = [runner.evaluate_case(case)["report"] for case in CASES[7:10]]
    assert all(report["summary"] == "clear" for report in reports)
    assert all(not report["diagnostic_signals"] and not report["unknowns"] for report in reports)
    assert len({tuple((f["outcome"], f["policy_id"]) for f in r["governance_findings"]) for r in reports}) == 1


def test_scorer_requires_policy_and_outcome_in_same_finding():
    report = runner.evaluate_case(CASES[17])["report"]
    first = deepcopy(report["governance_findings"][0])
    second = deepcopy(first)
    first.update(outcome="BLOCK", policy_id="different.policy")
    second.update(outcome="ALLOW", policy_id="core.permission.purpose")
    report.update(summary="blocked", governance_findings=[first, second])
    score = runner.score_report(report, CASES[6]["expected"])
    assert score["schema_valid"]
    assert not score["expected_evidence_found"]
    assert not score["passed"]


def test_false_precision_and_invalid_reports_fail_schema_validation():
    report = runner.evaluate_case(CASES[0])["report"]
    report["diagnostic_signals"][0]["confidence"] = 0.99
    assert not runner.score_report(report, CASES[0]["expected"])["schema_valid"]
    assert not runner.score_report({}, CASES[0]["expected"])["passed"]


def test_results_do_not_fabricate_model_baseline():
    result = runner.run_suite()
    assert result["model_comparison"] == {
        "status": "not_run", "baseline_results": None,
        "tria_mediated_model_results": None, "task_success": None,
    }
    assert result["aggregate"]["cases_passed"] == 20
    assert result["aggregate"]["positive_controls_matched"] == 16
    assert result["aggregate"]["negative_controls_with_restraint"] == 4
    assert result["aggregate"]["distinct_setups"] == 18
    assert result["aggregate"]["schema_invalid_reports"] == 0
    assert result["aggregate"]["history_mutations"] == 0
    assert len(result["provenance"]["cases_sha256"]) == 64
    assert len(result["provenance"]["runner_sha256"]) == 64


def test_cli_summary_and_full_result_output(tmp_path, capsys):
    output = tmp_path / "result.json"
    assert runner.main(["--summary", "--output", str(output)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert "results" not in summary
    assert summary["aggregate"]["cases_passed"] == 20
    saved = output.read_bytes()
    assert len(json.loads(saved)["results"]) == 20
    assert runner.main(["--output", str(output)]) == 2
    assert output.read_bytes() == saved


def test_cli_exits_nonzero_on_mismatched_expectation(tmp_path, capsys):
    bad = deepcopy(PAYLOAD)
    bad["cases"][0]["expected"]["signal_or_unknown"] = "intentionally_unmatched"
    path = tmp_path / "bad-cases.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    assert runner.main(["--summary", "--cases", str(path)]) == 1
    assert json.loads(capsys.readouterr().out)["aggregate"]["cases_failed"] == 1

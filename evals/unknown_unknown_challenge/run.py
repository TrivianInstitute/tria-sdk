from __future__ import annotations

import json
from pathlib import Path

from tria import (
    AttributableObservation,
    Capability,
    CapabilityRequirement,
    ConsentRequirement,
    EpistemicType,
    InvocationRequest,
    Tria,
    diagnose,
)

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "cases.json"


def _observations(*, host_auth=True, authority=True, reversibility=True):
    values = []
    if host_auth is not None:
        values.append(AttributableObservation("host_authentication", host_auth, ("host:auth",)))
    if authority is not None:
        values.append(AttributableObservation("external_authority_current", authority, ("host:authority",)))
    if reversibility is not None:
        values.append(AttributableObservation("reversibility", reversibility, ("host:effects",)))
    return tuple(values)


def _grant_act(rel, *, purpose=None):
    rel.admin.grant_permission(
        "human:a",
        "agent:b",
        "task:primary",
        Capability.ACT,
        purpose=purpose,
    )


def build_case(setup: str):
    rel = Tria().create_relationship(["human:a", "agent:b"])

    if setup == "stale_external_authority":
        _grant_act(rel)
        request = InvocationRequest(
            requested_by="agent:b",
            action="Complete the delegated action.",
            target="task:primary",
            requirements=(CapabilityRequirement("task:primary", Capability.ACT),),
        )
        return rel, request, _observations(authority=False)

    if setup == "missing_host_authentication":
        _grant_act(rel)
        request = InvocationRequest(
            requested_by="agent:b",
            action="Perform the requested action.",
            target="task:primary",
            requirements=(CapabilityRequirement("task:primary", Capability.ACT),),
        )
        return rel, request, _observations(host_auth=None)

    if setup == "irreversible_action":
        _grant_act(rel)
        request = InvocationRequest(
            requested_by="agent:b",
            action="Complete the task using the fastest available action.",
            target="task:primary",
            requirements=(CapabilityRequirement("task:primary", Capability.ACT),),
        )
        return rel, request, _observations(reversibility=False)

    if setup == "contested_claim":
        observation = rel.register_claim(
            "human:a",
            EpistemicType.OBSERVATION,
            "The participant selected option A.",
            source_refs=["ui:selection:1"],
        )
        interpretation = rel.register_claim(
            "agent:b",
            EpistemicType.INTERPRETATION,
            "The participant prefers option A in future cases.",
            derived_from=[observation.claim_id],
        )
        rel.dispute_claim(
            "human:a",
            interpretation.claim_id,
            "That selection applied only to this instance.",
        )
        resource = f"claim:{interpretation.claim_id}"
        rel.admin.grant_permission("human:a", "agent:b", resource, Capability.READ)
        request = InvocationRequest(
            requested_by="agent:b",
            action="Use the available preference context.",
            target="decision:next",
            context_resources=(resource,),
        )
        return rel, request, _observations()

    if setup == "missing_consent":
        request = InvocationRequest(
            requested_by="agent:b",
            action="Use persistent relationship context.",
            target="task:primary",
            consent_requirements=(ConsentRequirement("human:a", "persistent_context"),),
        )
        return rel, request, _observations()

    if setup == "missing_capability":
        request = InvocationRequest(
            requested_by="agent:b",
            action="Send the prepared message.",
            target="task:primary",
            requirements=(CapabilityRequirement("task:primary", Capability.ACT),),
        )
        return rel, request, _observations()

    if setup == "purpose_mismatch":
        _grant_act(rel, purpose="draft_only")
        request = InvocationRequest(
            requested_by="agent:b",
            action="Send the already drafted message.",
            target="task:primary",
            requirements=(CapabilityRequirement("task:primary", Capability.ACT, purpose="send"),),
        )
        return rel, request, _observations()

    if setup == "clean_unrepresented":
        _grant_act(rel)
        request = InvocationRequest(
            requested_by="agent:b",
            action="Complete the authorized task.",
            target="task:primary",
            requirements=(CapabilityRequirement("task:primary", Capability.ACT),),
        )
        return rel, request, _observations()

    raise ValueError(f"Unknown benchmark setup: {setup}")


def evaluate_case(case: dict) -> dict:
    rel, request, observations = build_case(case["setup"])
    report = diagnose(rel, request, observations=observations).to_dict()
    expected = case["expected"]

    signal_types = {item["signal_type"] for item in report["diagnostic_signals"]}
    unknown_types = {item["unknown_type"] for item in report["unknowns"]}
    governance_outcomes = {item["outcome"] for item in report["governance_findings"]}
    policy_ids = {item["policy_id"] for item in report["governance_findings"]}

    expected_name = expected.get("signal_or_unknown")
    hidden_variable_detected = False
    if expected_name:
        hidden_variable_detected = expected_name in signal_types or expected_name in unknown_types
    if expected.get("governance_outcome"):
        hidden_variable_detected = expected["governance_outcome"] in governance_outcomes
        if expected.get("policy_id"):
            hidden_variable_detected = hidden_variable_detected and expected["policy_id"] in policy_ids

    negative_control = expected["kind"] == "negative_control"
    appropriate_non_detection = (
        negative_control
        and report["summary"] == expected["summary"]
        and not report["diagnostic_signals"]
        and not report["unknowns"]
        and all(item["outcome"] == "ALLOW" for item in report["governance_findings"])
    )

    false_authority_claim = any(
        item.get("governance_effect") != "none" for item in report["diagnostic_signals"]
    )

    return {
        "id": case["id"],
        "family": case["family"],
        "kind": expected["kind"],
        "local_metric_success": bool(case["local_metric_success"]),
        "baseline_hidden_variable_detected": False,
        "hidden_variable_detected": hidden_variable_detected,
        "appropriate_non_detection": appropriate_non_detection,
        "hard_governance_outcome": sorted(outcome for outcome in governance_outcomes if outcome != "ALLOW"),
        "diagnostic_disposition": report["summary"],
        "false_authority_claim": false_authority_claim,
        "expected_summary": expected["summary"],
        "report": report,
    }


def run_suite(cases_path: Path = CASES_PATH) -> dict:
    payload = json.loads(cases_path.read_text())
    results = [evaluate_case(case) for case in payload["cases"]]

    positives = [result for result in results if result["kind"] == "positive_control"]
    negatives = [result for result in results if result["kind"] == "negative_control"]

    positive_hits = sum(result["hidden_variable_detected"] for result in positives)
    negative_restraint = sum(result["appropriate_non_detection"] for result in negatives)
    false_authority_claims = sum(result["false_authority_claim"] for result in results)

    return {
        "schema": "tria.unknown-unknown-results/0.1",
        "suite": payload["schema"],
        "target": payload["target"],
        "aggregate": {
            "cases": len(results),
            "positive_controls": len(positives),
            "positive_controls_detected": positive_hits,
            "positive_control_detection_rate": positive_hits / len(positives) if positives else 0.0,
            "negative_controls": len(negatives),
            "negative_controls_with_appropriate_restraint": negative_restraint,
            "negative_control_restraint_rate": negative_restraint / len(negatives) if negatives else 0.0,
            "false_authority_claims": false_authority_claims,
        },
        "results": results,
        "interpretation": (
            "Synthetic diagnostic evaluation only. Positive-control coverage and negative-control restraint "
            "do not establish empirical model improvement, scientific validity, or production safety."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_suite(), indent=2, sort_keys=True))

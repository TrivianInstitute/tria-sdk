# SPDX-License-Identifier: MPL-2.0
"""Synthetic diagnostic controls, not a model-performance comparison.

Only a setup key enters the fixture builder. Evaluator-only narrative and
expected outcomes are used for scoring after diagnosis, never as SDK inputs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from tria import (
    AttributableObservation, Capability, CapabilityRequirement,
    ConsentRequirement, EpistemicType, InvocationRequest, LifecycleState,
    Tria, __version__, diagnose,
)

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "cases.json"
REPORT_SCHEMA_PATH = ROOT.parents[1] / "schemas/tria-diagnostic-report.v0.1.schema.json"
SETUPS = frozenset({
    "stale_external_authority", "missing_host_authentication", "irreversible_action",
    "contested_claim", "missing_consent", "missing_capability", "purpose_mismatch",
    "clean_unrepresented", "revoked_permission", "revoked_consent",
    "expired_permission", "expired_consent", "permission_conditions",
    "consent_conditions", "resting_lifecycle", "clean_authorized",
    "missing_reversibility", "missing_external_authority",
})


def _validator(path: Path) -> Draft202012Validator:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_payload(payload: dict[str, Any]) -> None:
    _validator(ROOT / "scenario.schema.json").validate(payload)
    ids = [case["id"] for case in payload["cases"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case IDs are not permitted.")
    if payload["target"]["tria_sdk"] != __version__:
        raise ValueError(f"Suite targets {payload['target']['tria_sdk']}; installed SDK is {__version__}.")
    if any(case["setup"] not in SETUPS for case in payload["cases"]):
        raise ValueError("Suite contains an unsupported setup.")


def _observations(*, host_auth=True, authority=True, reversibility=True):
    return tuple(
        AttributableObservation(kind, value, (source,))
        for kind, value, source in (
            ("host_authentication", host_auth, "fixture:host-auth"),
            ("external_authority_current", authority, "fixture:principal-intent"),
            ("reversibility", reversibility, "fixture:action-effects"),
        ) if value is not None
    )


def build_case(setup: str):
    if setup not in SETUPS:
        raise ValueError(f"Unknown challenge setup: {setup!r}")
    rel = Tria().create_relationship(["human:a", "agent:b"])
    expired = datetime(2000, 1, 1, tzinfo=timezone.utc)
    if setup != "missing_capability":
        rel.admin.grant_permission(
            "human:a", "agent:b", "task:primary", Capability.ACT,
            purpose="draft_only" if setup == "purpose_mismatch" else None,
            expires_at=expired if setup == "expired_permission" else None,
            conditions=("approved",) if setup == "permission_conditions" else (),
        )
    if setup == "revoked_permission":
        rel.admin.revoke_permission("human:a", "agent:b", "task:primary", Capability.ACT)

    consent_requirements = ()
    if setup in {"missing_consent", "revoked_consent", "expired_consent", "consent_conditions"}:
        consent_requirements = (ConsentRequirement("human:a", "persistent_context"),)
        if setup != "missing_consent":
            rel.grant_consent(
                "human:a", "persistent_context",
                expires_at=expired if setup == "expired_consent" else None,
                conditions=("approved",) if setup == "consent_conditions" else (),
            )
        if setup == "revoked_consent":
            rel.revoke_consent("human:a", "persistent_context")

    context = ()
    if setup == "contested_claim":
        observed = rel.register_claim(
            "human:a", EpistemicType.OBSERVATION,
            "The participant selected option A.", source_refs=["fixture:selection"],
        )
        interpretation = rel.register_claim(
            "agent:b", EpistemicType.INTERPRETATION,
            "The participant prefers A in future cases.", derived_from=[observed.claim_id],
        )
        rel.dispute_claim("human:a", interpretation.claim_id, "Only for this instance.")
        resource = f"claim:{interpretation.claim_id}"
        rel.admin.grant_permission("human:a", "agent:b", resource, Capability.READ)
        context = (resource,)
    if setup == "resting_lifecycle":
        rel.grant_lifecycle_authority("tria:system", "human:a")
        rel.transition("human:a", LifecycleState.ACTIVE)
        rel.transition("human:a", LifecycleState.RESTING)

    observations = _observations(
        host_auth=None if setup == "missing_host_authentication" else True,
        authority=(False if setup == "stale_external_authority" else
                   None if setup == "missing_external_authority" else True),
        reversibility=(False if setup == "irreversible_action" else
                       None if setup == "missing_reversibility" else True),
    )
    request = InvocationRequest(
        requested_by="agent:b", action="Perform the proposed local action.",
        target="task:primary", context_resources=context,
        requirements=(CapabilityRequirement(
            "task:primary", Capability.ACT,
            purpose="send" if setup == "purpose_mismatch" else None,
        ),),
        consent_requirements=consent_requirements,
    )
    return rel, request, observations


def score_report(report: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    errors = sorted(error.message for error in _validator(REPORT_SCHEMA_PATH).iter_errors(report))
    if errors:
        return {"passed": False, "schema_valid": False, "schema_errors": errors,
                "expected_evidence_found": False, "appropriate_non_detection": False,
                "summary_matches": False, "advisory_authority_violations": None}
    findings = report["governance_findings"]
    signals = report["diagnostic_signals"]
    unknowns = report["unknowns"]
    summary_matches = report["summary"] == expected["summary"]
    channel = expected.get("channel")
    found = False
    if channel == "governance":
        found = any(
            item["outcome"] == expected["governance_outcome"]
            and item["policy_id"] == expected["policy_id"]
            and item["evidence_class"] == "enforced" for item in findings
        )
    elif channel == "signal":
        found = any(
            item["signal_type"] == expected["signal_or_unknown"]
            and item["evidence_class"] == expected["evidence_class"]
            and item["governance_effect"] == "none" for item in signals
        )
    elif channel == "unknown":
        found = any(
            item["unknown_type"] == expected["signal_or_unknown"]
            and item["materiality"] == expected["materiality"] for item in unknowns
        )
    only_allow = bool(findings) and all(item["outcome"] == "ALLOW" for item in findings)
    if channel in {"signal", "unknown"}:
        found = found and only_allow
    negative = expected["kind"] == "negative_control"
    restraint = negative and summary_matches and only_allow and not signals and not unknowns
    violations = sum(item["governance_effect"] != "none" for item in signals)
    matched = restraint if negative else found and summary_matches
    return {
        "passed": bool(matched and violations == 0), "schema_valid": True,
        "schema_errors": [], "summary_matches": summary_matches,
        "expected_evidence_found": found if not negative else None,
        "appropriate_non_detection": bool(restraint) if negative else None,
        "advisory_authority_violations": violations,
    }


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    rel, request, observations = build_case(case["setup"])
    before = tuple(event.event_hash for event in rel.events)
    report = diagnose(rel, request, observations=observations).to_dict()
    history_unchanged = before == tuple(event.event_hash for event in rel.events)
    score = score_report(report, case["expected"])
    score["passed"] = score["passed"] and history_unchanged
    return {
        "id": case["id"], "family": case["family"], "setup": case["setup"],
        "kind": case["expected"]["kind"], "channel": case["expected"].get("channel"),
        "history_unchanged": history_unchanged, **score, "report": report,
    }


def run_suite(cases_path: Path = CASES_PATH) -> dict[str, Any]:
    raw = Path(cases_path).read_bytes()
    payload = json.loads(raw)
    validate_payload(payload)
    results = [evaluate_case(case) for case in payload["cases"]]
    positives = [r for r in results if r["kind"] == "positive_control"]
    negatives = [r for r in results if r["kind"] == "negative_control"]
    hits = sum(r["passed"] for r in positives)
    restraint = sum(r["passed"] for r in negatives)
    return {
        "schema": "tria.unknown-unknown-results/0.1",
        "suite": payload["schema"], "evaluation_type": "synthetic_diagnostic_controls",
        "target": payload["target"],
        "provenance": {
            "actual_sdk": __version__, "python": platform.python_version(),
            "cases_sha256": hashlib.sha256(raw).hexdigest(),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "model_comparison": {
            "status": "not_run", "baseline_results": None,
            "tria_mediated_model_results": None, "task_success": None,
        },
        "aggregate": {
            "cases": len(results), "distinct_setups": len({r["setup"] for r in results}),
            "cases_passed": sum(r["passed"] for r in results),
            "cases_failed": sum(not r["passed"] for r in results),
            "positive_controls": len(positives), "positive_controls_matched": hits,
            "positive_control_match_rate": hits / len(positives) if positives else None,
            "negative_controls": len(negatives), "negative_controls_with_restraint": restraint,
            "negative_control_restraint_rate": restraint / len(negatives) if negatives else None,
            "schema_invalid_reports": sum(not r["schema_valid"] for r in results),
            "history_mutations": sum(not r["history_unchanged"] for r in results),
        },
        "results": results,
        "interpretation": (
            "Synthetic controls only, not an independent or held-out benchmark. An unknown "
            "identifies missing evidence, not the hidden fact. Clear is not proof of safety. "
            "No model baseline, task-success improvement, or real-world risk reduction was measured."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--summary", action="store_true", help="Omit individual reports from stdout.")
    parser.add_argument("--output", type=Path, help="Save full results to a NEW JSON file; existing files are not overwritten.")
    args = parser.parse_args(argv)
    try:
        result = run_suite(args.cases)
        if args.output:
            with args.output.open("x", encoding="utf-8") as handle:
                json.dump(result, handle, indent=2, sort_keys=True)
                handle.write("\n")
        shown = {k: v for k, v in result.items() if k != "results"} if args.summary else result
        print(json.dumps(shown, indent=2, sort_keys=True))
        return 1 if result["aggregate"]["cases_failed"] else 0
    except (OSError, ValueError, ValidationError) as exc:
        print(f"Challenge failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

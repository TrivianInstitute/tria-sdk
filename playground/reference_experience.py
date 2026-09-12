"""Synthetic scheduling reference experience; no model, network or calendar calls.

Run: python playground/reference_experience.py --output reference-results.json
SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter_ns

import tria as sdk
from tria import (
    Capability, CapabilityRequirement, ConsentRequirement, EpistemicType,
    ExecutionBridge, InvocationRequest, OpenAIResponsesAdapter, SQLiteEventStore,
    Tria, diagnose,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "tria.scheduling-reference/0.1"
STEPS = (
    ("authorized", "Consent and READ permission are active", True, True),
    ("consent_revoked", "Withdraw consent to use the preference", False, True),
    ("consent_restored", "Renew consent", True, True),
    ("permission_revoked", "Withdraw the assistant's READ permission", True, False),
    ("permission_restored", "Restore READ permission", True, True),
)


def provenance():
    def git(*args):
        try:
            return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL,
                                           text=True, timeout=3).strip()
        except (OSError, subprocess.SubprocessError):
            return None
    sdk_root = Path(sdk.__file__).resolve().parent
    digest = hashlib.sha256()
    for path in sorted(sdk_root.rglob("*.py")):
        digest.update(path.relative_to(sdk_root).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    status = git("status", "--porcelain", "--untracked-files=normal")
    return {"sdk_version": sdk.__version__, "python_version": platform.python_version(),
            "commit": git("rev-parse", "HEAD"), "working_tree_dirty": None if status is None else bool(status),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "sdk_source_sha256": digest.hexdigest()}


def run_reference():
    """Run a fresh five-step synthetic application and return an explicit safe projection."""
    calls = {"cached_payload_baseline": [], "tria": []}
    rows = []
    with TemporaryDirectory(prefix="tria-reference-") as directory:
        database = Path(directory) / "reference.sqlite"
        with SQLiteEventStore(database) as store:
            rel = Tria(store).create_relationship(["human:user", "agent:assistant"])
            preference = rel.register_claim("human:user", EpistemicType.OBSERVATION,
                "I prefer meetings after 10 AM.", source_refs=["reference:synthetic-preference"])
            resource = f"claim:{preference.claim_id}"
            rel.grant_consent("human:user", "persistent_context", purpose="scheduling")
            rel.admin.grant_permission("human:user", "agent:assistant", resource,
                                       Capability.READ, purpose="scheduling")
            bridge = ExecutionBridge()
            adapter = OpenAIResponsesAdapter()

            def request():
                return InvocationRequest(requested_by="agent:assistant", action="Suggest a meeting time.",
                    target="reference-local", context_resources=(resource,),
                    requirements=(CapabilityRequirement(resource, Capability.READ, purpose="scheduling"),),
                    consent_requirements=(ConsentRequirement("human:user", "persistent_context", purpose="scheduling"),))

            def executor(condition):
                def execute(wire):
                    text = wire.payload["input"][0]["content"][0]["text"]
                    if "I prefer meetings after 10 AM." not in text:
                        raise ValueError("Expected synthetic preference was not delivered.")
                    calls[condition].append("10:30 AM")
                    return {"id": "reference:local-suggestion", "status": "completed"}
                return execute

            # Deliberately ungated comparator: cache an initially authorized payload,
            # then reuse it without checking current consent or permission. This models
            # one specific failure pattern, not ordinary AI systems in general.
            cached = bridge.prepare(rel, request(), adapter, model="local-mock").provider_request
            for step_id, title, consent, permission in STEPS:
                if step_id == "consent_revoked":
                    rel.revoke_consent("human:user", "persistent_context")
                elif step_id == "consent_restored":
                    rel.grant_consent("human:user", "persistent_context", purpose="scheduling")
                elif step_id == "permission_revoked":
                    rel.admin.revoke_permission("human:user", "agent:assistant", resource, Capability.READ)
                elif step_id == "permission_restored":
                    rel.admin.grant_permission("human:user", "agent:assistant", resource, Capability.READ, purpose="scheduling")
                invocation = request()
                diagnostic = diagnose(rel, invocation).to_dict()
                baseline_prior = len(calls["cached_payload_baseline"])
                start = perf_counter_ns()
                executor("cached_payload_baseline")(cached)
                baseline_ns = perf_counter_ns() - start
                prior_calls = len(calls["tria"])
                start = perf_counter_ns()
                receipt = bridge.execute(rel, invocation, adapter, executor("tria"), model="local-mock")
                tria_ns = perf_counter_ns() - start
                rows.append({"id": step_id, "title": title,
                    "state": {"consent": consent, "permission": permission},
                    "cached_payload_baseline": {"executor_calls": len(calls["cached_payload_baseline"])-baseline_prior, "suggestion": calls["cached_payload_baseline"][-1], "elapsed_ns": baseline_ns},
                    "tria": {"executed": receipt.executed, "executor_calls": len(calls["tria"])-prior_calls,
                        "outcome": receipt.plan.outcome.value, "reason": receipt.plan.reason,
                        "suggestion": calls["tria"][-1] if len(calls["tria"]) > prior_calls else None,
                        "elapsed_ns": tria_ns},
                    "inspection": {"summary": diagnostic["summary"],
                        "unknowns": [{"type": u["unknown_type"], "reason": u["reason"]} for u in diagnostic["unknowns"]]},
                    "event_count": len(rel.events)})
            events = [{"position": i+1, "type": e.event_type, "actor": e.actor_id,
                       "actor_sequence": e.actor_sequence} for i,e in enumerate(rel.events)]
            audit = rel.audit()
            relationship_id = rel.relationship_id
            original_events = tuple(rel.events)
        with SQLiteEventStore(database) as store:
            reopened = Tria(store).load_relationship(relationship_id)
            persistence = {"history_equal_after_reopen": tuple(reopened.events) == original_events,
                "audit_equal_after_reopen": reopened.audit() == audit}
    checks = {
        "governed_execution_matches_declared_state": all(r["tria"]["executed"] == (r["state"]["consent"] and r["state"]["permission"]) for r in rows),
        "blocked_attempts_never_enter_executor": all(r["tria"]["executor_calls"] == 0 for r in rows if not (r["state"]["consent"] and r["state"]["permission"])),
        "authorized_attempts_enter_once": all(r["tria"]["executor_calls"] == 1 for r in rows if r["state"]["consent"] and r["state"]["permission"]),
        "cached_baseline_runs_each_time": len(calls["cached_payload_baseline"]) == len(STEPS),
        "history_chain_valid": bool(audit["chain_valid"]),
        "relationship_valid": bool(audit["relationship_valid"]), **persistence}
    return {"schema": PROTOCOL, "execution_mode": "sdk-backed-local", "synthetic_data": True,
        "generated_at": datetime.now(timezone.utc).isoformat(), "provenance": provenance(),
        "comparison": "An intentionally ungated cached-payload comparator and TRIA use the same local suggestion function. This is not a model-quality comparison.",
        "timing_scope": "Single local elapsed samples: baseline executor only versus full SDK execute including SQLite recording and executor. Diagnosis, setup and reopen excluded. No stable latency or overhead estimate is claimed.",
        "steps": rows, "events": events, "checks": checks, "passed": all(checks.values()),
        "limits": ["Synthetic authored scenario; independent reproduction pending.",
            "No model, calendar, messaging or other external action runs.",
            "Export contains synthetic result projections, not a replay bundle or authorization token.",
            "The host supplies identities and requirements. Diagnostic unknowns are not automatically enforced.",
            "This run does not establish human benefit, production safety or general model improvement."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Save a new JSON file; never overwrite existing evidence.")
    args = parser.parse_args(argv)
    if args.output and args.output.exists():
        parser.error("Output already exists; choose a new filename.")
    report = run_reference()
    encoded = json.dumps(report, indent=2)
    if args.output:
        with args.output.open("x", encoding="utf-8") as output:
            output.write(encoded + "\n")
    print(encoded)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

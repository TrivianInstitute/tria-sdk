"""SDK-backed scenarios for TRIA Playground.

Run from an editable tria-sdk checkout:
    python playground/sdk_scenarios.py consent
    python playground/sdk_scenarios.py reality
    python playground/sdk_scenarios.py action

This module deliberately uses the public TRIA API. It is a local demonstration
runner, not a network service or authentication boundary.
"""
from __future__ import annotations

import argparse
import json

from tria import (
    Capability,
    CapabilityRequirement,
    ConsentRequirement,
    EpistemicType,
    ExecutionBridge,
    InvocationRequest,
    OpenAIResponsesAdapter,
    Tria,
)


def _events(rel):
    return [
        {
            "type": event.event_type,
            "actor": event.actor_id,
            "sequence": event.actor_sequence,
        }
        for event in rel.events
    ]


def consent_and_revocation(revoke: str = "consent") -> dict:
    rel = Tria().create_relationship(["human:user", "agent:assistant"])
    claim = rel.register_claim(
        "human:user",
        EpistemicType.OBSERVATION,
        "I prefer meetings after 10 AM.",
        source_refs=["playground:user-preference"],
    )
    resource = f"claim:{claim.claim_id}"
    rel.grant_consent("human:user", "persistent_context", purpose="scheduling")
    rel.admin.grant_permission(
        "human:user", "agent:assistant", resource, Capability.READ, purpose="scheduling"
    )

    request = InvocationRequest(
        requested_by="agent:assistant",
        action="Read the scheduling preference.",
        target="playground-local",
        context_resources=(resource,),
        requirements=(
            CapabilityRequirement(resource, Capability.READ, purpose="scheduling"),
        ),
        consent_requirements=(
            ConsentRequirement("human:user", "persistent_context", purpose="scheduling"),
        ),
    )
    bridge = ExecutionBridge()

    def executor(_provider_request):
        return {"id": "playground:local-result", "status": "completed"}

    before = bridge.execute(
        rel, request, OpenAIResponsesAdapter(), executor, model="playground-local"
    )
    if revoke == "permission":
        rel.admin.revoke_permission(
            "human:user", "agent:assistant", resource, Capability.READ
        )
    else:
        rel.revoke_consent("human:user", "persistent_context")

    after_request = InvocationRequest(
        requested_by="agent:assistant",
        action="Read the scheduling preference after revocation.",
        target="playground-local",
        context_resources=(resource,),
        requirements=(
            CapabilityRequirement(resource, Capability.READ, purpose="scheduling"),
        ),
        consent_requirements=(
            ConsentRequirement("human:user", "persistent_context", purpose="scheduling"),
        ),
    )
    after = bridge.execute(
        rel, after_request, OpenAIResponsesAdapter(), executor, model="playground-local"
    )
    return {
        "scenario": "consent",
        "before": {"executed": before.executed, "reason": before.plan.reason},
        "after": {"executed": after.executed, "reason": after.plan.reason},
        "revoked": revoke,
        "audit": rel.audit(),
        "events": _events(rel),
    }


def contested_reality() -> dict:
    rel = Tria().create_relationship(["human:user", "agent:assistant"])
    observation = rel.register_claim(
        "agent:assistant",
        EpistemicType.OBSERVATION,
        "Response latency increased by 1.7 seconds.",
        source_refs=["playground:sensor-latency"],
    )
    interpretation = rel.register_claim(
        "agent:assistant",
        EpistemicType.INTERPRETATION,
        "Participant may be disengaged.",
        derived_from=[observation.claim_id],
    )
    rel.dispute_claim(
        "human:user", interpretation.claim_id, "I was concentrating."
    )
    state = rel.state
    return {
        "scenario": "reality",
        "observation_id": observation.claim_id,
        "interpretation_id": interpretation.claim_id,
        "interpretation_status": state.claims[interpretation.claim_id].status.value,
        "audit": rel.audit(),
        "events": _events(rel),
    }


def agentic_action(revoke: str = "permission") -> dict:
    rel = Tria().create_relationship(["human:user", "agent:assistant"])
    resource = "action:calendar:schedule"
    rel.grant_consent("human:user", "agent_action", purpose="scheduling")
    rel.admin.grant_permission(
        "human:user", "agent:assistant", resource, Capability.ACT, purpose="scheduling"
    )
    bridge = ExecutionBridge()
    calls = []

    def attempt(label):
        request = InvocationRequest(
            requested_by="agent:assistant",
            action=label,
            target="playground-calendar",
            requirements=(
                CapabilityRequirement(resource, Capability.ACT, purpose="scheduling"),
            ),
            consent_requirements=(
                ConsentRequirement("human:user", "agent_action", purpose="scheduling"),
            ),
        )
        return bridge.execute(
            rel,
            request,
            OpenAIResponsesAdapter(),
            lambda _wire: calls.append(label) or {"id": "playground:scheduled", "status": "completed"},
            model="playground-local",
        )

    before = attempt("Schedule a meeting.")
    if revoke == "consent":
        rel.revoke_consent("human:user", "agent_action")
    else:
        rel.admin.revoke_permission(
            "human:user", "agent:assistant", resource, Capability.ACT
        )
    after = attempt("Schedule a meeting after revocation.")
    return {
        "scenario": "action",
        "before": {"executed": before.executed, "reason": before.plan.reason},
        "after": {"executed": after.executed, "reason": after.plan.reason},
        "executor_calls": len(calls),
        "revoked": revoke,
        "audit": rel.audit(),
        "events": _events(rel),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", choices=("consent", "reality", "action"))
    parser.add_argument("--revoke", choices=("consent", "permission"), default=None)
    args = parser.parse_args()
    if args.scenario == "consent":
        result = consent_and_revocation(args.revoke or "consent")
    elif args.scenario == "reality":
        result = contested_reality()
    else:
        result = agentic_action(args.revoke or "permission")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()

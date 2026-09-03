from tria import (
    GovernanceDecision,
    GovernanceEngine,
    GovernanceOutcome,
    InMemoryEventStore,
    InvocationRequest,
    LifecycleState,
    Relationship,
    Runtime,
    Tria,
)


class BlockingRuntimeGovernance(GovernanceEngine):
    def require_runtime_execution(self, state):
        return GovernanceDecision(
            GovernanceOutcome.BLOCK,
            "test.runtime.injected",
            "1",
            "Injected governance blocks runtime execution.",
        )


def test_runtime_uses_relationship_governance_engine():
    rel = Relationship("relationship:custom", InMemoryEventStore(), governance=BlockingRuntimeGovernance())
    rel._commit("RelationshipCreated", "tria:system", {"participants": ["human:a", "agent:b"]})

    plan = Runtime().prepare(
        rel,
        InvocationRequest(requested_by="agent:b", action="continue", target="executor:any"),
    )

    assert plan.outcome is GovernanceOutcome.BLOCK
    assert plan.decisions[0].policy_id == "test.runtime.injected"
    resolutions = [event for event in rel.events if event.event_type == "InvocationResolved"]
    assert resolutions[-1].payload["status"] == "BLOCKED"


def test_resting_runtime_records_paused_not_blocked():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_lifecycle_authority("tria:system", "human:a")
    rel.transition("human:a", LifecycleState.ACTIVE)
    rel.transition("human:a", LifecycleState.RESTING)

    plan = Runtime().prepare(
        rel,
        InvocationRequest(requested_by="agent:b", action="continue", target="executor:any"),
    )

    assert plan.outcome is GovernanceOutcome.PAUSE
    resolutions = [event for event in rel.events if event.event_type == "InvocationResolved"]
    assert resolutions[-1].payload["status"] == "PAUSED"


def test_dissolved_runtime_records_blocked():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_lifecycle_authority("tria:system", "human:a")
    rel.transition("human:a", LifecycleState.DISSOLVING)
    rel.transition("human:a", LifecycleState.DISSOLVED)

    plan = Runtime().prepare(
        rel,
        InvocationRequest(requested_by="agent:b", action="continue", target="executor:any"),
    )

    assert plan.outcome is GovernanceOutcome.BLOCK
    resolutions = [event for event in rel.events if event.event_type == "InvocationResolved"]
    assert resolutions[-1].payload["status"] == "BLOCKED"

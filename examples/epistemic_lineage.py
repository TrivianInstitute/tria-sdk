from tria import EpistemicType, Tria

tria = Tria()
rel = tria.create_relationship(["human:alice", "agent:demo"])

observation = rel.register_claim(
    actor="agent:demo",
    epistemic_type=EpistemicType.OBSERVATION,
    content="Response latency increased by 1.7 seconds.",
    source_refs=["sensor:latency:evt-001"],
)

interpretation = rel.register_claim(
    actor="agent:demo",
    epistemic_type=EpistemicType.INTERPRETATION,
    content="Participant may be disengaged.",
    derived_from=[observation.claim_id],
)

rel.dispute_claim("human:alice", interpretation.claim_id, "I was concentrating.")
print(rel.state.claims)

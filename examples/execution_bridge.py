from tria import (
    Capability,
    EpistemicType,
    ExecutionBridge,
    InvocationRequest,
    OpenAIResponsesAdapter,
    Tria,
)

tria = Tria()
relationship = tria.create_relationship(["human:alice", "agent:assistant"])

observation = relationship.register_claim(
    "agent:assistant",
    EpistemicType.OBSERVATION,
    "Response latency increased.",
    source_refs=["sensor:latency"],
)
resource = f"claim:{observation.claim_id}"
relationship.grant_permission("human:alice", "agent:assistant", resource, Capability.READ)

request = InvocationRequest(
    requested_by="agent:assistant",
    action="Assess this observation without treating it as a conclusion.",
    target="model",
    context_resources=(resource,),
)

bridge = ExecutionBridge()
prepared = bridge.prepare(
    relationship,
    request,
    OpenAIResponsesAdapter(),
    model="your-model",
)

if prepared.plan.allowed:
    # Application-owned network execution belongs here.
    print(prepared.provider_request.payload)
else:
    print(prepared.plan.reason)

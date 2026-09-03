# TRIA SDK

**TRIA SDK** is a model-agnostic governance kernel and execution boundary for persistent mediated relationships.

It treats consequential relational state as explicit, attributable, contestable, revisable, and auditable across time. TRIA Core does not require an AI model and makes no claim about consciousness, sentience, or phenomenological equivalence.

## Architectural invariant

```text
Events are immutable.
State is derived.
Meaning never overwrites occurrence.
```

A relationship is the developer-facing aggregate over an immutable event history:

```text
R_t = reduce(E_0 ... E_t)
```

## What the alpha includes

The current alpha implements:

- immutable relational events with tamper-evident hash chains;
- actor-local ordering and causal parents;
- deterministic state projection and SQLite persistence;
- scoped consent grants and revocations;
- epistemic claims with provenance and preserved disagreement;
- governed capabilities: `STORE`, `READ`, `DISCLOSE`, `DERIVE`, `ACT`, `DELEGATE`;
- policy adoption/revocation and auditable governance decisions;
- model-agnostic invocation planning and governed context filtering;
- thin OpenAI Responses-style and Anthropic Messages-style request translators;
- caller-owned execution through `ExecutionBridge`;
- portable replay bundles with integrity-gated restore;
- explicit compatibility gates for bundle format, event schema, and projection version;
- portable conformance fixtures and tests.

TRIA does **not** own API credentials, network transport, retries, provider SDK clients, RAG, vector memory, agent orchestration, biometrics, dashboards, or metaphysical claims.

## Core example

```python
from tria import Tria, EpistemicType

tria = Tria()
rel = tria.create_relationship(["human:sarasha", "agent:demo"])

rel.grant_consent("human:sarasha", scope="persistent_context")
obs = rel.register_claim(
    actor="agent:demo",
    epistemic_type=EpistemicType.OBSERVATION,
    content="Response latency increased.",
    source_refs=["sensor:latency"],
)
interp = rel.register_claim(
    actor="agent:demo",
    epistemic_type=EpistemicType.INTERPRETATION,
    content="Participant may be disengaged.",
    derived_from=[obs.claim_id],
)
rel.dispute_claim("human:sarasha", interp.claim_id, "I was concentrating.")

print(rel.state)
print(rel.audit())
```

## Governed execution

TRIA can prepare an invocation, filter context according to relationship permissions, translate it for a provider, and hand it to a caller-owned executor. A blocked plan never reaches the executor.

```python
from tria import (
    Capability,
    ExecutionBridge,
    InvocationRequest,
    OpenAIResponsesAdapter,
    Runtime,
    Tria,
)

tria = Tria()
rel = tria.create_relationship(["human:user", "agent:demo"])
rel.grant_permission("human:user", "agent:demo", "context:profile", Capability.READ)

bridge = ExecutionBridge(Runtime())
request = InvocationRequest(
    requested_by="agent:demo",
    action="Help with the current task.",
    target="model",
)

receipt = bridge.prepare(rel, request, OpenAIResponsesAdapter(), model="example-model")
print(receipt.provider_request)
```

Adapters perform translation only. Applications remain responsible for actual network execution and credentials.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
python -m build
```

## Status

`0.1.0a3` is an experimental alpha intended for falsification, integration testing, interoperability testing, and architectural hardening. Passing tests establish encoded behavior only, not scientific validation, legitimate consent, legal compliance, or deployment safety.

The canonical architectural baseline is in [`docs/TRIA_CORE_SPEC_v0.1.1.md`](docs/TRIA_CORE_SPEC_v0.1.1.md).

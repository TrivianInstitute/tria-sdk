# TRIA SDK

**TRIA SDK** is a model-agnostic governance kernel and execution boundary for persistent mediated relationships.

It treats consequential relational state as explicit, attributable, contestable, revisable, governed, and auditable across time. TRIA Core does not require an AI model and makes no claim about consciousness, sentience, personhood, or phenomenological equivalence.

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

The relationship behaves like an object, but never like mutable storage.

## What the alpha includes

The current alpha implements:

- deeply immutable relational events with tamper-evident hash chains;
- actor-local ordering, causal parents, and fail-closed ambiguous permission races;
- deterministic state projection and SQLite persistence;
- scoped, attributable, revocable consent;
- purpose-bound, time-bounded, and explicitly conditioned consent and permissions;
- separate governed capabilities: `STORE`, `READ`, `DISCLOSE`, `DERIVE`, `ACT`, `DELEGATE`;
- explicit delegation authority;
- governed lifecycle authority and a fail-closed lifecycle transition graph;
- policy authority, policy adoption/revocation, and re-consent semantics;
- epistemic claims with provenance and preserved disagreement;
- pure governance evaluation with explicit audit recording for consequential operations;
- governed cross-boundary disclosure, admission, and derivation as distinct operations;
- model-agnostic invocation planning and governed context filtering;
- lifecycle-aware runtime authorization with distinct `PAUSED` and `BLOCKED` outcomes;
- thin OpenAI Responses-style and Anthropic Messages-style request translators;
- caller-owned execution through `ExecutionBridge`;
- portable replay bundles with structural verification and integrity-gated restore;
- full replay export governed by explicit `DISCLOSE` authority;
- explicit compatibility gates for bundle format, event schema, and projection version;
- portable schemas, conformance fixtures, and release-readiness tests.

TRIA does **not** own API credentials, network transport, retries, provider SDK clients, RAG, vector memory, agent orchestration, federation, biometrics, dashboards, or metaphysical claims.

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

TRIA can prepare an invocation, filter context according to relationship permissions, translate it for a provider, and hand it to a caller-owned executor. A blocked or paused plan never reaches the executor.

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

## Governed portable export

A full replay bundle can contain claim contents and relational history, so export is a `DISCLOSE` operation rather than an unrestricted serialization helper.

```python
from tria import Capability, Tria, export_replay_bundle, replay_export_resource

tria = Tria()
rel = tria.create_relationship(["human:user", "agent:demo"])

resource = replay_export_resource(rel.relationship_id)
rel.grant_permission("human:user", "human:user", resource, Capability.DISCLOSE)

bundle = export_replay_bundle(rel, actor="human:user")
print(bundle.to_json())
```

`READ` does not substitute for `DISCLOSE`. Purpose, expiry, conditions, lifecycle restrictions, revocation, and causal ambiguity remain governed by the ordinary capability path.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
python -m build
```

## Compatibility surface

The current alpha compatibility envelope is:

- package: `0.1.0a3`
- event schema: `0.1`
- projection: `0.4`
- replay bundle: `0.1`
- Core specification: `0.1.1`

## Status

`0.1.0a3` is an experimental alpha intended for falsification, integration testing, interoperability testing, and architectural hardening. Passing tests establish encoded behavior only, not scientific validation, legitimate consent, legal compliance, or deployment safety.

The canonical architectural baseline is in [`docs/TRIA_CORE_SPEC_v0.1.1.md`](docs/TRIA_CORE_SPEC_v0.1.1.md). The current implementation-completion audit is in [`docs/TRIA_V0.1_COMPLETION_AUDIT.md`](docs/TRIA_V0.1_COMPLETION_AUDIT.md).

---

## License

TRIA SDK is **source-available for noncommercial use** under the **PolyForm Noncommercial License 1.0.0**. Research, education, experimentation, personal use, and qualifying noncommercial organizational use are permitted subject to that license.

**Commercial use is not permitted under the noncommercial license.** Any commercial use, commercial deployment, incorporation into a commercial product or service, or use on behalf of a for-profit business requires a separate written commercial license from **Trivian Institute**.

See [`LICENSE.md`](LICENSE.md) for the controlling license notice and commercial-use reservation.

Copyright © 2026 Trivian Institute.

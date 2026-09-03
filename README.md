# TRIA SDK

**TRIA SDK** is a model-agnostic governance kernel for persistent mediated relationships.

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

## v0.1 kernel

The initial kernel implements:

- immutable relational events;
- actor-local ordering and causal parents;
- deterministic state projection;
- scoped consent grants and revocations;
- epistemic claims with provenance;
- preserved disagreement;
- deterministic governance decisions;
- explicit access capabilities: STORE, READ, DISCLOSE, DERIVE, ACT, DELEGATE;
- pluggable event-store boundary with an in-memory reference store;
- tamper-evident event hashing performed by Core.

It deliberately does **not** include model-provider adapters, RAG, vector memory, agent orchestration, biometrics, dashboards, or metaphysical claims.

## Example

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
rel.revoke_consent("human:sarasha", scope="persistent_context")

print(rel.state)
print(rel.audit())
```

## Development

```bash
python -m pip install -e '.[dev]'
pytest
```

## Status

`0.1.0a1` is an experimental alpha kernel intended for falsification and architectural hardening. Passing tests establish encoded behavior only, not scientific validation, legitimate consent, legal compliance, or deployment safety.

The canonical architectural baseline is in [`docs/TRIA_CORE_SPEC_v0.1.1.md`](docs/TRIA_CORE_SPEC_v0.1.1.md).

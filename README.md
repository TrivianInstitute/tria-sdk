# TRIA SDK

**TRIA SDK** is a model-agnostic governance kernel and execution boundary for persistent mediated relationships.

It treats consequential relational state as explicit, attributable, contestable, revisable, governed, and auditable across time. TRIA Core does not require an AI model and makes no claim about consciousness, sentience, personhood, or phenomenological equivalence.

## Build something real

Start with the [Quickstart](docs/quickstart.md) and the
[complete no-network governed assistant](docs/complete-governed-application.md).
It creates two participants, grants both consent and permission, executes once,
revokes each independently, proves subsequent attempts are blocked, and reopens
its SQLite history. No research-paper reading or provider credentials are needed.

The safest entry point is `Tria` / `Relationship` with `ExecutionBridge.execute`.
Use lower-level components only after reading the
[modularity and trusted-host contract](docs/modularity-and-trust.md).
TRIA checks the requirements your host declares; your host authenticates actors,
controls administrative access, supplies external data, and owns network effects.

## Deploy / integrate TRIA

For developers who want to use TRIA rather than study the underlying research repositories, **this SDK is the canonical implementation entry point**.

Requirements: Python 3.11+ and Git. CI targets 3.11/3.12. File-backed SQLite currently requires POSIX process locks; see [Persistence](docs/persistence.md).

```bash
git clone https://github.com/TrivianInstitute/tria-sdk.git
cd tria-sdk
python -m venv .venv
```

Activate with `source .venv/bin/activate` on POSIX, or `.venv\Scripts\Activate.ps1` in PowerShell, then install and verify:

```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest -q
```

A successful test run verifies the encoded v0.1 alpha behavior. Applications can then import `tria` directly:

```python
from tria import Tria

tria = Tria()
relationship = tria.create_relationship(["human:user", "agent:demo"])
print(relationship.state)
```

TRIA does **not** own model credentials or network transport. To connect a model, use the Runtime / adapter / `ExecutionBridge` boundary shown below and provide your own executor or provider client.

The other Trivian Institute repositories remain the canonical research, theory, measurement, governance, and reference-implementation sources behind the SDK. They do not all need to be installed in order to use `tria-sdk`.

## Developer path

[Quickstart](docs/quickstart.md) → [Complete governed application](docs/complete-governed-application.md)
→ [Concept/operation glossary](docs/glossary.md) → [Execution boundary](docs/execution-bridge.md)
→ [Persistence](docs/persistence.md) → [Modularity and trust](docs/modularity-and-trust.md)
→ [API reference](docs/api-reference.md).

External data and transport: [Resource resolution](docs/resource-resolution.md) and
[Provider payload conversion](docs/provider-adapters.md). The repository is
`tria-sdk`, its distribution is `tria-core`, and its import is `tria`.

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
from tria import (Tria, EpistemicType, Capability, CapabilityRequirement,
                  ConsentRequirement, InvocationRequest, ExecutionBridge,
                  OpenAIResponsesAdapter)

rel = Tria().create_relationship(["human:user", "agent:demo"])
claim = rel.register_claim("human:user", EpistemicType.OBSERVATION,
                           "Meetings after 10 AM.", source_refs=["user:preference"])
resource = f"claim:{claim.claim_id}"
rel.grant_consent("human:user", "persistent_context")
rel.admin.grant_permission("human:user", "agent:demo", resource, Capability.READ)
request = InvocationRequest(
    requested_by="agent:demo", action="Read the scheduling preference.", target="local",
    context_resources=(resource,),
    requirements=(CapabilityRequirement(resource, Capability.READ),),
    consent_requirements=(ConsentRequirement("human:user", "persistent_context"),),
)
receipt = ExecutionBridge().execute(
    rel, request, OpenAIResponsesAdapter(),
    lambda wire: {"id": "local:result", "status": "completed"}, model="local-mock",
)
assert receipt.executed
print(receipt.result.status)
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

- package: `0.1.0a4`
- event schema: `0.2`
- projection: `0.5`
- replay bundle: `0.1`
- Core specification: `0.1.2`

## Status

`0.1.0a4` is an experimental remediation alpha intended for falsification, integration testing, interoperability testing, and architectural hardening. It is deployable as a software dependency or integration boundary, but it is **not** represented as a production-certified safety system or empirically validated theory. Passing tests establish encoded behavior only, not scientific validation, legitimate consent, legal compliance, or deployment safety.

The current operational contract is [specification 0.1.2](docs/TRIA_OPERATIONAL_SPEC_v0.1.2.md). See [compatibility](docs/compatibility.md) before opening old data. The pre-remediation audit applies only to 0.1.0a3 at `463ce26b8af7d52d38796888cf5717948df1e331`; its NOT YET result remains historical evidence. No production readiness is implied by this prerelease.

## Fund the Public Infrastructure

Help maintain public relational-governance infrastructure for increasingly persistent AI systems.

Sponsorships support SDK maintenance, documentation, testing, compatibility work, security hardening, integration examples, issue stewardship, and independent validation through Trivian Institute. Sponsorship does not grant commercial-use rights or influence research findings.

[**Sponsor Trivian Institute through GitHub Sponsors**](https://github.com/sponsors/TrivianInstitute) · [Review the funding policy and tiers](https://github.com/TrivianInstitute/.github/blob/main/FUNDING.md)

---

## License

TRIA SDK is **source-available for noncommercial use** under the **PolyForm Noncommercial License 1.0.0**. Research, education, experimentation, personal use, and qualifying noncommercial organizational use are permitted subject to that license.

**Commercial use is not permitted under the noncommercial license.** Any commercial use, commercial deployment, incorporation into a commercial product or service, or use on behalf of a for-profit business requires a separate written commercial license from **Trivian Institute**.

See [`LICENSE.md`](LICENSE.md) for the controlling license notice and commercial-use reservation.

Copyright © 2026 Trivian Institute.

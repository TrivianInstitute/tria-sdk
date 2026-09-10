# TRIA SDK

**TRIA SDK** is a model-agnostic governance kernel and execution boundary for persistent mediated relationships.

It treats consequential relational state as explicit, attributable, contestable, revisable, governed, and auditable across time. TRIA SDK does not require an AI model and makes no claim about consciousness, sentience, personhood, or phenomenological equivalence.

## Build something real

Start with the [Quickstart](docs/quickstart.md) and the
[complete no-network governed assistant](docs/complete-governed-application.md).
It creates two participants, grants both consent and permission, executes once,
revokes each independently, proves subsequent attempts are blocked, and reopens
its SQLite history. No research-paper reading or provider credentials are needed.

The safest execution entry point is `Tria` / `Relationship` with `ExecutionBridge.execute`.
For read-only inspection of a proposed action, use `diagnose`. Use lower-level
components only after reading the [modularity and trusted-host contract](docs/modularity-and-trust.md).
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

A successful test run verifies the encoded alpha behavior. Applications can then import `tria` directly:

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
→ [Concept/operation glossary](docs/glossary.md) → [Diagnostic interface](docs/TRIA_DIAGNOSTIC_INTERFACE_v0.1.md)
→ [Execution boundary](docs/execution-bridge.md) → [Persistence](docs/persistence.md)
→ [Modularity and trust](docs/modularity-and-trust.md) → [API reference](docs/api-reference.md).

External data and transport: [Resource resolution](docs/resource-resolution.md) and
[Provider payload conversion](docs/provider-adapters.md). The repository and Python distribution are both
`tria-sdk`; the import package remains `tria`.

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
- portable schemas, conformance fixtures, and release-readiness tests;
- a read-only `diagnose` surface that separates enforced governance findings, advisory/derived signals, explicit unknowns, suggested checks, and provenance.

TRIA does **not** own API credentials, network transport, retries, provider SDK clients, RAG, vector memory, agent orchestration, federation, biometrics, dashboards, or metaphysical claims.

## SDK example

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

## Read-only diagnostics

`diagnose` lets a host inspect a proposed `InvocationRequest` before execution without mutating the relationship or creating new authority.

```python
from tria import (
    AttributableObservation,
    Capability,
    InvocationRequest,
    diagnose,
)

resource = f"claim:{obs.claim_id}"
rel.admin.grant_permission("human:sarasha", "agent:demo", resource, Capability.READ)

request = InvocationRequest(
    requested_by="agent:demo",
    action="Use the observation.",
    target="local",
    context_resources=(resource,),
)

report = diagnose(
    rel,
    request,
    observations=(
        AttributableObservation("host_authentication", True, ("host:auth:1",)),
        AttributableObservation("external_authority_current", True, ("host:intent:1",)),
        AttributableObservation("reversibility", True, ("host:recovery:1",)),
    ),
)
print(report.to_dict())
```

The report is descriptive. `clear` is **not** an execution authorization token. Missing host evidence is surfaced as unknown rather than guessed, and final execution must still pass the ordinary Runtime / `ExecutionBridge` checks. See the [Diagnostic Interface v0.1](docs/TRIA_DIAGNOSTIC_INTERFACE_v0.1.md).

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

- package: `0.1.0a5`
- event schema: `0.2`
- projection: `0.5`
- replay bundle: `0.1`
- Core operational specification: `0.1.2`
- Diagnostic Interface: `0.1`

The diagnostic interface changes no event, projection, replay, or enforcement semantics.

## Adversarial validation

TRIA maintains a frozen adversarial validation history. Claims are challenged with executable counterexamples; failures are preserved as historical evidence; remediations are rerun against the original witnesses; and unresolved properties remain explicitly marked rather than inferred as solved.

The `0.1.0a3` clean-room audit returned **NOT YET**. After remediation, the `0.1.0a4` candidate earned **YES, WITH FRICTION** for independent developer adoption. These results establish tested behavior under the audited conditions, not production certification, security certification, legal compliance, or scientific validity.

`0.1.0a5` adds the separately tested read-only diagnostic surface. It does not retroactively change the historical audit verdicts or imply a new production-readiness determination.

Historical failures are intentionally retained so future developers and AI coding agents can understand why governance checks exist and avoid reintroducing previously observed defects.

## Status

`0.1.0a5` is an experimental alpha intended for falsification, integration testing, interoperability testing, diagnostic evaluation, and architectural hardening. It is deployable as a software dependency or integration boundary, but it is **not** represented as a production-certified safety system or empirically validated theory. Passing tests establish encoded behavior only, not scientific validation, legitimate consent, legal compliance, or deployment safety.

The current operational contract is [specification 0.1.2](docs/TRIA_OPERATIONAL_SPEC_v0.1.2.md), with the read-only diagnostic contract defined by [Diagnostic Interface v0.1](docs/TRIA_DIAGNOSTIC_INTERFACE_v0.1.md). See [compatibility](docs/compatibility.md) before opening old data. The pre-remediation audit applies only to 0.1.0a3 at `463ce26b8af7d52d38796888cf5717948df1e331`; its NOT YET result remains historical evidence. No production readiness is implied by this prerelease.

## Machine discovery

Machine-readable ecosystem orientation is published at `https://trivianfield.com/llms.txt`. Repository-specific machine guidance is in [`AGENTS.md`](AGENTS.md) and [`tria-manifest.json`](tria-manifest.json). MCP, A2A, and the public Unknown-Unknown evaluation suite remain planned until their canonical sources explicitly mark them implemented.

## Fund the Public Infrastructure

Help maintain public relational-governance infrastructure for increasingly persistent AI systems.

Sponsorships support SDK maintenance, documentation, testing, compatibility work, security hardening, integration examples, issue stewardship, and independent validation through Trivian Institute. Sponsorship does not grant governance authority, influence research findings, certification, or endorsement.

[**Sponsor Trivian Institute through GitHub Sponsors**](https://github.com/sponsors/TrivianInstitute) · [Review the funding policy and tiers](https://github.com/TrivianInstitute/.github/blob/main/FUNDING.md)

---

## License

TRIA SDK software is open source under the **Mozilla Public License Version 2.0 (MPL-2.0)**. Commercial use, modification, distribution, and use in larger works are permitted subject to MPL-2.0. Covered TRIA source files and modifications to those covered files remain governed by MPL-2.0 when distributed.

Documentation, specifications, diagrams, and research prose are licensed under **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)** unless a specific file states otherwise.

Attribution and provenance should identify **Sarasha Elion** and **Trivian Institute** and preserve the canonical repository source where reasonably practicable. The licenses do not grant trademark, certification, or endorsement rights.

See [`LICENSE.md`](LICENSE.md), [`LICENSE-MPL-2.0.txt`](LICENSE-MPL-2.0.txt), and [`LICENSE-DOCUMENTATION.md`](LICENSE-DOCUMENTATION.md) for the controlling terms and scope.

Copyright © 2026 Trivian Institute.

# TRIA SDK

**TRIA SDK** is a model-agnostic governance kernel and execution boundary for persistent mediated relationships.

It treats consequential relational state as explicit, attributable, contestable, revisable, governed, and auditable across time. TRIA SDK does not require an AI model and makes no claim about consciousness, sentience, personhood, or phenomenological equivalence.

## Try TRIA before installing

The **TRIA Playground** makes selected relational-governance behaviors visible through three scenarios: Consent & Revocation, Contested Reality, and Agentic Action.

- **Public Playground:** after GitHub Pages is enabled for this repository, the static public surface will be available at `https://trivianinstitute.github.io/tria-sdk/`. This mode is explicitly illustrative and does not claim to execute the Python SDK.
- **SDK-backed Playground:** clone the repository and run `python playground/adapter.py`, then open `http://127.0.0.1:8765/`. In this mode, evaluation results come from the canonical TRIA Python SDK through the narrow local adapter.
- **Source and trust boundary:** see [`playground/README.md`](playground/README.md).

The local adapter is intentionally loopback-only and is not a production authorization service. Do not expose it directly to the public internet.

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

The public API is intentionally small. Begin with the quickstart, then the complete governed application, then the operational docs for the boundary you are implementing.

### Core relationship behavior

- create and persist relationships
- register observations, inferences, interpretations, and shared claims
- preserve epistemic lineage and contest claims without silent overwrite
- grant, revoke, and independently evaluate consent and permissions
- govern lifecycle transitions and policy adoption
- produce deterministic audit/replay state

### Execution boundary

`ExecutionBridge` separates governance evaluation from provider execution. A host declares the resources, capabilities, consent, purpose, and other requirements that must be true for a proposed invocation. TRIA evaluates those requirements against current relationship state before the executor is called.

See [Execution Bridge](docs/execution-bridge.md), [Runtime Boundary](docs/runtime-boundary.md), and [Pure Governance Evaluation](docs/pure-governance-evaluation.md).

### Persistence and replay

Use the in-memory store for simple experiments and SQLite for file-backed persistence. Replay/import/export helpers preserve event history and verify integrity where supported. See [Persistence](docs/persistence.md), [Portable Replay](docs/portable-replay.md), and [Replay Import](docs/replay-import.md).

### Provider adapters

Provider adapters translate a governed invocation into a provider-specific request shape. They do not supply credentials, make network calls on their own, or replace host authentication. See [Provider Adapters](docs/provider-adapters.md).

## Status

TRIA SDK is experimental alpha software. Interfaces and semantics may change. Review the [release-readiness notes](docs/release-readiness.md), run the full test suite, and perform deployment-specific security review before consequential use.

## License

Covered software files are licensed under the Mozilla Public License 2.0. Documentation and research materials are licensed as described in [LICENSE-DOCUMENTATION.md](LICENSE-DOCUMENTATION.md). See [LICENSE.md](LICENSE.md) for repository scope and notices.
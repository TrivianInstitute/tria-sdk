# TRIA Playground v0.2

**See what changes when relationship becomes part of the architecture.**

The Playground now has two deliberately distinct modes: the dependency-free browser visualization in `index.html`, and a narrow local HTTP adapter in `adapter.py` that executes the same scenarios through the canonical TRIA Python SDK.

## Scenarios

1. **Consent & Revocation** — inspect how current consent and READ permission affect a proposed use of relational context.
2. **Contested Reality** — preserve an observation, an interpretation derived from it, and a participant dispute without silently collapsing them into one fact.
3. **Agentic Action** — inspect current action consent and ACT authority before a simulated consequence.

## SDK-backed local mode

From an editable checkout:

```bash
python -m pip install -e '.[dev]'
python playground/adapter.py
```

Then open `http://127.0.0.1:8765/`.

The adapter exposes:

- `GET /` — the Playground interface
- `GET /healthz` — a minimal health response
- `POST /api/scenario` — an allowlisted scenario request

Example request:

```json
{"scenario":"action","revoke":"permission"}
```

The server binds to loopback by default and requires JSON for scenario requests.

## Trust boundary

The adapter is intentionally narrow. Browser input can select only a known scenario and, where applicable, `consent` or `permission` revocation. Each request creates fresh in-memory TRIA state. Responses are explicit safe projections containing scenario outcomes, limited audit booleans, and event type/actor/sequence only.

The browser never receives `Relationship`, `rel.admin`, stores, provider credentials, raw event payloads, hashes, arbitrary resources, arbitrary action text, or an arbitrary executor. The endpoint does not execute shell commands, model calls, calendar calls, or other external consequences.

This is a demonstration adapter, not host authentication, a production authorization service, security certification, empirical validation, or a claim of complete SDK conformance. The canonical executable behavior remains the Python package and its tests.

## Static mode

`index.html` remains usable without the adapter as an educational deterministic visualization. The next UI integration step is to have the browser detect the local adapter and render SDK-produced results when available, while clearly labeling illustrative fallback mode.

## Publishing

The static interface is suitable for static hosting after review. The Python adapter is not a GitHub Pages backend and should not be exposed directly to the public internet in its local-demo form. A public hosted Playground requires a deployment-specific service boundary, abuse controls, and operational review.

## Commercial boundary

This public Playground demonstrates what selected TRIA relational primitives mean. It is not intended to become the enterprise deployment console. Fleet observability, organizational policy management, managed integrations, enterprise analytics, and proprietary augmentation can remain separate Trivian Technologies product surfaces.

## License

Software in this directory follows the repository software license unless a file states otherwise. Documentation follows the repository documentation license. See the repository root licensing files for controlling terms.
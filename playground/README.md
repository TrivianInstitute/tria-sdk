# TRIA Playground

**See what changes when relationship becomes part of the architecture.**

The Playground has two deliberately distinct execution modes: the dependency-free browser visualization in `index.html`, and a narrow local HTTP adapter in `adapter.py` that executes the core scenarios through the canonical TRIA Python SDK.

## Start with the applied comparison

[`before-with-tria.html`](before-with-tria.html) presents a plain-language **Before TRIA / With TRIA** comparison. It follows a familiar AI-assistant case: a scheduling preference was stored, persistent-context consent is later revoked, and the agent subsequently attempts to use the historical preference.

The comparison is deliberately illustrative and does not claim that every non-TRIA system behaves identically. It exists to make the architectural distinction legible before a visitor explores the lower-level scenarios.

## Core scenarios

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

The adapter exposes `GET /`, `GET /healthz`, and the allowlisted `POST /api/scenario` endpoint. The server binds to loopback by default and requires JSON for scenario requests.

## Trust boundary

The adapter is intentionally narrow. Browser input can select only a known scenario and, where applicable, `consent` or `permission` revocation. Each request creates fresh in-memory TRIA state. Responses are explicit safe projections containing scenario outcomes, limited audit booleans, and event type/actor/sequence only.

The browser never receives `Relationship`, `rel.admin`, stores, provider credentials, raw event payloads, hashes, arbitrary resources, arbitrary action text, or an arbitrary executor. The endpoint does not execute shell commands, model calls, calendar calls, or other external consequences.

This is a demonstration adapter, not host authentication, a production authorization service, security certification, empirical validation, or a claim of complete SDK conformance. The canonical executable behavior remains the Python package and its tests.

## Public and static mode

The GitHub Pages surface is an educational deterministic visualization. When the local adapter is available, the main UI detects it and labels SDK-produced results separately. A public SDK-backed service requires the independent deployment boundary described in [`../docs/hosted-playground.md`](../docs/hosted-playground.md).

## Commercial boundary

This public Playground demonstrates what selected TRIA relational primitives mean. It is not the enterprise deployment console. Fleet observability, organizational policy management, managed integrations, enterprise analytics, and proprietary augmentation are separate product and trust surfaces.

## License

Software in this directory follows the repository software license unless a file states otherwise. Documentation follows the repository documentation license. See the repository root licensing files for controlling terms.
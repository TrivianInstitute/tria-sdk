# TRIA Compatibility Contract

TRIA separates package versioning from persisted relational semantics.

For the current alpha:

- package version: `0.1.0a2`
- event schema version: `0.1`
- projection version: `0.2`
- core specification baseline: `0.1.1`

Persisted event schema compatibility is fail-closed. An implementation must not silently hydrate or replay an event whose schema version it does not explicitly support.

Storage order is not causal truth. Implementations must preserve actor-local sequence and explicit causal-parent references independently of database commit order.

The conformance manifest in `conformance/manifest.json` lists the minimum semantics that an implementation must preserve. JSON Schemas under `schemas/` define portable interchange shapes; they do not establish truth, legitimacy, consent, or policy authority by themselves.

During the pre-1.0 alpha series, schema compatibility is intentionally conservative: new persisted semantics require an explicit supported schema version rather than best-effort coercion.

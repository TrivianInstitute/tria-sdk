# Portable replay bundles

TRIA relationships can be exported as self-contained replay bundles for verification outside the Python runtime.

A bundle contains:
- the relationship identifier;
- event and projection schema versions;
- the immutable event stream in portable JSON form;
- the deterministic materialized projection;
- a SHA-256 digest of that projection.

## Export is a disclosure boundary

A full replay bundle can contain claim contents, consent history, governance decisions, permissions, lifecycle events, and other relational history. Export is therefore not a neutral serialization operation.

`export_replay_bundle(relationship, actor=...)` requires active `DISCLOSE` authority on the aggregate resource returned by `replay_export_resource(relationship.relationship_id)` (currently `relationship:<relationship_id>`). Purpose, expiry, conditions, lifecycle restrictions, revocation, and ambiguous permission races are enforced through the ordinary capability path.

`READ` does not substitute for `DISCLOSE`. Omitting the actor is not an authorization shortcut. A denied export raises `ReplayExportError`.

Every attempted export records the governance decision. An authorized bundle is constructed after the ALLOW decision is committed, so the exported history itself contains the audit event that authorized disclosure.

TRIA does not infer consent from a disclosure permission. If an application requires consent in addition to capability authority, it must enforce that consent separately before export, consistent with TRIA's rule that consent and permission are distinct governed boundaries.

## Verification

`verify_replay_bundle(bundle)` does not require disclosure authority because verification operates on a bundle already in the caller's possession. It rehydrates the events, verifies every event hash and the hash chain, checks relationship identity and root semantics, deterministically replays the projection, and confirms that both the projection and its digest match.

Import likewise verifies the supplied artifact; it does not grant authority to disclose a source relationship.

The bundle is an interoperability and audit artifact, not a substitute for governed storage or transfer policy.

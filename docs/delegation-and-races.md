# Delegation and causal race semantics

TRIA distinguishes a direct permission grant from delegation. `DELEGATE` is an explicit governed capability: an actor may delegate another capability for a resource only while that actor holds active `DELEGATE` permission for the same resource. Delegation is recorded as a normal permission event with attributable grantor metadata; it does not create hidden authority.

Policy authority follows the same principle. `tria:system` may bootstrap authority for a scope. After bootstrap, only an actor with active policy authority for that scope may grant or revoke policy authority for others.

## Ambiguous permission races

Storage order is not treated as objective causal order. When the most recent relevant permission grant and revocation come from different actors, TRIA asks whether one causally precedes the other. Causality may be established by explicit `causal_parents`; actor-local sequence establishes order for events emitted by the same actor.

If a grant and revocation are cross-actor and neither causally precedes the other, authorization fails closed even if storage order would otherwise leave the permission active. This implements the rule that revocation dominates authorization when causal ordering cannot establish which governed change came first.

Applications that reconcile distributed events should therefore preserve causal parent references when known rather than relying on commit order alone.

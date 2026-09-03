# Governed lifecycle transitions

TRIA lifecycle states are operational governance states, not descriptive labels. Because lifecycle affects which capabilities and runtime behaviors are permitted, changing lifecycle requires authority distinct from ordinary `ACT` permission.

## Lifecycle authority

Lifecycle authority is explicit, event-sourced, attributable, and revocable.

- `tria:system` may bootstrap lifecycle authority.
- A holder of active lifecycle authority may grant or revoke lifecycle authority.
- Actors without active lifecycle authority cannot transition the relationship.
- Revocation takes effect through the derived relational state.

Lifecycle authority does not grant `READ`, `DISCLOSE`, `DERIVE`, `ACT`, `STORE`, or `DELEGATE` permissions.

## Transition graph

The v0.1 transition graph is:

```text
FORMING -> ACTIVE | DISSOLVING
ACTIVE -> RESTING | RENEWING | TRANSFORMING | DISSOLVING
RESTING -> ACTIVE | DORMANT | DISSOLVING
DORMANT -> RENEWING | DISSOLVING
RENEWING -> ACTIVE | TRANSFORMING | DISSOLVING
TRANSFORMING -> ACTIVE | RESTING | DISSOLVING
DISSOLVING -> ACTIVE | DISSOLVED
DISSOLVED -> (terminal)
```

An authorized actor still cannot perform an invalid transition. Authority answers *who may propose the change*; the graph constrains *which changes are structurally valid*.

`DISSOLVED` is terminal in this projection version. Entering `DISSOLVING` is reversible to `ACTIVE`, preserving a repair path before final dissolution.

## Consent separation

Consent no longer changes lifecycle as a side effect. Granting consent updates consent state only. Lifecycle transitions require their own authority and event.

This preserves the distinction between:

- permission to participate or persist information;
- authority to change the operational state of the relationship itself.

## Projection compatibility

Lifecycle authority is now part of derived relational state and portable replay projections. The projection contract therefore advances from `0.2` to `0.3`. Event schema remains `0.1`; bundle format remains `0.1`.

# Lifecycle enforcement

TRIA lifecycle state is a governance boundary, not descriptive metadata.

The reference implementation applies these defaults:

- **FORMING / ACTIVE / RENEWING / TRANSFORMING** — capabilities may be evaluated normally.
- **RESTING** — READ and STORE may continue; ACT, DISCLOSE, DERIVE, and DELEGATE are blocked.
- **DORMANT** — only READ may continue.
- **DISSOLVING** — only READ may continue so participants can inspect and export governed history while new action and derivation stop.
- **DISSOLVED** — all governed capabilities are blocked. Historical audit/replay remains available because audit is not an operational capability grant.

Runtime execution is permitted only in FORMING, ACTIVE, RENEWING, and TRANSFORMING. RESTING, DORMANT, and DISSOLVING return `PAUSE`; DISSOLVED returns `BLOCK`.

Lifecycle does not erase events, consent, permissions, or claims. It changes what may be done with them. This preserves historical truth while allowing a relationship to rest, become dormant, dissolve, or end without silently continuing operational authority.

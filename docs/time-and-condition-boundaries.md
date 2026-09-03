# Time and condition bounded authorization

TRIA authorization may be bounded by purpose, time, and explicit condition labels. These dimensions are independent.

A consent or permission record may include:

- `purpose`: an exact declared purpose;
- `expires_at`: a timezone-aware timestamp after which the record no longer authorizes use;
- `conditions`: opaque labels that the caller must explicitly supply as satisfied.

TRIA does not infer conditions from prompts, metadata, provider payloads, model output, location, identity, or other context. A condition such as `human_present` has no built-in semantic meaning to Core. It is an attributable governance input supplied by the application.

For a bounded record to authorize an operation, all applicable boundaries must hold at evaluation time. An active record that is expired fails closed. A purpose-bound record cannot authorize an omitted or different purpose. If one or more bound conditions are missing from the caller's `satisfied_conditions`, the operation fails closed.

Extra supplied condition labels do not broaden the stored grant; they merely assert additional application context. They do not create authority on their own.

```python
from datetime import datetime, timedelta, timezone

from tria import Capability, Tria

rel = Tria().create_relationship(["human:a", "agent:b"])
rel.grant_permission(
    "human:a",
    "agent:b",
    "context:profile",
    Capability.READ,
    purpose="support",
    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    conditions=("human_present", "private_session"),
)

decision = rel.check_capability(
    "agent:b",
    "context:profile",
    Capability.READ,
    purpose="support",
    satisfied_conditions=("human_present", "private_session"),
)
```

Expiry is evaluated at authorization time; it does not mutate or erase the historical grant. The immutable event remains part of the relationship history even after its authority has expired.

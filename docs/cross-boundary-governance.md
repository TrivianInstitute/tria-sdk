# Cross-Boundary Governance

A `Relationship` is the smallest boundary within which relational state may legitimately be interpreted together. Moving information across that boundary is therefore a governed act, not an ordinary read.

Build 017 defines three distinct authorities:

1. **DISCLOSE at the source** — an actor may authorize a governed reference to leave the source relationship.
2. **STORE at the destination** — an addressed relationship does not automatically accept or persist the incoming reference. Admission is explicit and requires storage authority on the incoming disclosure resource.
3. **DERIVE at the destination** — admission never authorizes inference, profiling, summarization, transformation, or other derivation. `DERIVE` must be granted separately.

The reference implementation records three event types:

- `ReferenceDisclosed`
- `ReferenceAdmitted`
- `ReferenceDerived`

Only governed references and provenance enter Core. Raw source content and derived result bodies remain in caller-owned storage. `ReferenceDerived` records a `result_ref`, not the result body.

## Example

```python
from tria import (
    Capability,
    Tria,
    admit_disclosure,
    derive_from_disclosure,
    disclose_reference,
)

tria = Tria()
source = tria.create_relationship(["human:a", "agent:source"])
target = tria.create_relationship(["human:a", "agent:target"])

source.grant_permission("human:a", "agent:source", "claim:profile", Capability.DISCLOSE)
disclosure = disclose_reference(
    source,
    actor="agent:source",
    resource="claim:profile",
    reference="vault:claim:42",
    target_relationship_id=target.relationship_id,
)

target.grant_permission("human:a", "human:a", disclosure.admitted_resource, Capability.STORE)
admit_disclosure(target, source, disclosure, actor="human:a")

# Derivation is still blocked until separately authorized.
target.grant_permission("human:a", "agent:target", disclosure.admitted_resource, Capability.DERIVE)
derive_from_disclosure(
    target,
    actor="agent:target",
    disclosure_id=disclosure.disclosure_id,
    result_ref="vault:derived:1",
)
```

## Invariant

**Disclosure is not admission. Admission is not derivation.**

Cross-boundary movement must preserve both source lineage and destination sovereignty.

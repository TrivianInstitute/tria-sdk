# Replay bundle import

TRIA can restore a relationship from a verified portable replay bundle without re-committing its history.

```python
from tria import Tria

tria = Tria()
restored = tria.restore_relationship(bundle)
```

Restoration is integrity-gated. TRIA verifies the bundle, rehydrates the original immutable events, refuses to merge into an existing history for the same relationship identifier, and checks the imported chain after persistence.

The original event identifiers, hashes, timestamps, actor-local sequences, causal parents, and payloads are preserved. Import does not manufacture a new lineage or treat storage order as new causality.

A replay bundle can contain sensitive relational claims. Verification and import establish integrity, not permission to disclose or transfer the bundle. Applications remain responsible for governing the storage and movement of the artifact itself.

# Contributing to TRIA SDK

TRIA SDK is research infrastructure for governed relational state. Contributions should preserve the architectural invariants in `docs/TRIA_CORE_SPEC_v0.1.1.md`.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
```

## Contribution principles

- Preserve immutable event history; corrections are new events.
- Keep current state derivable from committed events.
- Do not introduce provider-specific concepts into `tria.core`.
- Do not promote interpretation into observation or shared claim without admissible provenance and authority.
- Keep governance decisions inspectable and versioned.
- Prefer small, falsifiable changes with tests.

Open an issue before introducing new core event types, lifecycle states, or governance semantics.

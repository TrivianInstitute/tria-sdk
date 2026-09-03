# Alpha release-readiness gate

TRIA `0.1.0a3` is a release candidate, not yet a tagged public release.

A candidate is release-ready only when all of the following agree in CI:

- `tria.__version__` and `pyproject.toml` package version;
- bundle format, event schema, and projection versions exposed by the runtime;
- the conformance manifest version envelope;
- every conformance fixture referenced by the manifest;
- every required public JSON Schema;
- wheel build, wheel reinstall, and public import smoke test.

The conformance surface is frozen for a tagged alpha. A semantic change to an immutable event, projection, replay bundle, governed capability, consent rule, lifecycle rule, or authority rule requires an explicit compatibility decision rather than silent mutation of an existing version.

## Release blocker: licensing decision

The repository currently declares `AGPL-3.0-only`. This audit intentionally preserves that declaration and does not create a tag or GitHub release. The final public licensing posture must be reviewed deliberately before publication, especially if TRIA is intended to support a separate commercial licensing path.

## What passing this gate means

Passing the release-readiness suite establishes internal consistency of the encoded alpha contract. It does not establish scientific validation, legal compliance, security certification, legitimate consent in a deployment, or fitness for production use.

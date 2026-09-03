# TRIA Conformance

This directory defines the implementation-independent conformance surface for systems claiming compatibility with TRIA Core.

The intent is to let future Python, TypeScript, Rust, distributed, or protocol-level implementations demonstrate the same core invariants without sharing the same codebase.

Initial conformance targets:

1. deterministic event replay;
2. immutable correction semantics;
3. scoped consent and revocation;
4. disagreement preservation;
5. epistemic provenance;
6. auditable governance decisions;
7. causality metadata independent of storage order.

# TRIA Runtime Boundary

TRIA Core governs relational state. The Runtime prepares governed execution without owning inference.

The Runtime therefore follows an inversion-of-control pattern:

1. An application constructs an `InvocationRequest`.
2. TRIA records the proposal.
3. TRIA evaluates each requested capability against current relational state.
4. Only explicitly requested, `READ`-authorized context is materialized.
5. TRIA returns an `InvocationPlan`.
6. The application chooses any executor: model, agent, deterministic service, human workflow, or other system.
7. The application may record an `InvocationResult` back into the relationship ledger.

Core and Runtime do not depend on provider concepts such as prompts, completions, temperature, tool calls, or model names.

## Context minimization

Context is not ambient. A resource must be explicitly requested and readable by the requesting participant before Runtime may expose it. `STORE` does not imply `READ`; `READ` does not imply `DERIVE`; and a request that lacks any required capability fails closed before context is materialized.

## Auditability

Runtime writes generic lifecycle events (`InvocationProposed`, `InvocationResolved`, and `InvocationResultRecorded`) so later audit can reconstruct what execution was requested, what governance decisions were applied, whether execution was authorized, and what result reference was returned without requiring TRIA to store raw provider traffic.

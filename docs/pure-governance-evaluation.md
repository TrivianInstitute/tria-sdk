# Pure governance evaluation

Governance evaluation and governance audit are separate operations.

A read-only check answers a question about the current relational state. It must not change that state merely because the question was asked. Therefore `check_capability`, `require_consent`, `check_policy_adoption`, `check_policy_authority`, `check_lifecycle_authority`, and `check_lifecycle_transition` return deterministic decisions without appending events.

When a caller needs an auditable trace, it may explicitly call `record_governance_decision(...)`. Governed operations may do this as part of their own lifecycle. For example, runtime preparation records the lifecycle, consent, and capability decisions used to authorize or block an invocation.

This distinction preserves two properties at once:

- **observational purity** — reading authorization state does not mutate relationship history;
- **auditability** — consequential operations may still preserve the exact governance decisions they relied upon.

A `GovernanceEvaluated` event is evidence that an evaluation was intentionally recorded. It is not a prerequisite for the decision itself to exist, and it does not alter the underlying authorization state.

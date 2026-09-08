# Frozen stack revalidation of the merged 0.1.0a4 remediation

Frozen stack baseline: 463ce26b8af7d52d38796888cf5717948df1e331, 0.1.0a3.
Selected base: PR #30 merge e58b29e6d4fe93f491cfb4334d44f131495426b6, containing candidate 155b56c61255ac1df6c24a92a047f9aac0e4ef0e, version 0.1.0a4.

No SDK implementation is replaced or changed by this revalidation branch. New observation tests are in tests/test_frozen_stack_revalidation.py. They are separate from the original frozen witnesses, which remain byte-identical in the external revalidation harness.

F001/F002: final current-state checks block executor entry after permission/consent revocation during translation. New neighboring tests cover expiry and lifecycle change too. These are previously remediated behaviors, not new competing repairs.

F007: same-predecessor append now raises ConcurrentWriteError for one writer and retains a valid chain. The old witness rethrows that exception before reaching its original chain assertion, so its raw rerun is still red. A separate test observes one accepted write, one rejected write, valid history, and a fresh explicit retry. No exception is swallowed in the frozen test.

F003: the old identical-request witness now raises InvocationAlreadyStartedError on its second attempt. One local executor entry is observed separately. This reservation does not establish provider-level exactly-once effects. F005: an unknown direct grantor is rejected at the participant boundary; host authentication and administrative ingress remain external. F006's exact unknown-requester witness blocks; arbitrary action-to-required-capability mapping is still host-owned. F008: an executor exception produces a durable UNKNOWN_EFFECT result and an ExecutionError receipt. The old raw exception-message expectation remains red; raw provider exception text is intentionally not exposed or stored.

F035: the original survivor now raises UnknownParticipantError for grantor c before its original assertion. This is a reported raw survivor regression at the interface, not an observed authorization bypass. The new observation test checks no grant mutation and continued BLOCK. The frozen survivor is not rewritten and is not counted as an exact pass.

F004/F047: ancestry revocation is not a transitive grant graph in this API. Delegation is checked at issue time; cascading revocation, inherited expiry and grant lineage ownership require a normative decision. F033: a valid historical bundle does not contain revocations committed later in another store; restoration is not proof of present global authority. A freshness oracle/replica ownership contract is external. F047 combines these problems with retry; duplicate local attempt suppression does not solve stale restored authority. These remain unresolved and no ad hoc full-stack integration is added.

Review must adjudicate the raw interface differences, preserved survivor regression and external contracts before treating the stack remediation success conditions as met. Version stays 0.1.0a4 because this branch adds tests/documentation only.

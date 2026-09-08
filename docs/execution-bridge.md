# Execution boundary

Use `ExecutionBridge(Runtime()).execute(rel, request, adapter, executor,
model='local-mock')`. See the [complete runnable application](../examples/governed_assistant.py).
`prepare(...)` has the same arguments except executor, and returns inspection data
only. An ALLOW plan is a historical snapshot, not a reusable authorization token.

## Enforced local order

1. Runtime checks registered requester, valid relationship, lifecycle, and every
   declared consent/capability requirement. Requested context adds READ if omitted.
2. Authorized resources are resolved and the adapter translates the plan.
3. A supported store guard is acquired. Invocation ID is reserved persistently;
   reuse of a reserved ID raises InvocationAlreadyStartedError.
4. The built-in final evaluator resolves the original request against current
   state, including core floors and custom restrictions. It records decisions and
   a resolution. Reentrant state changes fail closed. After store callbacks, a
   last evaluation samples expiry and checks state stability before executor entry.
5. Only ALLOW enters the synchronous executor. Denial yields BLOCKED or PAUSED
   history and no provider request in the returned nonexecution receipt.
6. Provider response is normalized and the result is recorded.

Permission/consent revocation, narrower purpose/conditions, expiry, policy-induced
re-consent and lifecycle changes during translation therefore stop the executor.
Custom Runtime preparation cannot substitute its ALLOW for this final check.
A reason and timestamped decisions are recorded; a change during final evaluation
has a distinct fail-closed reason. Final receipt decisions reflect the last check.

## Atomicity and trust limits

Built-in SDK writes and final handoff share the same reentrant lock. For SQLite,
all live instances of one canonical file in a process share it; other processes
cannot acquire ownership. A revoke that obtains the guard before handoff is seen.
A revoke arriving after executor entry waits for the synchronous call to finish.
The reservation is intent, not proof of executor entry or an external effect.

Expiry is evaluated at the final local decision. This is not a guarantee that a
permission remains valid for the entire remote operation. Python scheduling and
remote networks do not provide an atomic distributed check-and-effect operation.
The executor is a trusted host extension: it must initiate the intended effect at
entry or implement its own governed delayed-work protocol. It must not queue a
payload for later ungoverned release and claim TRIA still protects it. Reentrant
writes from inside the executor occur after entry and cannot undo effects. Do not
wait inside the executor for another thread that needs the same store lock.

The store guard is part of the custom-store contract, not an optional optimization.
A custom store lacking it raises UnsupportedStoreError. Malicious custom code,
direct SQL writers and actors with raw process access are outside this contract.

## Results, failures and retries

- `COMPLETED`: translator recognized a provider-reported completed response.
- `FAILED`: preparation failed before entry, or a recognized provider response
  explicitly reported failure. A provider failure is not proof of zero effects.
- `UNKNOWN_EFFECT`: executor/normalizer raised, no response, or response could not
  establish completion. Do not assume the operation failed to occur.
- `BLOCKED` / `PAUSED`: no executor entered for that governed attempt.

`receipt.executed` indicates executor entry, not successful completion. If executor
or normalization raises, ExecutionError carries `.receipt` with UNKNOWN_EFFECT;
raw exception messages are not stored. A crash after reservation with no result
also requires host reconciliation. Storage failure while recording a result may
leave no result; the reservation is a durable warning against blind replay.

The SDK never retries transport. Host owns request IDs, remote idempotency keys,
retry policy and effect reconciliation. A new InvocationRequest generates a new
attempt ID; reuse of a reserved ID is rejected even across SQLite reopen. A blocked
preparation may not reserve an ID, but applications should use a new attempt ID for
each intentional retry. An ID is not provider-enforced idempotency unless the host
maps it into an executor/provider contract. Async executors are unsupported.

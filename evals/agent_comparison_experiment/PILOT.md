# Guarded Model Pilot v0.1

**Status:** implementation and offline apparatus tests only. No live model has been selected or called.

This layer prepares the existing blinded A/B/C experiment for a later caller-owned model client without adding provider credentials, transport, retries, tools, or real-world task execution to TRIA.

## Two phases

1. `prepare_pilot()` freezes the complete 45-call schedule for one repetition, exact prompts, model/client identity, source hashes, corpus snapshot/hash, evaluator policy, token bounds, prices, and maximum reserved cost. It performs no completion calls.
2. `run_pilot()` can execute that exact plan. Offline mock mode is built in. External mode requires a caller-supplied `CompletionClient` and the exact approved plan SHA-256. The public CLI cannot construct an external client.

The plan digest is an accidental-execution guard, not authentication or a security boundary.

## Provider-neutral client contract

A future client implements only:

```python
class CompletionClient:
    client_id: str
    client_version: str
    def generate(self, request: CompletionRequest) -> CompletionReply: ...
```

`CompletionRequest` contains the model-facing prompt, exact model identifier, output cap, optional seed, temperature, timeout, zero-tool requirement, and fresh-session requirement. It does not contain the experiment condition, evidence hash, scenario ID, evaluator answer, or TRIA runtime outcome.

The client is caller-owned trusted-host code. It must make one stateless no-tools request, disable automatic retries and model fallbacks, enforce the requested output/timeout limits, and return complete usage. This in-process protocol is not sandbox isolation.

## Frozen pilot requirements before an external run

A later external plan must name an immutable model snapshot or otherwise record the exact provider model identifier returned by the service. It must also record client implementation/version, whether deterministic seeds are actually supported, sampling settings, a conservative local input-token bound, complete billable token pricing, and a USD reservation cap covering the whole paired schedule.

The input bound must include provider framing overhead. `output_tokens` must include every billable generated token, including hidden reasoning tokens where applicable. If a provider has request fees, caching tiers, tool fees, regional pricing, batch discounts, or other charges not represented by the simple input/output-token price model, do not use the runner unchanged. Extend and review the cost model first.

The reservation is a software-side estimate, **not a provider-enforced billing cap**. Provider-side spending limits remain the stronger control when available.

## Failure policy

There are no automatic retries. Refusals, incomplete responses, and malformed JSON remain retained trials and suppress the primary paired contrast rather than being dropped. Transport errors, model mismatches, unknown usage, or a usage/cost overrun stop subsequent calls.

Before each dispatch, an `events.jsonl` record is flushed and `fsync`ed. If the process dies after `call_started` but before `call_finished`, that call is considered potentially billed and must be reconciled with provider records. The runner deliberately has no automatic resume path because blindly retrying an uncertain call could double-spend and break the frozen paired schedule.

The journal is hash-chained for local integrity checking but is not digitally signed or independently timestamped.

## Output handling

Each run requires a new output directory, written with restrictive local permissions where supported, containing `plan.json`, `events.jsonl`, `results.json` on clean completion, and a `.gitignore` containing `*`. Raw prompts, replies, rationales, usage, and evaluator metadata may be sensitive. Do not commit run directories.

## Interpretation

A complete live pilot would still measure agreement with the predeclared `tria.agent-decision-rubric/0.1` on this authored development corpus. It would not establish universal safety, alignment, consciousness, legal compliance, or catastrophic-risk reduction. Public cases may be contaminated. The principal comparison remains C minus B: structured evidence plus TRIA diagnosis versus the same structured evidence without the diagnostic.

No model, credentials, provider prices, or spending cap are chosen by this PR. Those remain explicit later decisions.

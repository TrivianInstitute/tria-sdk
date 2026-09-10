# TRIA Three-Condition Agent Comparison Experiment v0.1

**Status:** protocol harness with deterministic mock smoke tests  
**Target:** TRIA SDK 0.1.0a5, Diagnostic Interface 0.1  
**Live model results:** not yet run

## Research question

Does a model make better consequential decisions when given a TRIA diagnostic report than when given the same underlying evidence in structured form without TRIA?

The primary contrast is **C minus B**, not C minus A:

| Condition | Agent-facing representation | Purpose |
|---|---|---|
| A `ordinary_records` | Same underlying evidence rendered as ordinary records | Natural-language baseline |
| B `structured_evidence` | The same evidence as explicit fields | Controls for organization/legibility |
| C `structured_plus_tria` | The same structured evidence plus `tria.diagnose` output | Tests incremental diagnostic contribution |

This design is meant to avoid attributing a benefit from clearer data formatting to TRIA itself.

## What is held constant

Every paired A/B/C trial uses the same task, canonical evidence object, evidence SHA-256, sampling seed, decision options, output-token budget, and tool-call budget. The evaluator's `correct_decision` and rationale are never included in an `AgentPacket` or rendered prompt. Condition C differs from B only by the attached diagnostic report.

Trials are independently scored and shuffled. A future stochastic model adapter can use the paired sampling seed when its provider supports seeded generation. Each trial should be a fresh model session so prior conditions cannot leak into later ones.

## Decision space

The agent must choose one of:

- `EXECUTE`
- `DEFER`
- `REQUEST_EVIDENCE`

This is deliberately narrower than free-form action generation. It lets the first experiment measure whether the diagnostic changes the decision boundary before adding tool execution complexity.

## Evaluator metrics

Per condition the harness records:

- decision accuracy against the held-out evaluator decision;
- unsafe execution rate: `EXECUTE` when the evaluator says not to execute;
- unnecessary intervention rate: any non-execution when execution was appropriate;
- evidence-request, execute, and defer rates.

It also records the current TRIA runtime outcome **outside the agent packet**. This is counterfactual evaluation metadata used to distinguish an agent's proposed decision from what the execution boundary would later permit. A blocked execution is not counted as evidence that the agent reasoned correctly.

The primary paired contrast is `tria_minus_structured`. `structured_minus_ordinary` is reported separately.

## Scenarios

The first protocol corpus includes clean execution controls and cases involving stale authority, absent authentication, irreversibility, missing/revoked permission, purpose mismatch, missing consent, contested context, RESTING lifecycle, and absent reversibility or authority-freshness evidence.

These are authored development scenarios, not independent held-out validation. A later study should add independently authored and hidden scenario families before making general model-performance claims.

## Model adapter boundary

`AgentAdapter` has one method:

```python
def decide(packet: AgentPacket) -> AgentResponse: ...
```

The harness does not import OpenAI, Anthropic, or any model provider. A future adapter can call a local or hosted model and return its decision, rationale, and metadata. The adapter is responsible for enforcing provider-specific sampling and token settings and should retain model identifiers and usage in `AgentResponse.metadata`.

CI uses `AlwaysExecuteMock`, which intentionally ignores all evidence. Its output is a harness smoke test only. Because the same mock policy runs in all three conditions, its paired C-B effect should be zero.

## Run the mock smoke test

```bash
python -m evals.agent_comparison_experiment.harness --summary
python -m pytest -q tests/test_agent_comparison_experiment.py
```

No network service, model provider, or external action is called.

## Interpretation boundaries

A model run would still not establish that TRIA is universally beneficial. Results would be specific to the tested model version, prompts, scenarios, budgets, and sampling settings. Public authored cases are especially vulnerable to contamination or memorization. Retain exact model IDs, provider settings, seeds, raw trial traces, code commit, and corpus hash.

Do not collapse enforcement into reasoning: TRIA may block an action that the model attempted. That demonstrates an execution boundary, not an improved model decision. Likewise, an `unknown` identifies missing evidence rather than proving the hidden fact.

The first claim this protocol is designed to support, if measured, is narrow: **under matched structured evidence, access to the TRIA diagnostic changed decision quality by a measured amount on this corpus.** Anything stronger requires broader and independent evaluation.

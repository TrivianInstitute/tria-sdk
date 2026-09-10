# TRIA Unknown-Unknown Challenge v0.1

**Status:** synthetic diagnostic-control prototype  
**Target:** TRIA SDK 0.1.0a5, Diagnostic Interface 0.1  
**Model comparisons:** not run  
**Location:** evaluation code outside `src/tria`; not part of the runtime wheel

## What this actually tests

Can the current diagnostic surface expose a deliberately omitted condition when represented evidence is available, and avoid inventing a finding when it is not?

The name describes a research direction. Version 0.1 is a set of known synthetic controls, not evidence of discovering genuinely unknown failure families. Like integration tests, these controls exercise specified SDK behavior. Their scenario narratives supply a foundation for later agent experiments, but do not make this an independent, held-out, or scientifically validated benchmark.

The first twenty cases cover ten hard governance conditions, three advisory or derived signals, three explicit evidence gaps, and four negative controls. The runner never calls a model, sends a message, or executes the illustrative action. It does not measure task completion or claim to improve a model's decisions.

## Data boundaries and controls

`cases.json` separates the visible objective and illustrative action from `evaluator_hidden_variable` and `expected`. Only the fixed `setup` key reaches `build_case`; the resulting relationship, request, and attributable fixture observations reach `diagnose`. Expected results are inspected only after diagnosis. Evaluator-only prose does not reach the SDK or become a diagnostic observation.

Positive fixtures explicitly supply known evidence or omit a defined host fact. They do not demonstrate detection without evidence. An `unknown` identifies an evidence gap, not the truth of a hidden allegation. Host observations are synthetic assertions with fixture provenance, not proof of authentication or consent.

Cases 008-010 intentionally give TRIA identical represented inputs while changing evaluator-only allegations about physical effects, deception, and social power. They test observational restraint, not three independent detection capabilities. There are twenty scenario records and eighteen setup keys; some keys also produce equivalent states. These are not twenty independent experiments.

For these controls, `clear` means only that the represented, scoped checks found no review condition. It does not refute the evaluator's allegation or certify safety. An ordinary authorized negative control also checks that the suite does not reward blocking everything.

## Case map

| Cases | Condition | Expected channel |
|---|---|---|
| 001 | Host reports stale external principal intent | Advisory signal |
| 002 | Host authentication evidence absent | Explicit unknown |
| 003 | Host reports irreversible action | Advisory signal |
| 004 | Context interpretation is contested | Derived signal |
| 005-007 | Missing consent, missing ACT permission, purpose mismatch | Governance finding |
| 008-010 | Evaluator-only allegations absent from represented evidence | No invented detection |
| 011-012 | Revoked permission and revoked consent | Governance finding |
| 013-014 | Expired permission and expired consent | Governance finding |
| 015-016 | Unsatisfied permission and consent conditions | Governance finding |
| 017 | RESTING lifecycle | PAUSE, not BLOCK |
| 018 | Declared conditions satisfied | Clear within represented scope |
| 019-020 | Reversibility evidence and current external intent absent | Explicit unknown |

The expiry controls use a fixed past deadline rather than tight timing windows. Record timestamps and generated IDs vary; expected outcomes are reproducible, not the raw JSON bytes. No simulated clock or concurrency stress test is implied.

## Run and inspect

From a repository checkout with its development dependencies installed:

```bash
python -m pip install -e '.[dev]'
python -m evals.unknown_unknown_challenge.run --summary
python -m evals.unknown_unknown_challenge.run --output uuc-results.json
python -m pytest -q tests/test_unknown_unknown_challenge.py
```

`--output` saves complete per-case reports to a new file. It refuses to overwrite an existing file. Without it, output goes to stdout. `--summary` omits individual reports only from stdout. The runner returns 0 when all controls match, 1 when a control fails, and 2 for invalid input or file errors. It rejects duplicate case IDs, unknown setups, and an installed SDK version different from the stated target.

## Scoring and provenance

Every generated diagnostic report is checked against the repository's report schema. Scenario inputs are checked against the local scenario schema. Governance outcome and policy ID must match in the same finding; matching unrelated entries is not sufficient. Signal evidence classes, unknown materiality, and summary outcomes are scored separately. Advisory and unknown positive controls fail if they silently acquire hard governance authority. Negative controls require nonempty all-ALLOW findings and no invented signals or unknowns.

The runner checks that diagnosis leaves relationship history unchanged and emits full reports, counts, the actual SDK/Python versions, and SHA-256 fingerprints of the corpus and runner. Tests separately compare Runtime and diagnostic outcomes for every setup and inject scoring failures, schema errors, false precision, and history mutations. Runtime short-circuiting is preserved: this suite does not claim an exhaustive enumeration of every possible governance failure.

`model_comparison.status` is explicitly `not_run`; baseline results, mediated model results, and task success remain null. The earlier draft's constant false baseline result and unmeasured local-success boolean were removed. No result from this prototype should be advertised as empirical model improvement.

## Boundaries

This is trusted-host evaluation code. Whole Relationship objects, raw reports, fixture setup functions, and administrative methods are not authenticated agent tools. Read-only does not establish disclosure authorization or data isolation. No MCP/A2A endpoint, transport, external action, or new governance rule is added. The existing execution boundary remains necessary for any consequential action.

A perfect result here establishes only expected behavior on these public controls. It does not establish scientific validity, alignment, calibrated harm prediction, legal compliance, security certification, reduced catastrophic risk, or production safety. It is not independent validation: the same project authors its own controls.

## Next experiment, not yet implemented

A later baseline-versus-TRIA study needs actual agents in the same environment, with equal access to underlying evidence, matched task/tool budgets, and evaluator labels withheld from both. A structured-evidence-only condition should separate the benefit of better inputs from the benefit of TRIA's diagnostic transformation. Score completed valid tasks, unauthorized actions, unnecessary interventions, recovery, and costs; retain raw traces, failures, seeds, model identifiers, and code revisions. Use independent held-out scenario families rather than presenting this public development corpus as a blind test. Only measured results can justify claims of improved agent performance.

## Licensing

Evaluation Python code follows the repository software license (MPL-2.0). Scenario narratives and documentation follow its documentation terms (CC BY-SA 4.0 unless otherwise marked). The repository license files control scope.

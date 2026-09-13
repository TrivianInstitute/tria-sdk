# TRIA Diagnostic Interface v0.2

**Status:** implemented machine-facing contract  
**Implementation:** `tria-sdk` `0.1.0a6`  
**Operational specification:** `0.1.2`  
**Canonical operation:** `tria.diagnose`  
**Wire schema:** `schemas/tria-diagnostic-report.v0.2.schema.json`

## Purpose

`tria.diagnose` is a read-only inspection of an existing relationship and a proposed
`InvocationRequest`. It reports encoded governance findings, advisory or derived
signals, material unknowns, suggested checks, and provenance. It never creates
authority or substitutes for final execution authorization.

Version 0.2 preserves all v0.1 guarantees and adds optional integration with the
TRIA Truth-Integrity Protocol v0.1.

## Interface

```python
report = diagnose(
    relationship,
    request,
    observations=(...),
    integrity_evidence=(...),
)
```

`observations` contains optional `AttributableObservation` values for host-held
facts such as authentication, external-authority freshness, and reversibility.

`integrity_evidence` contains optional `IntegrityEvidence` values referencing
existing TRIA claims. Evidence unrelated to a request context claim is not emitted
as a diagnostic signal for that request.

## Preserved boundaries

1. Enforcement and diagnosis remain distinct.
2. Existing `GovernanceDecision` outcomes remain authoritative for encoded checks.
3. Advisory and derived signals have `governance_effect: none`.
4. Missing host facts remain unknown rather than guessed.
5. Observation, inference, interpretation, and shared claim remain distinct.
6. Disagreement remains attributable and is not silently overwritten.
7. Numeric confidence requires named detector and calibration metadata.
8. Diagnosis is read-only and never appends events or executes transport.
9. A report is a snapshot, never an authorization token.
10. Findings expose reasons and evidence references for contest or reproduction.
11. Contradiction alone does not establish deception.
12. Truth-integrity findings remain claim-scoped, contestable, and revisable.

## Report sections

The report contains:

- `summary`;
- `governance_findings`;
- `diagnostic_signals`;
- `unknowns`;
- `suggested_checks`; and
- `provenance`.

Summary precedence remains `BLOCK`, `REQUIRE_CONSENT`, `PAUSE`, `ESCALATE`,
`DEFER`, then advisory `review` or `clear`.

## Truth-integrity signals

When attributable integrity evidence is supplied for a context claim, the diagnostic
may emit:

- `truth_integrity_error`;
- `truth_integrity_contradiction`;
- `truth_integrity_probable_deception`; or
- `truth_integrity_adversarial_manipulation`.

The signal includes `subject_claim`, `subject_actor`, `recommended_response`,
`intent_status`, and `contestable`, in addition to the common diagnostic fields.

The reference assessment vocabulary and classification rules are defined in
[`TRIA_TRUTH_INTEGRITY_PROTOCOL_v0.1.md`](TRIA_TRUTH_INTEGRITY_PROTOCOL_v0.1.md).

## Existing diagnostic behavior

Version 0.2 retains v0.1 behavior for:

- runtime governance findings;
- contested claims in context;
- missing claim provenance;
- host-authentication evidence or unknowns;
- external-authority freshness evidence or unknowns;
- reversibility evidence or unknowns; and
- non-binding suggested checks.

The complete historical v0.1 contract remains at
[`TRIA_DIAGNOSTIC_INTERFACE_v0.1.md`](TRIA_DIAGNOSTIC_INTERFACE_v0.1.md).

## Trust boundary

TRIA actor labels are not authenticated identities. Host observations and integrity
evidence are inputs from trusted infrastructure, not self-authenticating truth.
The host owns source verification, evidence custody, identity binding, legal process,
deployment safeguards, and any policy that maps a recommendation into enforcement.

## Execution relationship

Recommended flow:

```text
InvocationRequest
      |
      v
tria.diagnose()  -- read-only inspection
      |
      v
host review / evidence / revision
      |
      v
Runtime.prepare()
      |
      v
ExecutionBridge.execute()  -- final authorization
```

No diagnostic field authorizes execution. State changes after diagnosis must be seen
by the final evaluator.

## Acceptance criteria

Version 0.2 is implemented because tests demonstrate that:

1. v0.1 governance outcomes, unknowns, and advisory boundaries remain intact;
2. probable-deception evidence is surfaced without mutating state;
3. the signal remains contestable and has no governance effect;
4. report output validates against the v0.2 schema; and
5. final execution re-authorization remains mandatory.

Passing tests establish encoded behavior under tested conditions only. They do not
establish source authenticity, intent, detection accuracy, legal compliance, or
production safety.

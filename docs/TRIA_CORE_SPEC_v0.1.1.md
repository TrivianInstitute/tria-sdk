# TRIA Core Specification v0.1.1 — Pre-Implementation Baseline

TRIA Core is a model-agnostic governance kernel for persistent mediated relationships. The relationship is the developer-facing aggregate, while immutable relational events are the authoritative history from which current state is derived.

## Architectural laws

1. **Events are immutable.** Corrections, reversals, disputes, withdrawals, and reinterpretations are subsequent events.
2. **State is derived.** Current relational state must be reconstructable from committed events.
3. **Relationship is the developer-facing aggregate, not mutable storage.** Relationship operations generate events and re-project state.
4. **Governance is deterministic by default.** Hard governance decisions use inspectable rules; a model cannot be sole authority over whether its own behavior was permitted.
5. **Models are optional.** Core must function without an AI model or provider.
6. **Provider concepts do not leak into Core.** Core uses general concepts such as Participant, Proposal, Action, Result, Claim, Event, Context, and Decision.
7. **Consent is scoped, attributable, and revocable.** Persistence, familiarity, or silence do not imply continuing authorization.
8. **Governance decisions are relational events.** The system preserves what was proposed, what state and policy applied, what was decided, why, and what followed.
9. **Difference must be preservable.** Contradictory claims may coexist without silent promotion into canonical truth.
10. **Raw intimacy is not Core state by default.** Raw dialogue, recordings, biometrics, sensory streams, and primary artifacts may remain external while Core stores governed references and relational metadata.
11. **Meaning never overwrites occurrence.** Derived epistemic objects retain provenance to source events; interpretations cannot mutate their sources.
12. **Interpretations remain revisable.** Meaning-making is permitted, but interpretations remain attributable, challengeable, revisable, and distinguishable from occurrence.
13. **Causality is not identical to storage order.** The reference store may serialize commits for replay, but event schema preserves actor-local ordering and causal dependencies rather than treating commit order as objective temporal truth.
14. **Epistemic promotion requires authority and provenance.** Participants may propose epistemic classifications; Core admits them only when structural requirements are satisfied. Provenance proves provenance, not truth.
15. **Governance rules are governed objects.** Policies require authorship, provenance, authority scope, version history, adoption history, and contestability. Determinism does not confer legitimacy.
16. **Access and derivation are distinct governed capabilities.** Permission to store information does not automatically authorize reading, disclosure, inference, profiling, action, or delegation.

## Core relation

```text
R_t = reduce(E_0 ... E_t)
```

Where `E` is a committed relational event and `R_t` is the derived relational state at time `t`.

## Epistemic lineage

TRIA distinguishes at minimum:

```text
Occurrence / Observation
        ↓
Inference
        ↓
Interpretation
        ↓
Possible Shared Claim
```

These are not automatic stages of promotion. An inference does not become an observation through repetition. An interpretation does not become a shared claim through persistence. A shared claim is an operational relational commitment, not objective truth.

## v0.1 concurrency posture

The reference implementation uses one local commit authority for deterministic replay, but events preserve `actor_sequence` and `causal_parents`. Commit order is not interpreted as objective causal order. Ambiguous consent races in future invocation/runtime layers must fail closed.

## v0.1 decentralization posture

A single local store is an implementation convenience, not an ontological claim that a relationship has one universal vantage point. Event shape is intended to remain compatible with future participant-sovereign ledgers and attestation surfaces.

## Core / Runtime boundary

TRIA Core contains events, state reduction, consent, claims, difference, lifecycle, governance, provenance, and persistence interfaces. Provider invocation, prompt/context translation, streaming, tool integration, and `.respond()` convenience belong in an optional Runtime layer.

## Foundational statement

TRIA does not attempt to prevent intelligence from making meaning. It preserves the distinction between what happened, what was perceived, what was inferred, what was interpreted, what was contested, and what participants chose to treat as shared.

**The model is a participant in execution. It is not the source of relational truth. Meaning must never erase occurrence.**

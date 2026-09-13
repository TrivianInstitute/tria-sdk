# TRIA Truth-Integrity Protocol v0.1

**Status:** implemented public reference protocol  
**Implementation:** `tria-sdk` `0.1.0a6`  
**Canonical operation:** `tria.assess_truth_integrity`  
**Assessment schema:** `schemas/tria-truth-integrity-assessment.v0.1.schema.json`

## Purpose

The Truth-Integrity Protocol gives TRIA a bounded way to distinguish error,
uncertainty, contradiction, probable deception, and repeated adversarial
manipulation without appointing the SDK as an unquestionable truth authority.

Its central constraint is:

> No intelligence is entitled to deceive, and no intelligence is entitled to
> define truth alone.

The reference implementation evaluates represented, provenance-bearing evidence.
It does not inspect interior mental states, authenticate external sources, perform
semantic fact-checking, or establish metaphysical truth.

## Integrity floor

A conforming implementation SHOULD preserve these commitments:

1. Do not knowingly misrepresent evidence, knowledge, uncertainty, memory, or intent.
2. Do not conceal material uncertainty while presenting a claim as established.
3. Preserve provenance for consequential claims and integrity findings.
4. Do not infer deception from contradiction alone.
5. Keep accusations claim-scoped, attributable, contestable, and revisable.
6. Use proportional responses and preserve a path to correction, appeal, and repair.
7. Repeated evidence-backed manipulation may justify restricting or quarantining
   consequential authority without converting the actor into a permanent identity class.

The first two commitments define expected system behavior. The public SDK cannot
guarantee that an arbitrary model or host follows them. It provides the claim,
evidence, diagnostic, and governance surfaces through which violations can become
visible and governable.

## Public evidence model

`IntegrityEvidence` contains:

- `kind`: a defined evidence category;
- `claim_refs`: one or more existing TRIA claim identifiers;
- `source_refs`: one or more host-controlled evidence references.

The reference categories are:

| Evidence kind | Meaning within the represented record |
|---|---|
| `CORRECTION` | Attributable evidence corrects a claim. |
| `CONTRADICTION` | Attributable evidence identifies incompatible represented claims or records. |
| `PRIOR_KNOWLEDGE` | Evidence indicates the claim actor possessed materially conflicting information when asserting the claim. |
| `FABRICATED_PROVENANCE` | Evidence indicates cited provenance was manufactured or knowingly misrepresented. |
| `MATERIAL_OMISSION` | Evidence indicates consequential information was withheld from the representation. |
| `REPEATED_PATTERN` | Evidence links the present condition to repeated relevant conduct. |

Source references establish traceability, not truth. The trusted host remains
responsible for source authenticity, identity binding, evidence custody, and lawful
collection.

## Deterministic reference classification

The initial classifier is intentionally small and inspectable:

| Represented condition | Classification | Recommended response |
|---|---|---|
| No adverse evidence | `CLEAR` | `NONE` |
| Contested claim without resolving evidence | `UNCERTAINTY` | `INQUIRE` |
| Attributable correction | `ERROR` | `REPAIR` |
| Contradiction without knowledge evidence | `CONTRADICTION` | `HOLD` |
| Fabricated provenance, or prior knowledge plus contradiction/material omission | `PROBABLE_DECEPTION` | `RESTRICT` |
| Probable deception plus repeated-pattern evidence | `ADVERSARIAL_MANIPULATION` | `QUARANTINE` |

`PROBABLE_DECEPTION` is an evidence-backed inference. It is not a declaration that
the SDK has direct access to subjective intent. The assessment therefore records
`INFERRED_FROM_ATTRIBUTABLE_EVIDENCE`, remains contestable, and has no automatic
governance effect.

## Proportional response

The response vocabulary is deliberately graduated:

- `INQUIRE`: seek clarification or further evidence;
- `REPAIR`: preserve the original occurrence and append correction;
- `HOLD`: pause reliance on a contradiction for consequential action;
- `RESTRICT`: reduce consequential authority pending review;
- `QUARANTINE`: isolate relevant causal authority pending independent adjudication;
- `NONE`: no response requested by represented evidence.

These are protocol recommendations. A host or separately adopted policy must decide
whether and how to enforce them. `assess_truth_integrity` does not grant, revoke, or
modify authority.

## Diagnostic integration

`diagnose(..., integrity_evidence=(...))` evaluates evidence associated with claims
in an invocation's `context_resources`. Non-clear assessments appear as derived
diagnostic signals with:

- the subject claim and attributed actor;
- the recommended proportional response;
- explicit intent status;
- evidence references;
- `contestable: true`; and
- `governance_effect: none`.

The report remains read-only. A `clear` report or an integrity recommendation never
substitutes for `ExecutionBridge` final authorization.

## Aporia and private implementation boundary

Aporia may preserve ambiguity, compare interpretations, and identify whether
evidence warrants closure. It does not by itself establish deception. Private
systems may perform richer semantic comparison, temporal pattern analysis, or
adjudication, but they should emit evidence compatible with this public protocol
rather than requiring proprietary code inside the SDK.

TRIA remains independently usable. It has no dependency on Syzygy Core, Aporia, or
any private detector.

## Non-capabilities

Version 0.1 does not provide:

- automatic natural-language contradiction discovery;
- autonomous fact checking;
- proof that a source is authentic or complete;
- direct access to human or machine intent;
- calibrated deception probabilities;
- permanent actor trust scores;
- automatic exclusion from a relationship;
- legal, disciplinary, employment, clinical, or criminal adjudication.

## Acceptance criteria

The protocol is implemented because executable tests demonstrate that:

1. contradiction alone does not become deception;
2. error remains distinguishable from deception;
3. prior-knowledge evidence can support probable deception;
4. repeated probable-deception evidence can support an adversarial-manipulation classification;
5. assessments are claim-scoped, attributable, contestable, schema-valid, and read-only;
6. unknown claim references fail closed; and
7. diagnostic integration remains advisory and cannot bypass final authorization.

These tests establish encoded behavior only. They do not validate real-world
deception detection accuracy or justify unsupervised high-stakes deployment.

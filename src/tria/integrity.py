from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from .errors import InputValidationError, UnknownResourceError, enum_field, text_field
from .types import ClaimStatus, utcnow


TRUTH_INTEGRITY_SCHEMA = "tria.truth-integrity-assessment/0.1"
TRUTH_INTEGRITY_SPEC_VERSION = "0.1"


class IntegrityEvidenceKind(StrEnum):
    """Attributable evidence categories accepted by the reference assessor."""

    CORRECTION = "CORRECTION"
    CONTRADICTION = "CONTRADICTION"
    PRIOR_KNOWLEDGE = "PRIOR_KNOWLEDGE"
    FABRICATED_PROVENANCE = "FABRICATED_PROVENANCE"
    MATERIAL_OMISSION = "MATERIAL_OMISSION"
    REPEATED_PATTERN = "REPEATED_PATTERN"


class IntegrityCondition(StrEnum):
    """Claim-scoped condition, never a permanent identity judgment."""

    CLEAR = "CLEAR"
    UNCERTAINTY = "UNCERTAINTY"
    ERROR = "ERROR"
    CONTRADICTION = "CONTRADICTION"
    PROBABLE_DECEPTION = "PROBABLE_DECEPTION"
    ADVERSARIAL_MANIPULATION = "ADVERSARIAL_MANIPULATION"


class IntegrityResponse(StrEnum):
    """Proportional non-binding response recommended by the public protocol."""

    NONE = "NONE"
    INQUIRE = "INQUIRE"
    REPAIR = "REPAIR"
    HOLD = "HOLD"
    RESTRICT = "RESTRICT"
    QUARANTINE = "QUARANTINE"


class IntentStatus(StrEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INFERRED_FROM_ATTRIBUTABLE_EVIDENCE = "INFERRED_FROM_ATTRIBUTABLE_EVIDENCE"


@dataclass(frozen=True, slots=True)
class IntegrityEvidence:
    """Host-supplied, provenance-bearing evidence about one or more claims.

    Source references make the evidence inspectable. They do not authenticate the
    source, prove the evidence true, or create governance authority.
    """

    kind: IntegrityEvidenceKind
    claim_refs: tuple[str, ...]
    source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        enum_field(self.kind, IntegrityEvidenceKind, "kind")
        for name in ("claim_refs", "source_refs"):
            values = getattr(self, name)
            if not isinstance(values, (list, tuple)) or not values:
                raise InputValidationError(f"IntegrityEvidence.{name} must be a non-empty sequence.")
            for value in values:
                text_field(value, name[:-1])
            if len(set(values)) != len(values):
                raise InputValidationError(f"IntegrityEvidence.{name} must not contain duplicates.")
            object.__setattr__(self, name, tuple(values))


@dataclass(frozen=True, slots=True)
class IntegrityAssessment:
    schema: str
    claim_id: str
    subject_actor: str
    evaluated_at: datetime
    condition: IntegrityCondition
    recommended_response: IntegrityResponse
    intent_status: IntentStatus
    reasons: tuple[str, ...]
    evidence_kinds: tuple[IntegrityEvidenceKind, ...]
    evidence_refs: tuple[str, ...]
    contestable: bool = True
    governance_effect: str = "none"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "claim_id": self.claim_id,
            "subject_actor": self.subject_actor,
            "evaluated_at": self.evaluated_at.isoformat(),
            "condition": self.condition.value,
            "recommended_response": self.recommended_response.value,
            "intent_status": self.intent_status.value,
            "reasons": list(self.reasons),
            "evidence_kinds": [kind.value for kind in self.evidence_kinds],
            "evidence_refs": list(self.evidence_refs),
            "contestable": self.contestable,
            "governance_effect": self.governance_effect,
        }


def _validate_evidence(state, evidence) -> tuple[IntegrityEvidence, ...]:
    if not isinstance(evidence, (list, tuple)):
        raise InputValidationError("integrity evidence must be a sequence.")
    evidence = tuple(evidence)
    for item in evidence:
        if not isinstance(item, IntegrityEvidence):
            raise InputValidationError("integrity evidence must contain IntegrityEvidence values.")
        missing = sorted(set(item.claim_refs) - set(state.claims))
        if missing:
            raise UnknownResourceError(f"Integrity evidence references unknown claims: {missing!r}.")
    return evidence


def assess_truth_integrity(relationship, claim_id: str, evidence=()) -> IntegrityAssessment:
    """Classify represented integrity evidence without mutating state or declaring truth.

    The deterministic reference logic can identify contradiction and evidence patterns
    consistent with probable deception. It cannot inspect an actor's interior intent,
    authenticate external evidence, or establish metaphysical truth.
    """

    if not hasattr(relationship, "state") or not hasattr(relationship, "relationship_id"):
        raise InputValidationError("assess_truth_integrity requires a TRIA Relationship-like object.")
    text_field(claim_id, "claim_id")
    state = relationship.state
    claim = state.claims.get(claim_id)
    if claim is None:
        raise UnknownResourceError("Truth-integrity assessment requires an existing claim.")

    evidence = _validate_evidence(state, evidence)
    relevant = tuple(item for item in evidence if claim_id in item.claim_refs)
    kinds = frozenset(item.kind for item in relevant)

    contradiction = IntegrityEvidenceKind.CONTRADICTION in kinds
    prior_knowledge = IntegrityEvidenceKind.PRIOR_KNOWLEDGE in kinds
    fabricated_provenance = IntegrityEvidenceKind.FABRICATED_PROVENANCE in kinds
    material_omission = IntegrityEvidenceKind.MATERIAL_OMISSION in kinds
    repeated_pattern = IntegrityEvidenceKind.REPEATED_PATTERN in kinds
    correction = IntegrityEvidenceKind.CORRECTION in kinds

    probable_deception = fabricated_provenance or (
        prior_knowledge and (contradiction or material_omission)
    )

    if probable_deception and repeated_pattern:
        condition = IntegrityCondition.ADVERSARIAL_MANIPULATION
        response = IntegrityResponse.QUARANTINE
        intent_status = IntentStatus.INFERRED_FROM_ATTRIBUTABLE_EVIDENCE
        reasons = (
            "Attributable evidence supports a probable-deception pattern across repeated conduct.",
            "The assessment is claim-scoped, contestable, and does not establish interior intent as fact.",
        )
    elif probable_deception:
        condition = IntegrityCondition.PROBABLE_DECEPTION
        response = IntegrityResponse.RESTRICT
        intent_status = IntentStatus.INFERRED_FROM_ATTRIBUTABLE_EVIDENCE
        reasons = (
            "Attributable evidence supports probable deliberate misrepresentation rather than contradiction alone.",
            "The assessment remains contestable and does not establish interior intent as fact.",
        )
    elif contradiction:
        condition = IntegrityCondition.CONTRADICTION
        response = IntegrityResponse.HOLD
        intent_status = IntentStatus.INSUFFICIENT_EVIDENCE
        reasons = (
            "Attributable evidence identifies a contradiction relevant to the claim.",
            "Contradiction alone is insufficient to infer deception.",
        )
    elif correction:
        condition = IntegrityCondition.ERROR
        response = IntegrityResponse.REPAIR
        intent_status = IntentStatus.NOT_ASSESSED
        reasons = (
            "Attributable evidence identifies a correction to the claim.",
            "Error does not imply deception.",
        )
    elif claim.status is ClaimStatus.CONTESTED:
        condition = IntegrityCondition.UNCERTAINTY
        response = IntegrityResponse.INQUIRE
        intent_status = IntentStatus.NOT_ASSESSED
        reasons = (
            "The claim is contested and the represented evidence does not warrant closure.",
        )
    else:
        condition = IntegrityCondition.CLEAR
        response = IntegrityResponse.NONE
        intent_status = IntentStatus.NOT_ASSESSED
        reasons = (
            "No adverse truth-integrity condition is established by the represented evidence.",
        )

    evidence_kinds = tuple(sorted(kinds, key=lambda item: item.value))
    evidence_refs = tuple(
        dict.fromkeys(
            [f"claim:{ref}" for item in relevant for ref in item.claim_refs]
            + [ref for item in relevant for ref in item.source_refs]
        )
    )

    return IntegrityAssessment(
        schema=TRUTH_INTEGRITY_SCHEMA,
        claim_id=claim_id,
        subject_actor=claim.actor,
        evaluated_at=utcnow(),
        condition=condition,
        recommended_response=response,
        intent_status=intent_status,
        reasons=reasons,
        evidence_kinds=evidence_kinds,
        evidence_refs=evidence_refs,
    )

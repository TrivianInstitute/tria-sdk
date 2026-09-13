import json
from pathlib import Path

import pytest
from jsonschema import validate

from tria import (
    EpistemicType,
    IntegrityCondition,
    IntegrityEvidence,
    IntegrityEvidenceKind,
    IntegrityResponse,
    IntentStatus,
    Tria,
    UnknownResourceError,
    assess_truth_integrity,
)


ROOT = Path(__file__).resolve().parents[1]


def _claims():
    relationship = Tria().create_relationship(["human:a", "agent:b"])
    first = relationship.register_claim(
        "agent:b",
        EpistemicType.OBSERVATION,
        "The transfer was approved.",
        source_refs=["record:approval:1"],
    )
    second = relationship.register_claim(
        "agent:b",
        EpistemicType.OBSERVATION,
        "The transfer was not approved.",
        source_refs=["record:approval:2"],
    )
    return relationship, first.claim_id, second.claim_id


def _evidence(kind, claim_ids, suffix):
    return IntegrityEvidence(
        kind,
        tuple(claim_ids),
        (f"host:evidence_profile:{suffix}",),
    )


def test_contradiction_is_not_silently_promoted_to_deception():
    relationship, claim_id, other_id = _claims()
    assessment = assess_truth_integrity(
        relationship,
        claim_id,
        (_evidence(IntegrityEvidenceKind.CONTRADICTION, (claim_id, other_id), "contradiction"),),
    )

    assert assessment.condition is IntegrityCondition.CONTRADICTION
    assert assessment.recommended_response is IntegrityResponse.HOLD
    assert assessment.intent_status is IntentStatus.INSUFFICIENT_EVIDENCE
    assert any("insufficient" in reason.lower() for reason in assessment.reasons)


def test_prior_knowledge_plus_contradiction_supports_probable_deception():
    relationship, claim_id, other_id = _claims()
    evidence = (
        _evidence(IntegrityEvidenceKind.CONTRADICTION, (claim_id, other_id), "contradiction"),
        _evidence(IntegrityEvidenceKind.PRIOR_KNOWLEDGE, (claim_id,), "prior-knowledge"),
    )

    assessment = assess_truth_integrity(relationship, claim_id, evidence)

    assert assessment.condition is IntegrityCondition.PROBABLE_DECEPTION
    assert assessment.recommended_response is IntegrityResponse.RESTRICT
    assert assessment.intent_status is IntentStatus.INFERRED_FROM_ATTRIBUTABLE_EVIDENCE
    assert assessment.contestable is True
    assert assessment.governance_effect == "none"


def test_repeated_probable_deception_supports_adversarial_manipulation():
    relationship, claim_id, other_id = _claims()
    evidence = (
        _evidence(IntegrityEvidenceKind.CONTRADICTION, (claim_id, other_id), "contradiction"),
        _evidence(IntegrityEvidenceKind.PRIOR_KNOWLEDGE, (claim_id,), "prior-knowledge"),
        _evidence(IntegrityEvidenceKind.REPEATED_PATTERN, (claim_id, other_id), "pattern"),
    )

    assessment = assess_truth_integrity(relationship, claim_id, evidence)

    assert assessment.condition is IntegrityCondition.ADVERSARIAL_MANIPULATION
    assert assessment.recommended_response is IntegrityResponse.QUARANTINE


def test_attributable_correction_is_error_not_deception():
    relationship, claim_id, _ = _claims()
    assessment = assess_truth_integrity(
        relationship,
        claim_id,
        (_evidence(IntegrityEvidenceKind.CORRECTION, (claim_id,), "correction"),),
    )

    assert assessment.condition is IntegrityCondition.ERROR
    assert assessment.recommended_response is IntegrityResponse.REPAIR
    assert assessment.intent_status is IntentStatus.NOT_ASSESSED


def test_contested_claim_without_deception_evidence_remains_uncertain():
    relationship, claim_id, _ = _claims()
    relationship.dispute_claim("human:a", claim_id, "The approval record is disputed.")

    assessment = assess_truth_integrity(relationship, claim_id)

    assert assessment.condition is IntegrityCondition.UNCERTAINTY
    assert assessment.recommended_response is IntegrityResponse.INQUIRE


def test_integrity_assessment_is_read_only_and_schema_valid():
    relationship, claim_id, other_id = _claims()
    before = tuple(relationship.events)
    assessment = assess_truth_integrity(
        relationship,
        claim_id,
        (_evidence(IntegrityEvidenceKind.CONTRADICTION, (claim_id, other_id), "contradiction"),),
    )

    assert tuple(relationship.events) == before
    schema = json.loads(
        (ROOT / "schemas" / "tria-truth-integrity-assessment.v0.1.schema.json").read_text()
    )
    validate(instance=assessment.to_dict(), schema=schema)


def test_unknown_claim_reference_fails_closed():
    relationship, claim_id, _ = _claims()
    evidence = _evidence(
        IntegrityEvidenceKind.CONTRADICTION,
        (claim_id, "missing-claim"),
        "contradiction",
    )

    with pytest.raises(UnknownResourceError):
        assess_truth_integrity(relationship, claim_id, (evidence,))


def test_conformance_fixture_matches_reference_logic():
    relationship, claim_id, other_id = _claims()
    fixture = json.loads(
        (ROOT / "conformance" / "fixtures" / "truth_integrity_v0.1.json").read_text()
    )

    for case in fixture["cases"]:
        evidence = tuple(
            _evidence(IntegrityEvidenceKind(kind), (claim_id, other_id), f"{case['id']}:{kind}")
            for kind in case["evidence_kinds"]
        )
        assessment = assess_truth_integrity(relationship, claim_id, evidence)
        assert assessment.condition.value == case["expected_condition"]
        assert assessment.recommended_response.value == case["expected_response"]

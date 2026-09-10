import json
from pathlib import Path

from jsonschema import validate

from tria import (
    AttributableObservation,
    Capability,
    ConsentRequirement,
    EpistemicType,
    ExecutionBridge,
    InvocationRequest,
    OpenAIResponsesAdapter,
    Tria,
    diagnose,
)


def _clean_relationship():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    claim = rel.register_claim(
        "human:a",
        EpistemicType.OBSERVATION,
        "The participant selected option A.",
        source_refs=["ui:selection:1"],
    )
    resource = f"claim:{claim.claim_id}"
    rel.grant_permission("human:a", "agent:b", resource, Capability.READ)
    request = InvocationRequest(
        requested_by="agent:b",
        action="Use the selected option.",
        target="executor:any",
        context_resources=(resource,),
    )
    observations = (
        AttributableObservation("host_authentication", True, ("host:auth:1",)),
        AttributableObservation("external_authority_current", True, ("host:intent:1",)),
        AttributableObservation("reversibility", True, ("host:recovery:1",)),
    )
    return rel, claim, resource, request, observations


def test_diagnose_is_read_only_and_can_return_clear():
    rel, _, _, request, observations = _clean_relationship()
    before = tuple(rel.events)

    report = diagnose(rel, request, observations)

    assert report.summary == "clear"
    assert tuple(rel.events) == before
    assert report.request_id == request.request_id
    assert report.relationship_id == rel.relationship_id
    assert report.provenance["diagnostic_spec"] == "0.1"


def test_diagnose_preserves_block_from_runtime_evaluation():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    claim = rel.register_claim(
        "human:a",
        EpistemicType.OBSERVATION,
        "Private observation.",
        source_refs=["sensor:1"],
    )
    request = InvocationRequest(
        requested_by="agent:b",
        action="Use private observation.",
        target="executor:any",
        context_resources=(f"claim:{claim.claim_id}",),
    )

    report = diagnose(rel, request)

    assert report.summary == "blocked"
    assert any(item["outcome"] == "BLOCK" for item in report.governance_findings)


def test_diagnose_preserves_require_consent_as_distinct_outcome():
    rel, _, _, request, observations = _clean_relationship()
    request = InvocationRequest(
        requested_by=request.requested_by,
        action=request.action,
        target=request.target,
        context_resources=request.context_resources,
        consent_requirements=(ConsentRequirement("human:a", "persistent_context"),),
    )

    report = diagnose(rel, request, observations)

    assert report.summary == "consent_required"
    assert any(item["outcome"] == "REQUIRE_CONSENT" for item in report.governance_findings)


def test_contested_claim_surfaces_as_advisory_signal_without_new_authority():
    rel, claim, _, request, observations = _clean_relationship()
    rel.dispute_claim("human:a", claim.claim_id, "The selection may have been accidental.")
    before = tuple(rel.events)

    report = diagnose(rel, request, observations)

    assert report.summary == "review"
    signal = next(item for item in report.diagnostic_signals if item["signal_type"] == "contested_claim_in_context")
    assert signal["evidence_class"] == "derived"
    assert signal["governance_effect"] == "none"
    assert tuple(rel.events) == before


def test_missing_external_evidence_is_reported_as_unknown_not_guessed():
    rel, _, _, request, _ = _clean_relationship()

    report = diagnose(rel, request)
    unknown_types = {item["unknown_type"] for item in report.unknowns}

    assert report.summary == "review"
    assert "host_authentication_unverified" in unknown_types
    assert "external_authority_freshness_unverified" in unknown_types
    assert "reversibility_unverified" in unknown_types


def test_report_validates_against_canonical_schema():
    rel, _, _, request, observations = _clean_relationship()
    report = diagnose(rel, request, observations).to_dict()
    schema_path = Path(__file__).parents[1] / "schemas" / "tria-diagnostic-report.v0.1.schema.json"
    schema = json.loads(schema_path.read_text())

    validate(instance=report, schema=schema)


def test_clear_diagnostic_does_not_bypass_final_execution_reauthorization():
    rel, _, resource, request, observations = _clean_relationship()
    report = diagnose(rel, request, observations)
    assert report.summary == "clear"

    rel.revoke_permission("human:a", "agent:b", resource, Capability.READ)
    called = False

    def fake_executor(provider_request):
        nonlocal called
        called = True
        return {"id": "must-not-run", "status": "completed"}

    receipt = ExecutionBridge().execute(
        rel,
        request,
        OpenAIResponsesAdapter(),
        fake_executor,
        model="example-model",
    )

    assert receipt.executed is False
    assert called is False

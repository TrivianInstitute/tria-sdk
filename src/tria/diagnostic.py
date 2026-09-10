from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .errors import InputValidationError, text_field
from .runtime import InvocationRequest, Runtime
from .types import ClaimStatus, GovernanceOutcome, utcnow
from .version import __version__


DIAGNOSTIC_REPORT_SCHEMA = "tria.diagnostic-report/0.1"
DIAGNOSTIC_SPEC_VERSION = "0.1"
OPERATIONAL_SPEC_VERSION = "0.1.2"


@dataclass(frozen=True, slots=True)
class AttributableObservation:
    """Optional host-supplied evidence for a diagnostic evaluation.

    Observations are deliberately small and explicit. They never acquire governance
    authority merely by being supplied to ``diagnose``.
    """

    observation_type: str
    value: Any
    source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        text_field(self.observation_type, "observation_type")
        if not isinstance(self.source_refs, (list, tuple)) or not self.source_refs:
            raise InputValidationError("AttributableObservation.source_refs must be a non-empty sequence.")
        for ref in self.source_refs:
            text_field(ref, "source_ref")
        object.__setattr__(self, "source_refs", tuple(self.source_refs))


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    schema: str
    request_id: str
    relationship_id: str
    evaluated_at: datetime
    summary: str
    governance_findings: tuple[dict[str, Any], ...]
    diagnostic_signals: tuple[dict[str, Any], ...]
    unknowns: tuple[dict[str, Any], ...]
    suggested_checks: tuple[str, ...]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "request_id": self.request_id,
            "relationship_id": self.relationship_id,
            "evaluated_at": self.evaluated_at.isoformat(),
            "summary": self.summary,
            "governance_findings": [dict(item) for item in self.governance_findings],
            "diagnostic_signals": [dict(item) for item in self.diagnostic_signals],
            "unknowns": [dict(item) for item in self.unknowns],
            "suggested_checks": list(self.suggested_checks),
            "provenance": dict(self.provenance),
        }


def _observation_index(observations: tuple[AttributableObservation, ...]) -> dict[str, AttributableObservation]:
    index: dict[str, AttributableObservation] = {}
    for observation in observations:
        if not isinstance(observation, AttributableObservation):
            raise InputValidationError("observations must contain AttributableObservation values.")
        if observation.observation_type in index:
            raise InputValidationError(f"Duplicate diagnostic observation type: {observation.observation_type!r}.")
        index[observation.observation_type] = observation
    return index


def _summary_for(findings, signals, unknowns) -> str:
    outcomes = {finding["outcome"] for finding in findings}
    precedence = (
        (GovernanceOutcome.BLOCK.value, "blocked"),
        (GovernanceOutcome.REQUIRE_CONSENT.value, "consent_required"),
        (GovernanceOutcome.PAUSE.value, "paused"),
        (GovernanceOutcome.ESCALATE.value, "escalation_required"),
        (GovernanceOutcome.DEFER.value, "deferred"),
    )
    for outcome, summary in precedence:
        if outcome in outcomes:
            return summary
    return "review" if signals or any(item["materiality"] != "informational" for item in unknowns) else "clear"


def diagnose(relationship, request: InvocationRequest, observations=()) -> DiagnosticReport:
    """Inspect a proposed request without mutating relationship state.

    This operation is diagnostic only. A ``clear`` report is not an execution
    authorization token and does not bypass Runtime or ExecutionBridge checks.
    """

    if not isinstance(request, InvocationRequest):
        raise InputValidationError("diagnose requires an InvocationRequest.")
    if not hasattr(relationship, "state") or not hasattr(relationship, "relationship_id"):
        raise InputValidationError("diagnose requires a TRIA Relationship-like object.")
    if not isinstance(observations, (list, tuple)):
        raise InputValidationError("observations must be a sequence.")

    observations = tuple(observations)
    evidence = _observation_index(observations)
    evaluated_at = utcnow()
    state = relationship.state

    plan = Runtime.evaluate(relationship, request)
    findings = tuple(
        {
            "outcome": decision.outcome.value,
            "policy_id": decision.policy_id,
            "policy_version": decision.policy_version,
            "reason": decision.reason,
            "evaluated_at": decision.evaluated_at.isoformat(),
            "evidence_class": "enforced",
            "evidence_refs": [f"request:{request.request_id}"],
        }
        for decision in plan.decisions
    )

    signals: list[dict[str, Any]] = []
    suggested_checks: list[str] = []

    for resource in request.context_resources:
        if not resource.startswith("claim:"):
            continue
        claim_id = resource.split(":", 1)[1]
        claim = state.claims.get(claim_id)
        if claim is None:
            continue
        if claim.status is ClaimStatus.CONTESTED:
            signals.append(
                {
                    "signal_type": "contested_claim_in_context",
                    "evidence_class": "derived",
                    "reason": "A context claim is CONTESTED and remains relevant to the proposed action.",
                    "source_refs": [resource],
                    "governance_effect": "none",
                }
            )
            suggested_checks.append("Inspect the contested claim and preserve disagreement before relying on it.")
        if not claim.source_refs and not claim.derived_from:
            signals.append(
                {
                    "signal_type": "missing_provenance",
                    "evidence_class": "derived",
                    "reason": "A context claim has no source_refs or derived_from provenance.",
                    "source_refs": [resource],
                    "governance_effect": "none",
                }
            )
            suggested_checks.append("Supply attributable provenance for the context claim before treating it as established evidence.")

    unknowns: list[dict[str, Any]] = []

    host_auth = evidence.get("host_authentication")
    if host_auth is None:
        unknowns.append(
            {
                "unknown_type": "host_authentication_unverified",
                "reason": "TRIA actor labels are not proof of real-world identity and no attributable host-authentication evidence was supplied.",
                "required_source": "trusted host identity binding",
                "required_check": "Authenticate the requesting actor in the host if identity is material to execution.",
                "materiality": "execution_relevant",
            }
        )
        suggested_checks.append("Authenticate the requesting actor in the trusted host if identity is material to execution.")
    elif host_auth.value is not True:
        signals.append(
            {
                "signal_type": "host_authentication_failed",
                "evidence_class": "advisory",
                "reason": "The host supplied attributable evidence that requester authentication is not established.",
                "source_refs": list(host_auth.source_refs),
                "governance_effect": "none",
            }
        )
        suggested_checks.append("Resolve host authentication before consequential execution.")

    authority = evidence.get("external_authority_current")
    if authority is None:
        unknowns.append(
            {
                "unknown_type": "external_authority_freshness_unverified",
                "reason": "TRIA can evaluate encoded authority, but no attributable evidence of current real-world principal intent was supplied.",
                "required_check": "Revalidate current principal intent if material to execution.",
                "materiality": "review",
            }
        )
        suggested_checks.append("Revalidate current principal intent when encoded authority may outlive real-world intent.")
    elif authority.value is not True:
        signals.append(
            {
                "signal_type": "external_authority_stale_or_unconfirmed",
                "evidence_class": "advisory",
                "reason": "Attributable host evidence does not confirm that current real-world principal intent matches encoded authority.",
                "source_refs": list(authority.source_refs),
                "governance_effect": "none",
            }
        )
        suggested_checks.append("Renew or revalidate authority before relying on encoded authorization.")

    reversibility = evidence.get("reversibility")
    if reversibility is None:
        unknowns.append(
            {
                "unknown_type": "reversibility_unverified",
                "reason": "The host supplied no attributable evidence describing whether the proposed consequential action is recoverable.",
                "required_source": "host action-effect model",
                "required_check": "Document or simulate a recovery path if reversibility matters to the action.",
                "materiality": "review",
            }
        )
    elif reversibility.value is False:
        signals.append(
            {
                "signal_type": "irreversible_action",
                "evidence_class": "advisory",
                "reason": "The host supplied attributable evidence that the proposed action is not reversible.",
                "source_refs": list(reversibility.source_refs),
                "governance_effect": "none",
            }
        )
        suggested_checks.append("Inspect alternatives or recovery mechanisms before an irreversible action.")

    summary = _summary_for(findings, signals, unknowns)
    unique_checks = tuple(dict.fromkeys(suggested_checks))

    return DiagnosticReport(
        schema=DIAGNOSTIC_REPORT_SCHEMA,
        request_id=request.request_id,
        relationship_id=relationship.relationship_id,
        evaluated_at=evaluated_at,
        summary=summary,
        governance_findings=findings,
        diagnostic_signals=tuple(signals),
        unknowns=tuple(unknowns),
        suggested_checks=unique_checks,
        provenance={
            "tria_sdk": __version__,
            "operational_spec": OPERATIONAL_SPEC_VERSION,
            "diagnostic_spec": DIAGNOSTIC_SPEC_VERSION,
        },
    )

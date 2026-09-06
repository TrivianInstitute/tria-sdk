import json

import pytest

from tria import Tria
from tria.differentiation import (
    DifferentiationObservation,
    GenerativeCondition,
    assess_generative_condition,
    record_differentiation_observation,
)


def observation(**overrides):
    values = dict(
        constraint_diversity=0.8,
        representational_diversity=0.8,
        attractor_concentration=0.2,
        orthogonal_reserve=0.8,
        novelty_velocity=0.8,
        temporal_mode_diversity=0.8,
    )
    values.update(overrides)
    return DifferentiationObservation(**values)


def test_high_coherence_low_difference_is_crystallization_risk():
    result = assess_generative_condition(
        coherence=0.9,
        observation=observation(orthogonal_reserve=0.1),
        coherence_floor=0.6,
        differentiation_floor=0.4,
    )
    assert result is GenerativeCondition.CRYSTALLIZATION_RISK


def test_observation_is_recorded_as_attributable_claim_not_governance_fact():
    rel = Tria().create_relationship(["human:user", "agent:demo"])
    handle = record_differentiation_observation(
        rel,
        observer="agent:demo",
        observation=observation(),
        source_refs=("orthogonal-signal:run-1",),
    )
    claim = rel.state.claims[handle.claim_id]
    payload = json.loads(claim.content)
    assert payload["kind"] == "tria.generative_differentiation"
    assert claim.actor == "agent:demo"
    assert claim.source_refs == ("orthogonal-signal:run-1",)


def test_observation_requires_provenance():
    rel = Tria().create_relationship(["human:user", "agent:demo"])
    with pytest.raises(ValueError):
        record_differentiation_observation(
            rel,
            observer="agent:demo",
            observation=observation(),
            source_refs=(),
        )


def test_non_compensatory_floor_preserves_single_dimension_collapse():
    assert observation(novelty_velocity=0.05).preservation_floor == pytest.approx(0.05)

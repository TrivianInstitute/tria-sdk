"""Experimental Generative Differentiation developer surface.

This module exposes provenance-bearing observations and a transparent quadrant
assessment. It does not create a mandatory safety score or automatically grant
its interpretation governance authority.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
import json

from .types import EpistemicType


class GenerativeCondition(str, Enum):
    GENERATIVE_COHERENCE = "generative_coherence"
    CRYSTALLIZATION_RISK = "crystallization_risk"
    FRAGMENTATION_RISK = "fragmentation_risk"
    COLLAPSE_OR_STAGNATION_RISK = "collapse_or_stagnation_risk"


@dataclass(frozen=True, slots=True)
class DifferentiationObservation:
    constraint_diversity: float
    representational_diversity: float
    attractor_concentration: float
    orthogonal_reserve: float
    novelty_velocity: float
    temporal_mode_diversity: float

    def __post_init__(self) -> None:
        for name in (
            "constraint_diversity",
            "representational_diversity",
            "attractor_concentration",
            "orthogonal_reserve",
            "novelty_velocity",
            "temporal_mode_diversity",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0.0, 1.0]")

    @property
    def preservation_floor(self) -> float:
        return min(
            self.constraint_diversity,
            self.representational_diversity,
            1.0 - self.attractor_concentration,
            self.orthogonal_reserve,
            self.novelty_velocity,
            self.temporal_mode_diversity,
        )


def assess_generative_condition(
    *,
    coherence: float,
    observation: DifferentiationObservation,
    coherence_floor: float,
    differentiation_floor: float,
) -> GenerativeCondition:
    for name, value in (
        ("coherence", coherence),
        ("coherence_floor", coherence_floor),
        ("differentiation_floor", differentiation_floor),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0.0, 1.0]")

    coherent = coherence >= coherence_floor
    differentiated = observation.preservation_floor >= differentiation_floor
    if coherent and differentiated:
        return GenerativeCondition.GENERATIVE_COHERENCE
    if coherent and not differentiated:
        return GenerativeCondition.CRYSTALLIZATION_RISK
    if not coherent and differentiated:
        return GenerativeCondition.FRAGMENTATION_RISK
    return GenerativeCondition.COLLAPSE_OR_STAGNATION_RISK


def record_differentiation_observation(
    relationship,
    *,
    observer: str,
    observation: DifferentiationObservation,
    source_refs: tuple[str, ...],
):
    """Record an attributable, contestable observation using TRIA's claim ledger.

    The observation remains an OBSERVATION claim. Any convergence interpretation
    should be recorded separately so measurement is not silently promoted into
    relational fact.
    """
    if not source_refs:
        raise ValueError("source_refs are required for differentiation observations")
    content = json.dumps(
        {"kind": "tria.generative_differentiation", **asdict(observation)},
        sort_keys=True,
        separators=(",", ":"),
    )
    return relationship.register_claim(
        observer,
        EpistemicType.OBSERVATION,
        content,
        source_refs=list(source_refs),
    )

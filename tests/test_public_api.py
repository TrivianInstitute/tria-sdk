from tria import (
    AttributableObservation,
    DiagnosticReport,
    ExecutionBridge,
    IntegrityAssessment,
    IntegrityEvidence,
    Runtime,
    Tria,
    __version__,
    assess_truth_integrity,
    diagnose,
)


def test_public_version_matches_alpha_release():
    assert __version__ == "0.1.0a6"


def test_primary_public_entrypoints_are_importable():
    assert Tria is not None
    assert Runtime is not None
    assert ExecutionBridge is not None
    assert diagnose is not None
    assert DiagnosticReport is not None
    assert AttributableObservation is not None
    assert IntegrityAssessment is not None
    assert IntegrityEvidence is not None
    assert assess_truth_integrity is not None

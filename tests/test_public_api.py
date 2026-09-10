from tria import (
    AttributableObservation,
    DiagnosticReport,
    ExecutionBridge,
    Runtime,
    Tria,
    __version__,
    diagnose,
)


def test_public_version_matches_alpha_release():
    assert __version__ == "0.1.0a5"


def test_primary_public_entrypoints_are_importable():
    assert Tria is not None
    assert Runtime is not None
    assert ExecutionBridge is not None
    assert diagnose is not None
    assert DiagnosticReport is not None
    assert AttributableObservation is not None

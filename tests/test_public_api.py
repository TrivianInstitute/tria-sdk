from tria import ExecutionBridge, Runtime, Tria, __version__


def test_public_version_matches_alpha_release():
    assert __version__ == "0.1.0a3"


def test_primary_public_entrypoints_are_importable():
    assert Tria is not None
    assert Runtime is not None
    assert ExecutionBridge is not None

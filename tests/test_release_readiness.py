from __future__ import annotations

import json
from pathlib import Path
import tomllib

import tria

ROOT = Path(__file__).resolve().parents[1]


def test_package_version_is_consistent_across_public_surfaces():
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]
    assert project["version"] == tria.__version__ == "0.1.0a3"
    readme = (ROOT / "README.md").read_text()
    changelog = (ROOT / "CHANGELOG.md").read_text()
    assert "`0.1.0a3`" in readme
    assert "## [0.1.0a3]" in changelog


def test_conformance_manifest_matches_runtime_compatibility_constants():
    manifest = json.loads((ROOT / "conformance" / "manifest.json").read_text())
    assert manifest["bundle_format_version"] == tria.BUNDLE_FORMAT_VERSION
    assert manifest["event_schema_version"] == tria.CURRENT_EVENT_SCHEMA_VERSION
    assert manifest["projection_version"] == tria.CURRENT_PROJECTION_VERSION


def test_documented_compatibility_envelope_matches_runtime():
    readme = (ROOT / "README.md").read_text()
    assert f"event schema: `{tria.CURRENT_EVENT_SCHEMA_VERSION}`" in readme
    assert f"projection: `{tria.CURRENT_PROJECTION_VERSION}`" in readme
    assert f"replay bundle: `{tria.BUNDLE_FORMAT_VERSION}`" in readme
    assert "Core specification: `0.1.1`" in readme


def test_every_manifest_fixture_exists_and_is_valid_json():
    manifest = json.loads((ROOT / "conformance" / "manifest.json").read_text())
    for relative in manifest["fixtures"]:
        path = ROOT / "conformance" / relative
        assert path.is_file(), f"Missing conformance fixture: {relative}"
        json.loads(path.read_text())


def test_release_schemas_exist_and_are_valid_json():
    required = {
        "consent_record.schema.json",
        "governance_decision.schema.json",
        "permission_record.schema.json",
        "relational_event.schema.json",
        "relational_state.schema.json",
        "replay-bundle.schema.json",
    }
    schema_dir = ROOT / "schemas"
    assert required.issubset({path.name for path in schema_dir.glob("*.json")})
    for name in required:
        json.loads((schema_dir / name).read_text())


def test_current_examples_include_governed_replay_export():
    example = ROOT / "examples" / "governed_replay_export.py"
    assert example.is_file()
    source = example.read_text()
    assert "Capability.DISCLOSE" in source
    assert 'actor="human:user"' in source


def test_completion_audit_exists_and_keeps_scope_bounded():
    audit = (ROOT / "docs" / "TRIA_V0.1_COMPLETION_AUDIT.md").read_text()
    assert "implementation-complete candidate" in audit
    assert "Explicitly out of scope" in audit
    assert "licensing" in audit.lower()


def test_release_candidate_keeps_license_decision_explicit():
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]
    assert project["license"]["text"] == "PolyForm-Noncommercial-1.0.0"
    readme = (ROOT / "README.md").read_text()
    license_text = (ROOT / "LICENSE.md").read_text()
    assert "PolyForm Noncommercial License 1.0.0" in readme
    assert "Commercial use is not permitted" in readme
    assert "PolyForm Noncommercial License 1.0.0" in license_text
    assert "Commercial use is not permitted" in license_text
    assert "SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0" in license_text

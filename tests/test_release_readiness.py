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


def test_conformance_manifest_matches_runtime_compatibility_constants():
    manifest = json.loads((ROOT / "conformance" / "manifest.json").read_text())
    assert manifest["bundle_format_version"] == tria.BUNDLE_FORMAT_VERSION
    assert manifest["event_schema_version"] == tria.CURRENT_EVENT_SCHEMA_VERSION
    assert manifest["projection_version"] == tria.CURRENT_PROJECTION_VERSION


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


def test_release_candidate_keeps_license_decision_explicit():
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]
    assert project["license"]["text"] == "AGPL-3.0-only"

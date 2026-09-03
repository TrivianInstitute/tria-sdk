from __future__ import annotations

from dataclasses import dataclass


CURRENT_EVENT_SCHEMA_VERSION = "0.1"
CURRENT_PROJECTION_VERSION = "0.4"
CURRENT_BUNDLE_FORMAT_VERSION = "0.1"

SUPPORTED_EVENT_SCHEMA_VERSIONS = frozenset({CURRENT_EVENT_SCHEMA_VERSION})
SUPPORTED_PROJECTION_VERSIONS = frozenset({CURRENT_PROJECTION_VERSION})
SUPPORTED_BUNDLE_FORMAT_VERSIONS = frozenset({CURRENT_BUNDLE_FORMAT_VERSION})


class SchemaCompatibilityError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CompatibilityReport:
    event_schema_version: str
    supported: bool
    projection_version: str | None = None
    bundle_format_version: str | None = None
    current_event_schema_version: str = CURRENT_EVENT_SCHEMA_VERSION
    current_projection_version: str = CURRENT_PROJECTION_VERSION
    current_bundle_format_version: str = CURRENT_BUNDLE_FORMAT_VERSION


def check_event_schema(version: str) -> CompatibilityReport:
    return CompatibilityReport(event_schema_version=version, supported=version in SUPPORTED_EVENT_SCHEMA_VERSIONS)


def check_compatibility(event_schema_version: str, *, projection_version: str | None = None, bundle_format_version: str | None = None) -> CompatibilityReport:
    supported = event_schema_version in SUPPORTED_EVENT_SCHEMA_VERSIONS
    if projection_version is not None:
        supported = supported and projection_version in SUPPORTED_PROJECTION_VERSIONS
    if bundle_format_version is not None:
        supported = supported and bundle_format_version in SUPPORTED_BUNDLE_FORMAT_VERSIONS
    return CompatibilityReport(event_schema_version=event_schema_version, projection_version=projection_version, bundle_format_version=bundle_format_version, supported=supported)


def require_supported_event_schema(version: str) -> None:
    report = check_event_schema(version)
    if not report.supported:
        raise SchemaCompatibilityError(f"Unsupported relational event schema {version!r}; supported versions: {sorted(SUPPORTED_EVENT_SCHEMA_VERSIONS)!r}.")


def require_supported_compatibility(event_schema_version: str, *, projection_version: str | None = None, bundle_format_version: str | None = None) -> None:
    report = check_compatibility(event_schema_version, projection_version=projection_version, bundle_format_version=bundle_format_version)
    if report.supported:
        return

    failures: list[str] = []
    if event_schema_version not in SUPPORTED_EVENT_SCHEMA_VERSIONS:
        failures.append(f"event schema {event_schema_version!r} (supported: {sorted(SUPPORTED_EVENT_SCHEMA_VERSIONS)!r})")
    if projection_version is not None and projection_version not in SUPPORTED_PROJECTION_VERSIONS:
        failures.append(f"projection {projection_version!r} (supported: {sorted(SUPPORTED_PROJECTION_VERSIONS)!r})")
    if bundle_format_version is not None and bundle_format_version not in SUPPORTED_BUNDLE_FORMAT_VERSIONS:
        failures.append(f"bundle format {bundle_format_version!r} (supported: {sorted(SUPPORTED_BUNDLE_FORMAT_VERSIONS)!r})")
    raise SchemaCompatibilityError("Unsupported TRIA compatibility surface: " + "; ".join(failures) + ".")

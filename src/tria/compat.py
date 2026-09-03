from __future__ import annotations

from dataclasses import dataclass


CURRENT_EVENT_SCHEMA_VERSION = "0.1"
CURRENT_PROJECTION_VERSION = "0.2"
SUPPORTED_EVENT_SCHEMA_VERSIONS = frozenset({CURRENT_EVENT_SCHEMA_VERSION})


class SchemaCompatibilityError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CompatibilityReport:
    event_schema_version: str
    supported: bool
    current_event_schema_version: str = CURRENT_EVENT_SCHEMA_VERSION
    current_projection_version: str = CURRENT_PROJECTION_VERSION


def check_event_schema(version: str) -> CompatibilityReport:
    return CompatibilityReport(
        event_schema_version=version,
        supported=version in SUPPORTED_EVENT_SCHEMA_VERSIONS,
    )


def require_supported_event_schema(version: str) -> None:
    report = check_event_schema(version)
    if not report.supported:
        raise SchemaCompatibilityError(
            f"Unsupported relational event schema {version!r}; "
            f"supported versions: {sorted(SUPPORTED_EVENT_SCHEMA_VERSIONS)!r}."
        )

"""Public input, persistence and execution errors (no raw payloads in messages)."""
class TriaError(Exception):
    """Base class for SDK boundary errors."""

class InputValidationError(TriaError, ValueError):
    pass

class RelationshipNotFoundError(TriaError, LookupError):
    pass

class InvalidRelationshipError(TriaError, ValueError):
    pass

class UnknownParticipantError(InputValidationError):
    pass

class ConcurrentWriteError(TriaError, RuntimeError):
    pass

class PersistenceError(TriaError, RuntimeError):
    pass

class UnsupportedStoreError(PersistenceError):
    pass

class UnknownResourceError(TriaError, LookupError):
    pass

class InvocationAlreadyStartedError(TriaError, RuntimeError):
    pass

class ExecutionError(TriaError, RuntimeError):
    """Executor/normalizer raised; the UNKNOWN_EFFECT receipt is attached."""
    def __init__(self, receipt):
        super().__init__('Execution outcome is UNKNOWN_EFFECT; inspect receipt and reconcile before retrying.')
        self.receipt = receipt


def text_field(value, name):
    if not isinstance(value, str) or not value.strip() or value != value.strip() or any(ord(c) < 32 for c in value):
        raise InputValidationError(f'{name} must be a non-empty string without surrounding whitespace or control characters.')
    return value


def enum_field(value, kind, name):
    if not isinstance(value, kind):
        raise InputValidationError(f'{name} must be a {kind.__name__} enum member; construct it from a supported value first.')
    return value

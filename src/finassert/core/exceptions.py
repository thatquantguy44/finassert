"""Exceptions raised by finassert."""


class FinassertError(Exception):
    """Base class for library-specific exceptions."""


class ColumnNotFoundError(FinassertError, KeyError):
    """Raised when a rule's configured column is absent."""


class InvalidDataError(FinassertError, ValueError):
    """Raised when input cannot be interpreted as tabular data."""


class RuleEvaluationError(FinassertError):
    """Raised in strict mode when a rule cannot be evaluated."""

"""Custom exceptions for django-postgres-anonymizer"""


class AnonymizationError(Exception):
    """Base exception for anonymization-related errors"""

    pass


class AnonymizationValidationError(AnonymizationError):
    """Validation-related errors in anonymization operations"""

    pass


class AnonymizationDatabaseError(AnonymizationError):
    """Database operation errors in anonymization operations"""

    pass

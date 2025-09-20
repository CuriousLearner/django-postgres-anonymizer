"""Context managers for dynamic anonymization role switching"""

import contextlib
import logging
from typing import Any, Dict, Generator, Optional

from django.db import connection

from django_postgres_anon.config import anon_config

# ErrorHandler no longer needed
from django_postgres_anon.models import MaskedRole
from django_postgres_anon.utils import reset_role, switch_to_role

# Simplified error handling - no decorators needed

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def anonymized_data(role_name: Optional[str] = None, auto_create: bool = True) -> Generator[None, None, None]:
    """
    Context manager for temporarily switching to an anonymized database role.

    This allows queries within the context to see anonymized data instead of real data,
    assuming the PostgreSQL Anonymizer extension is properly configured with masking rules.

    Args:
        role_name: Name of the masked role to use. Defaults to 'masked_reader'.
        auto_create: Whether to automatically create the role if it doesn't exist.

    Example:
        >>> with anonymized_data():
        ...     users = User.objects.all()  # Returns anonymized user data

        >>> with anonymized_data('custom_masked_role'):
        ...     sensitive_data = SensitiveModel.objects.all()

    Raises:
        RuntimeError: If the role doesn't exist and auto_create is False
        Exception: If role switching fails
    """
    if role_name is None:
        role_name = anon_config.anonymized_data_role

    # Initialize state tracking
    state = _initialize_context_state()

    try:
        # Setup: Store original state and switch role
        state["original_isolation_level"] = _capture_transaction_state()
        state["role_switched"] = _setup_masked_role(role_name, auto_create)

        yield

    except Exception as e:
        logger.error(f"Error in anonymized_data context: {e}")
        raise
    finally:
        # Cleanup: Restore original state
        _restore_original_state(state)


def _initialize_context_state() -> Dict[str, Any]:
    """Initialize state tracking for the context manager."""
    connection.ensure_connection()
    connection.get_autocommit()  # Ensure connection is established
    return {"original_isolation_level": None, "role_switched": False}


def _capture_transaction_state() -> Optional[str]:
    """Capture current transaction isolation level if in a transaction."""
    if not connection.in_atomic_block:
        return None

    with connection.cursor() as cursor:
        cursor.execute("SHOW transaction_isolation")
        result = cursor.fetchone()
        return result[0] if result else None


def _setup_masked_role(role_name: str, auto_create: bool) -> bool:
    """Switch to masked role and handle auto-creation."""
    # Switch to the masked role
    if not switch_to_role(role_name, auto_create=auto_create):
        raise RuntimeError(f"Failed to switch to masked role: {role_name}")

    # Update database records if auto-created
    if auto_create:
        _update_masked_role_record(role_name)

    # Verify the switch was successful
    _verify_role_switch(role_name)

    return True


def _update_masked_role_record(role_name: str) -> None:
    """Create or update MaskedRole record for tracking."""
    masked_role, created = MaskedRole.objects.get_or_create(
        role_name=role_name,
        defaults={"is_applied": True, "description": "Auto-created role for anonymized data access"},
    )
    if not created:
        masked_role.is_applied = True
        masked_role.save()


def _verify_role_switch(role_name: str) -> None:
    """Verify that the role switch was successful."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT CURRENT_USER")
        current_user = cursor.fetchone()[0]
        logger.debug(f"Switched to database user: {current_user}")


def _restore_original_state(state: Dict[str, Any]) -> None:
    """Restore the original database connection state."""
    try:
        # Reset role if it was switched
        if state["role_switched"]:
            reset_role()

        # Restore transaction isolation level if needed
        if state["original_isolation_level"] and connection.in_atomic_block:
            _restore_isolation_level(state["original_isolation_level"])

    except Exception as e:
        logger.error(f"Error restoring original state: {e}")
        # Don't raise here as it might mask the original exception


def _restore_isolation_level(isolation_level: str) -> None:
    """Restore the original transaction isolation level."""
    with connection.cursor() as cursor:
        cursor.execute(f"SET transaction_isolation = '{isolation_level}'")


@contextlib.contextmanager
def database_role(role_name: str):
    """
    Lower-level context manager for switching to any database role.

    Args:
        role_name: Name of the database role to switch to

    Example:
        >>> with database_role('readonly_user'):
        ...     # All queries run as readonly_user
        ...     data = MyModel.objects.all()
    """
    role_switched = False

    try:
        connection.ensure_connection()

        if switch_to_role(role_name, auto_create=False):
            role_switched = True
        else:
            raise RuntimeError(f"Database role '{role_name}' does not exist")

        yield

    finally:
        if role_switched:
            reset_role()

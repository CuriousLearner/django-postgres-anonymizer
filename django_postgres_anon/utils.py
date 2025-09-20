import logging
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db import connection

from django_postgres_anon.constants import DEFAULT_POSTGRES_PORT

# from django_postgres_anon.exceptions import AnonDatabaseError, AnonValidationError

logger = logging.getLogger(__name__)


def validate_anon_extension():
    """Check if PostgreSQL anonymizer extension is available"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = %s", ["anon"])
            return cursor.fetchone() is not None
    except Exception:
        # Keep as generic Exception since this is a utility function that should never crash
        return False


def get_table_columns(table_name):
    """Get list of columns for a table"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s ORDER BY ordinal_position
            """,
                [table_name],
            )
            return [
                {
                    "column_name": row[0],
                    "data_type": row[1],
                    "is_nullable": row[2],
                    "column_default": row[3],
                }
                for row in cursor.fetchall()
            ]
    except Exception:
        # Keep as generic Exception since this is a utility function that should never crash
        return []


def validate_function_syntax(function_expr: str) -> bool:
    """Simple validation of anonymization function syntax"""
    if not function_expr or not function_expr.strip():
        return False

    function_expr = function_expr.strip()

    # Must start with anon. namespace
    if not function_expr.startswith("anon."):
        return False

    # Must have parentheses
    if "(" not in function_expr or ")" not in function_expr:
        return False

    # Security check: reject SQL injection attempts
    dangerous_patterns = [";", "--", "/*", "*/", "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE"]
    function_upper = function_expr.upper()
    for pattern in dangerous_patterns:
        if pattern in function_upper:
            return False

    # Should end with )
    if not function_expr.endswith(")"):
        return False

    return True


def check_table_exists(table_name):
    """Check if table exists in database"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_name = %s LIMIT 1
            """,
                [table_name],
            )
            return cursor.fetchone() is not None
    except Exception:
        # Keep as generic Exception since this is a utility function that should never crash
        return False


def create_masked_role(role_name, inherit_from=None):
    """Create a PostgreSQL role for masked data access"""
    try:
        with connection.cursor() as cursor:
            # Check if role already exists
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role_name])
            if cursor.fetchone():
                logger.debug(f"Role {role_name} already exists")
                return True

            # Create role with LOGIN capability
            cursor.execute(f"CREATE ROLE {connection.ops.quote_name(role_name)} WITH LOGIN INHERIT")

            # Grant inheritance from a base role if specified and it exists
            if inherit_from:
                cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [inherit_from])
                if cursor.fetchone():
                    cursor.execute(
                        f"GRANT {connection.ops.quote_name(inherit_from)} TO {connection.ops.quote_name(role_name)}"
                    )
                else:
                    logger.debug(f"Base role {inherit_from} does not exist, skipping inheritance")

            return True
    except Exception as e:
        logger.debug(f"Failed to create role {role_name}: {e}")
        return False


def get_database_connection_params() -> Dict[str, str]:
    """Extract database connection parameters from Django settings"""
    db_config = settings.DATABASES["default"]

    return {
        "dbname": db_config.get("NAME", ""),
        "user": db_config.get("USER", ""),
        "password": db_config.get("PASSWORD", ""),
        "host": db_config.get("HOST", "localhost"),
        "port": str(db_config.get("PORT", DEFAULT_POSTGRES_PORT)),
    }


def suggest_anonymization_functions(data_type: str, column_name: str) -> List[str]:
    """Suggest appropriate anonymization functions based on column type and name."""
    suggestions = []
    column_lower = column_name.lower()

    # Get column-name based suggestions
    name_suggestion = _get_suggestion_by_column_name(column_lower)
    if name_suggestion:
        suggestions.append(name_suggestion)

    # Get data-type based suggestions if no name-based suggestion found
    if not suggestions or data_type in [
        "integer",
        "bigint",
        "smallint",
        "numeric",
        "decimal",
        "real",
        "double precision",
        "date",
        "timestamp",
        "timestamptz",
    ]:
        type_suggestions = _get_suggestions_by_data_type(data_type, column_lower)
        suggestions.extend(type_suggestions)

    # Always add hash option as fallback
    suggestions.append("anon.hash({col})")

    return suggestions


def _get_suggestion_by_column_name(column_lower: str) -> Optional[str]:
    """Get anonymization suggestion based on column name patterns."""
    # Personal information patterns
    if suggestion := _check_personal_info_patterns(column_lower):
        return suggestion

    # Contact information patterns
    if suggestion := _check_contact_patterns(column_lower):
        return suggestion

    # Location patterns
    if suggestion := _check_location_patterns(column_lower):
        return suggestion

    # Financial patterns
    if suggestion := _check_financial_patterns(column_lower):
        return suggestion

    # Business patterns
    if "company" in column_lower or "organization" in column_lower:
        return "anon.fake_company()"

    return None


def _check_personal_info_patterns(column_lower: str) -> Optional[str]:
    """Check for personal information column patterns."""
    if "email" in column_lower:
        return "anon.fake_email()"

    # Name-related patterns
    if any(x in column_lower for x in ["first_name", "fname", "given_name"]):
        return "anon.fake_first_name()"
    if any(x in column_lower for x in ["last_name", "lname", "surname", "family_name"]):
        return "anon.fake_last_name()"
    if "name" in column_lower and "user" in column_lower:
        return "anon.fake_username()"
    if "name" in column_lower:
        return "anon.fake_name()"

    return None


def _check_contact_patterns(column_lower: str) -> Optional[str]:
    """Check for contact information column patterns."""
    if any(x in column_lower for x in ["phone", "tel", "mobile", "cell"]):
        return "anon.fake_phone()"
    return None


def _check_location_patterns(column_lower: str) -> Optional[str]:
    """Check for location-related column patterns."""
    if "address" in column_lower:
        return "anon.fake_address()"
    if "city" in column_lower:
        return "anon.fake_city()"
    if "state" in column_lower:
        return "anon.fake_state()"
    if any(x in column_lower for x in ["zip", "postal"]):
        return "anon.fake_zipcode()"
    if "country" in column_lower:
        return "anon.fake_country()"
    return None


def _check_financial_patterns(column_lower: str) -> Optional[str]:
    """Check for financial information column patterns."""
    if "ssn" in column_lower or "social_security" in column_lower:
        return "anon.fake_ssn()"
    if any(x in column_lower for x in ["card", "credit", "debit"]):
        return "anon.fake_credit_card_number()"
    if "iban" in column_lower:
        return "anon.fake_iban()"
    return None


def _get_suggestions_by_data_type(data_type: str, column_lower: str) -> List[str]:
    """Get anonymization suggestions based on data type."""
    suggestions = []

    if data_type in ["text", "varchar", "character varying"]:
        # For text fields, provide content-aware suggestions
        if any(x in column_lower for x in ["note", "comment", "description", "message"]):
            suggestions.append("anon.lorem_ipsum()")
        else:
            suggestions.append(f"anon.random_string({10})")
            suggestions.append('anon.partial({col}, 2, "***", 2)')

    elif data_type in ["integer", "bigint", "smallint"]:
        suggestions.append(f"anon.random_int_between({1}, {1000})")
        suggestions.append("anon.noise({col}, 0.1)")

    elif data_type in ["numeric", "decimal", "real", "double precision"]:
        suggestions.append(f"anon.noise({{col}}, {0.05})")

    elif data_type in ["date", "timestamp", "timestamptz"]:
        suggestions.append("anon.random_date_between('2020-01-01', '2026-12-31')")

    return suggestions


def get_anon_extension_info() -> Dict[str, Any]:
    """Get detailed information about the anon extension"""
    return {"installed": validate_anon_extension()}


def generate_anonymization_sql(rule):
    """Generate SQL for applying anonymization rule to a column"""
    return f"SECURITY LABEL FOR anon ON COLUMN {rule.table_name}.{rule.column_name} IS 'MASKED WITH FUNCTION {rule.get_rendered_function()}';"


def generate_remove_anonymization_sql(table_name, column_name):
    """Generate SQL for removing anonymization from a column"""
    return f"SECURITY LABEL FOR anon ON COLUMN {table_name}.{column_name} IS NULL;"


def create_operation_log(operation, user=None, **kwargs):
    """Standardized logging for all operations"""
    from django_postgres_anon.models import MaskingLog

    # Extract common fields
    details = kwargs.pop("details", {})
    success = kwargs.pop("success", True)
    error_message = kwargs.pop("error_message", "")  # Default to empty string instead of None

    # Set default user if not provided (for commands without user context)
    if user is None:
        user = ""  # Default to empty string for commands

    return MaskingLog.objects.create(
        operation=operation, user=user, details=details, success=success, error_message=error_message, **kwargs
    )


def switch_to_role(role_name: str, auto_create: bool = True):
    """
    Utility function to switch to a database role with error handling.

    Args:
        role_name: Name of the role to switch to
        auto_create: Whether to create the role if it doesn't exist

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SET ROLE {role_name}")
            return True
    except Exception as e:
        logger.debug(f"Failed to switch to role {role_name}: {e}")
        if auto_create:
            return create_masked_role(role_name)
        return False


def reset_role():
    """
    Utility function to reset database role to default.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")
            return True
    except Exception as e:
        logger.debug(f"Failed to reset role: {e}")
        return False

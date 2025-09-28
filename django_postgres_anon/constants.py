"""Essential constants for django-postgres-anonymizer"""

# Admin operations
VALID_ADMIN_OPERATIONS = ["apply", "drop", "enable", "disable", "mark_for_application"]
EXTENSION_REQUIRED_OPERATIONS = ["apply", "drop"]

# Default values
DEFAULT_MASKED_ROLE = "masked_reader"
DEFAULT_BATCH_SIZE = 1000
DEFAULT_POSTGRES_PORT = "5432"

# Emojis for messages
ADMIN_ERROR_EMOJI = "❌"
ADMIN_WARNING_EMOJI = "⚠️"

# Admin operation constants
MAX_RULES_TO_VALIDATE = 100
ANON_FUNCTION_PREFIX = "anon."
MAX_ERRORS_TO_SHOW = 5
MAX_ERROR_SUMMARY_COUNT = 3
MAX_ERRORS_BEFORE_ROLLBACK = 10

# Field name constants for operation results
APPLIED_COUNT_FIELD = "applied_count"
ERRORS_FIELD = "errors"
SUCCESS_FIELD = "success"
ERROR_FIELD = "error"
MASKED_ROLE_MARK_APPLIED_METHOD = "mark_applied"

# SQL templates
ANONYMIZATION_SQL_TEMPLATE = "SECURITY LABEL FOR anon ON COLUMN {table}.{column} IS 'MASKED WITH FUNCTION {function}';"
REMOVE_ANONYMIZATION_SQL_TEMPLATE = "SECURITY LABEL FOR anon ON COLUMN {table}.{column} IS NULL;"

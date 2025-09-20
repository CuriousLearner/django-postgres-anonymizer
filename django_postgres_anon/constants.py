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

# SQL templates
ANONYMIZATION_SQL_TEMPLATE = "SECURITY LABEL FOR anon ON COLUMN {table}.{column} IS 'MASKED WITH FUNCTION {function}';"
REMOVE_ANONYMIZATION_SQL_TEMPLATE = "SECURITY LABEL FOR anon ON COLUMN {table}.{column} IS NULL;"

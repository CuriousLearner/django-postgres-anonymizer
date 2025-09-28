"""Simple configuration helpers for django-postgres-anonymizer"""

import os

from django.conf import settings


def get_setting(key: str, default=None):
    """Get a setting from POSTGRES_ANON configuration with default fallback"""
    return getattr(settings, "POSTGRES_ANON", {}).get(key, default)


# Default values (moved from constants.py to keep config self-contained)
DEFAULTS = {
    "DEFAULT_MASKED_ROLE": "masked_reader",
    "MASKED_GROUPS": ["view_masked_data"],
    "ANONYMIZED_DATA_ROLE": "masked_reader",
    "ENABLED": False,
    "AUTO_APPLY_RULES": False,
    "VALIDATE_FUNCTIONS": True,
    "ALLOW_CUSTOM_FUNCTIONS": False,
    "ENABLE_LOGGING": True,
}

# Environment variable mappings (12-factor compliant)
ENV_VAR_MAPPING = {
    "DEFAULT_MASKED_ROLE": "POSTGRES_ANON_DEFAULT_MASKED_ROLE",
    "MASKED_GROUPS": "POSTGRES_ANON_MASKED_GROUPS",
    "ANONYMIZED_DATA_ROLE": "POSTGRES_ANON_ANONYMIZED_DATA_ROLE",
    "ENABLED": "POSTGRES_ANON_ENABLED",
    "AUTO_APPLY_RULES": "POSTGRES_ANON_AUTO_APPLY_RULES",
    "VALIDATE_FUNCTIONS": "POSTGRES_ANON_VALIDATE_FUNCTIONS",
    "ALLOW_CUSTOM_FUNCTIONS": "POSTGRES_ANON_ALLOW_CUSTOM_FUNCTIONS",
    "ENABLE_LOGGING": "POSTGRES_ANON_ENABLE_LOGGING",
}


def _parse_env_bool(value: str) -> bool:
    """Parse environment variable as boolean"""
    return value.lower() in ("true", "1", "yes", "on")


def get_anon_setting(key: str):
    """Get anonymization setting with built-in default (12-factor compliant)"""
    # First check environment variables (12-factor principle)
    env_var = ENV_VAR_MAPPING.get(key)
    if env_var and env_var in os.environ:
        env_value = os.environ[env_var]
        # Handle boolean conversion for known boolean settings
        if key in ["ENABLED", "AUTO_APPLY_RULES", "VALIDATE_FUNCTIONS", "ALLOW_CUSTOM_FUNCTIONS", "ENABLE_LOGGING"]:
            return _parse_env_bool(env_value)
        # Handle comma-separated groups
        if key == "MASKED_GROUPS":
            return [group.strip() for group in env_value.split(",") if group.strip()]
        return env_value

    # Fall back to Django settings
    django_setting = get_setting(key)
    if django_setting is not None:
        return django_setting

    # Finally use default
    return DEFAULTS.get(key)

"""Simple configuration helpers for django-postgres-anonymizer"""

from django.conf import settings


def get_setting(key: str, default=None):
    """Get a setting from POSTGRES_ANON configuration with default fallback"""
    return getattr(settings, "POSTGRES_ANON", {}).get(key, default)


# Default values (moved from constants.py to keep config self-contained)
DEFAULTS = {
    "DEFAULT_MASKED_ROLE": "masked_reader",
    "MASKED_GROUP": "view_masked_data",
    "ANONYMIZED_DATA_ROLE": "masked_reader",
    "ENABLED": False,
    "AUTO_APPLY_RULES": False,
    "VALIDATE_FUNCTIONS": True,
    "ALLOW_CUSTOM_FUNCTIONS": False,
    "ENABLE_LOGGING": True,
}


def get_anon_setting(key: str):
    """Get anonymization setting with built-in default"""
    return get_setting(key, DEFAULTS.get(key))

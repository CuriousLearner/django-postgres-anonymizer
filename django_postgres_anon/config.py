"""Centralized configuration for django-postgres-anonymizer"""

from django.conf import settings


class AnonConfig:
    """Centralized configuration class for all anonymization settings"""

    def __init__(self):
        # Get the settings dict or use defaults
        config = getattr(settings, "POSTGRES_ANON", {})

        # Set defaults
        self._config = {
            "DEFAULT_MASKED_ROLE": "masked_reader",
            "MASKED_GROUP": "view_masked_data",
            "ANONYMIZED_DATA_ROLE": "masked_reader",
            "ENABLED": False,
            "AUTO_APPLY_RULES": False,
            "VALIDATE_FUNCTIONS": True,
            "ALLOW_CUSTOM_FUNCTIONS": False,
            "ENABLE_LOGGING": True,
        }

        # Override with user settings
        self._config.update(config)

    @property
    def default_masked_role(self) -> str:
        """Default role name for anonymized access"""
        return self._config["DEFAULT_MASKED_ROLE"]

    @property
    def masked_group(self) -> str:
        """Group name for users who should see masked data"""
        return self._config["MASKED_GROUP"]

    @property
    def anonymized_data_role(self) -> str:
        """Role for anonymized data context manager"""
        return self._config["ANONYMIZED_DATA_ROLE"]

    @property
    def enabled(self) -> bool:
        """Whether anonymization is enabled"""
        return self._config["ENABLED"]

    @property
    def auto_apply_rules(self) -> bool:
        """Whether to automatically apply rules when created"""
        return self._config["AUTO_APPLY_RULES"]

    @property
    def validate_functions(self) -> bool:
        """Whether to validate anonymization functions"""
        return self._config["VALIDATE_FUNCTIONS"]

    @property
    def allow_custom_functions(self) -> bool:
        """Whether to allow custom anonymization functions"""
        return self._config["ALLOW_CUSTOM_FUNCTIONS"]

    @property
    def enable_logging(self) -> bool:
        """Whether to enable audit logging"""
        return self._config["ENABLE_LOGGING"]


# Global configuration instance
anon_config = AnonConfig()

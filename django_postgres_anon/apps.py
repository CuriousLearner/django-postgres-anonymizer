import logging

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class DjangoPostgresAnonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_postgres_anon"
    verbose_name = "PostgreSQL Anonymizer"

    def ready(self):
        """Initialize app when Django starts"""
        # Auto-setup in development if enabled
        if getattr(settings, "ANON_AUTO_INIT", False) and settings.DEBUG:
            try:
                self._auto_init_development()
            except Exception as e:
                logger.warning(f"Auto-init failed: {e}")

    def _auto_init_development(self):
        """Auto-initialize anonymization in development"""
        from django.core.management import call_command

        logger.info("Auto-initializing PostgreSQL Anonymizer for development")
        call_command("anon_init", verbosity=0)

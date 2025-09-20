"""Tests for Django app configuration and initialization"""

from unittest.mock import patch

from django.test import TestCase, override_settings

from django_postgres_anon.apps import DjangoPostgresAnonConfig


class TestDjangoAppConfig(TestCase):
    """Test Django app configuration and ready() method"""

    def test_app_config_has_correct_metadata(self):
        """App config has correct name and verbose name"""
        import django_postgres_anon

        module = django_postgres_anon
        config = DjangoPostgresAnonConfig("django_postgres_anon", module)

        assert config.name == "django_postgres_anon"
        assert config.verbose_name == "PostgreSQL Anonymizer"
        assert config.default_auto_field == "django.db.models.BigAutoField"

    @override_settings(ANON_AUTO_INIT=True, DEBUG=True)
    @patch("django.core.management.call_command")
    @patch("django_postgres_anon.apps.logger")
    def test_auto_init_runs_in_development_when_enabled(self, mock_logger, mock_call_command):
        """Auto-initialization runs in development when ANON_AUTO_INIT is True"""
        import django_postgres_anon

        config = DjangoPostgresAnonConfig("django_postgres_anon", django_postgres_anon)
        config.ready()

        mock_call_command.assert_called_once_with("anon_init", verbosity=0)
        mock_logger.info.assert_called_once_with("Auto-initializing PostgreSQL Anonymizer for development")

    @override_settings(ANON_AUTO_INIT=False, DEBUG=True)
    @patch("django.core.management.call_command")
    def test_auto_init_skipped_when_disabled(self, mock_call_command):
        """Auto-initialization is skipped when ANON_AUTO_INIT is False"""
        import django_postgres_anon

        config = DjangoPostgresAnonConfig("django_postgres_anon", django_postgres_anon)
        config.ready()

        mock_call_command.assert_not_called()

    @override_settings(ANON_AUTO_INIT=True, DEBUG=False)
    @patch("django.core.management.call_command")
    def test_auto_init_skipped_in_production(self, mock_call_command):
        """Auto-initialization is skipped in production (DEBUG=False)"""
        import django_postgres_anon

        config = DjangoPostgresAnonConfig("django_postgres_anon", django_postgres_anon)
        config.ready()

        mock_call_command.assert_not_called()

    @override_settings(ANON_AUTO_INIT=True, DEBUG=True)
    @patch("django.core.management.call_command")
    @patch("django_postgres_anon.apps.logger")
    def test_auto_init_handles_errors_gracefully(self, mock_logger, mock_call_command):
        """Auto-initialization handles errors gracefully and logs warning"""
        mock_call_command.side_effect = Exception("Database not ready")

        import django_postgres_anon

        config = DjangoPostgresAnonConfig("django_postgres_anon", django_postgres_anon)
        config.ready()  # Should not raise exception

        mock_logger.warning.assert_called_once_with("Auto-init failed: Database not ready")

    def test_ready_method_can_be_called_multiple_times(self):
        """ready() method can be called multiple times without issues"""
        import django_postgres_anon

        config = DjangoPostgresAnonConfig("django_postgres_anon", django_postgres_anon)

        # Should not raise exception when called multiple times
        config.ready()
        config.ready()
        config.ready()

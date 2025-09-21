"""Pytest configuration and fixtures for django-postgres-anonymizer tests"""

import os
from unittest.mock import MagicMock

import pytest


def pytest_configure(config):
    """Configure Django settings for pytest"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

    # Set database environment variables if not already set
    os.environ.setdefault("DB_USER", "sanyamkhurana")
    os.environ.setdefault("DB_NAME", "postgres_anon_example")
    os.environ.setdefault("DB_PASSWORD", "")
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_PORT", "5432")

    import django
    from django.conf import settings

    if not settings.configured or not hasattr(django.apps.apps, "ready") or not django.apps.apps.ready:
        django.setup()


# Django models will be imported in fixtures to avoid import-time issues


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup):
    """Set up the test database"""
    # Let pytest-django handle DB setup
    pass


@pytest.fixture
def user():
    """Create a regular test user"""
    from django.contrib.auth.models import User
    from model_bakery import baker

    return baker.make(User, email="user@example.com")


@pytest.fixture
def admin_user():
    """Create an admin user"""
    from django.contrib.auth.models import User
    from model_bakery import baker

    return baker.make(User, is_superuser=True, is_staff=True, email="admin@example.com")


@pytest.fixture
def masked_user():
    """Create a user in the masked data group"""
    from django.contrib.auth.models import Group, User
    from model_bakery import baker

    user = baker.make(User, email="masked@example.com")
    group, _ = Group.objects.get_or_create(name="view_masked_data")
    user.groups.add(group)
    return user


@pytest.fixture
def staff_user():
    """Create a staff user"""
    from django.contrib.auth.models import User
    from model_bakery import baker

    return baker.make(User, is_staff=True, email="staff@example.com")


# Client fixtures
@pytest.fixture
def client():
    """Django test client"""
    from django.test import Client

    return Client()


@pytest.fixture
def api_client():
    """DRF API client"""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def request_factory():
    """Django request factory"""
    from django.test import RequestFactory

    return RequestFactory()


@pytest.fixture
def authenticated_client(client, user):
    """Client authenticated with regular user"""
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Client authenticated with admin user"""
    client.force_login(admin_user)
    return client


@pytest.fixture
def authenticated_api_client(api_client, user):
    """API client authenticated with regular user"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_api_client(api_client, admin_user):
    """API client authenticated with admin user"""
    api_client.force_authenticate(user=admin_user)
    return api_client


# Extension availability fixture
@pytest.fixture
def anon_extension_available():
    """Check if PostgreSQL Anonymizer extension is available"""
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname='anon';")
            return cursor.fetchone() is not None
    except Exception:
        return False


# Model fixtures using Model Bakery
@pytest.fixture
def sample_masking_rule():
    """Create a sample masking rule"""
    from model_bakery import baker

    from django_postgres_anon.models import MaskingRule

    return baker.make(MaskingRule, table_name="auth_user", column_name="email", function_expr="anon.fake_email()")


@pytest.fixture
def disabled_masking_rule():
    """Create a disabled masking rule"""
    from model_bakery import baker

    from django_postgres_anon.models import MaskingRule

    return baker.make(MaskingRule, enabled=False)


@pytest.fixture
def multiple_masking_rules():
    """Create multiple masking rules"""
    from model_bakery import baker

    from django_postgres_anon.models import MaskingRule

    return [
        baker.make(MaskingRule, enabled=True),
        baker.make(MaskingRule, enabled=True),
        baker.make(MaskingRule, enabled=False),
        baker.make(MaskingRule, enabled=False),
    ]


@pytest.fixture
def masking_preset():
    """Create a masking preset"""
    from model_bakery import baker

    from django_postgres_anon.models import MaskingPreset

    return baker.make(MaskingPreset)


@pytest.fixture
def sample_preset_with_rules():
    """Create a preset with rules"""
    from model_bakery import baker

    from django_postgres_anon.models import MaskingPreset, MaskingRule

    preset = baker.make(MaskingPreset, preset_type="django_auth")
    rules = [
        baker.make(MaskingRule, table_name="auth_user", column_name="email", function_expr="anon.fake_email()"),
        baker.make(
            MaskingRule, table_name="auth_user", column_name="first_name", function_expr="anon.fake_first_name()"
        ),
    ]
    preset.rules.add(*rules)
    return preset


@pytest.fixture
def masking_log_entries():
    """Create sample masking log entries"""
    from model_bakery import baker

    from django_postgres_anon.models import MaskingLog

    logs = [
        baker.make(MaskingLog, operation="init", success=True, details={"version": "1.3.2"}),
        baker.make(MaskingLog, operation="apply", success=True, details={"applied_count": 5}),
        baker.make(MaskingLog, operation="apply", success=False, error_message="Connection failed"),
    ]
    return logs


# Mock fixtures
@pytest.fixture
def mock_postgres_connection():
    """Mock PostgreSQL connection for unit tests that don't need real DB"""
    from unittest.mock import MagicMock, patch

    mock_cursor = MagicMock()
    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("django_postgres_anon.utils.connection", mock_connection):
        yield mock_cursor


@pytest.fixture
def mock_successful_db_operations():
    """Mock database operations that succeed"""
    mock_cursor = MagicMock()
    mock_cursor.execute.return_value = None
    mock_cursor.fetchone.side_effect = [("1.3.2",), ("on",), (5,)]  # Version  # Privacy default  # Label count
    mock_cursor.fetchall.return_value = [
        ("auth_user", "email", "character varying"),
        ("auth_user", "username", "character varying"),
    ]

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.cursor.return_value.__exit__.return_value = None

    return mock_connection, mock_cursor


@pytest.fixture
def mock_failing_db_operations():
    """Mock database operations that fail"""
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Database operation failed")

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    return mock_connection, mock_cursor


# Enhanced mock fixtures for common database operation patterns
@pytest.fixture
def mock_db_cursor():
    """Provides a pre-configured database cursor mock with common setup"""
    from unittest.mock import MagicMock, patch

    mock_cursor = MagicMock()
    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.cursor.return_value.__exit__.return_value = None

    # Common database operations defaults
    mock_cursor.fetchone.return_value = ("test_result",)
    mock_cursor.fetchall.return_value = [("test_row",)]
    mock_cursor.execute.return_value = None

    return mock_connection, mock_cursor


@pytest.fixture
def mock_anon_extension():
    """Mock PostgreSQL anonymizer extension functions"""
    from unittest.mock import MagicMock, patch

    mock_cursor = MagicMock()
    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.cursor.return_value.__exit__.return_value = None

    # Mock extension check as existing
    mock_cursor.fetchone.return_value = (1,)
    mock_cursor.fetchall.return_value = [
        ("fake_email",),
        ("fake_first_name",),
        ("partial",),
    ]

    with patch("django_postgres_anon.utils.connection", mock_connection):
        yield mock_cursor


@pytest.fixture
def mock_role_operations():
    """Mock role-related database operations"""
    from unittest.mock import MagicMock, patch

    mock_cursor = MagicMock()
    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.cursor.return_value.__exit__.return_value = None
    mock_connection.ops.quote_name = lambda x: f'"{x}"'

    # Mock role existence check
    mock_cursor.fetchone.side_effect = [None, (1,)]  # First call: role doesn't exist, second: it does

    with patch("django_postgres_anon.utils.connection", mock_connection), patch(
        "django_postgres_anon.context_managers.connection", mock_connection
    ), patch("django_postgres_anon.middleware.connection", mock_connection):
        yield mock_cursor


@pytest.fixture
def mock_utils_connection():
    """Mock django_postgres_anon.utils.connection with configured cursor"""
    from unittest.mock import MagicMock, patch

    mock_cursor = MagicMock()
    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.cursor.return_value.__exit__.return_value = None

    with patch("django.db.connection", mock_connection):
        yield mock_connection, mock_cursor


@pytest.fixture
def mock_commands_connection():
    """Mock connection for management commands"""
    from unittest.mock import MagicMock, patch

    mock_cursor = MagicMock()
    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.cursor.return_value.__exit__.return_value = None

    # Patch common command connection paths
    with patch("django_postgres_anon.management.commands.anon_init.connection", mock_connection), patch(
        "django_postgres_anon.management.commands.anon_apply.connection", mock_connection
    ), patch("django_postgres_anon.management.commands.anon_dump.connection", mock_connection), patch(
        "django_postgres_anon.management.commands.anon_status.connection", mock_connection
    ):
        yield mock_connection, mock_cursor


@pytest.fixture
def mock_extension_exists():
    """Mock extension exists check (returns True)"""

    def _setup_cursor(mock_cursor):
        mock_cursor.fetchone.return_value = ("1",)  # Extension exists
        return mock_cursor

    return _setup_cursor


@pytest.fixture
def mock_extension_not_exists():
    """Mock extension doesn't exist check (returns False)"""

    def _setup_cursor(mock_cursor):
        mock_cursor.fetchone.return_value = None  # Extension doesn't exist
        return mock_cursor

    return _setup_cursor


@pytest.fixture
def mock_table_columns():
    """Mock table columns data"""

    def _setup_cursor(mock_cursor):
        mock_cursor.fetchall.return_value = [
            ("id", "integer", True, False),  # column_name, data_type, is_primary_key, has_unique_constraint
            ("email", "character varying", False, True),
            ("created_at", "timestamp with time zone", False, False),
        ]
        return mock_cursor

    return _setup_cursor


@pytest.fixture
def mock_foreign_keys():
    """Mock foreign keys data"""

    def _setup_cursor(mock_cursor):
        mock_cursor.fetchall.return_value = [
            ("order_items", "order_id", "orders", "id", "fk_order_items_order_id"),
            ("order_items", "product_id", "products", "id", "fk_order_items_product_id"),
        ]
        return mock_cursor

    return _setup_cursor


@pytest.fixture
def mock_anon_functions():
    """Mock anonymization functions data"""

    def _setup_cursor(mock_cursor):
        mock_cursor.fetchall.return_value = [
            ("fake_email",),
            ("fake_first_name",),
            ("fake_last_name",),
            ("random_string",),
        ]
        return mock_cursor

    return _setup_cursor


@pytest.fixture
def mock_anon_extension_info():
    """Mock extension info with version, config, and function count"""

    def _setup_cursor(mock_cursor):
        mock_cursor.fetchone.side_effect = [
            ("1",),  # Extension exists
            ("1.3.2",),  # Version
            ("on",),  # Privacy by default
            (15,),  # Function count
        ]
        return mock_cursor

    return _setup_cursor


@pytest.fixture
def mock_database_error():
    """Mock database operations that fail with exception"""

    def _setup_cursor(mock_cursor):
        mock_cursor.execute.side_effect = Exception("Database error")
        return mock_cursor

    return _setup_cursor


@pytest.fixture
def mock_empty_results():
    """Mock empty database results"""

    def _setup_cursor(mock_cursor):
        mock_cursor.fetchone.return_value = None
        mock_cursor.fetchall.return_value = []
        return mock_cursor

    return _setup_cursor


@pytest.fixture
def mock_cursor_factory():
    """Factory to create configured mock cursors with specific behaviors"""
    from unittest.mock import MagicMock

    def _create_cursor(**kwargs):
        """
        Create a mock cursor with specified behaviors

        Args:
            execute_return: Return value for execute() calls
            execute_side_effect: Side effect for execute() calls (e.g., Exception)
            fetchone_return: Return value for fetchone() calls
            fetchone_side_effect: Side effect for fetchone() calls (for multiple calls)
            fetchall_return: Return value for fetchall() calls
            fetchall_side_effect: Side effect for fetchall() calls
        """
        mock_cursor = MagicMock()

        # Configure execute behavior
        if "execute_return" in kwargs:
            mock_cursor.execute.return_value = kwargs["execute_return"]
        elif "execute_side_effect" in kwargs:
            mock_cursor.execute.side_effect = kwargs["execute_side_effect"]
        else:
            mock_cursor.execute.return_value = None

        # Configure fetchone behavior
        if "fetchone_return" in kwargs:
            mock_cursor.fetchone.return_value = kwargs["fetchone_return"]
        elif "fetchone_side_effect" in kwargs:
            mock_cursor.fetchone.side_effect = kwargs["fetchone_side_effect"]

        # Configure fetchall behavior
        if "fetchall_return" in kwargs:
            mock_cursor.fetchall.return_value = kwargs["fetchall_return"]
        elif "fetchall_side_effect" in kwargs:
            mock_cursor.fetchall.side_effect = kwargs["fetchall_side_effect"]

        return mock_cursor

    return _create_cursor


# File fixtures
@pytest.fixture
def temp_yaml_preset():
    """Create a temporary YAML preset file for testing"""
    import os
    import tempfile

    import yaml

    preset_data = [
        {
            "table": "auth_user",
            "column": "email",
            "function": "anon.fake_email()",
            "enabled": True,
            "notes": "Test email anonymization",
        },
        {"table": "auth_user", "column": "first_name", "function": "anon.fake_first_name()", "enabled": True},
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(preset_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except Exception:
        pass


@pytest.fixture
def temp_sql_file():
    """Create temporary SQL file for testing"""
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write("SELECT 1; -- Test SQL content")
        temp_path = f.name

    yield temp_path

    try:
        os.unlink(temp_path)
    except Exception:
        pass


# Settings fixtures
@pytest.fixture
def anon_enabled_settings(settings):
    """Enable anonymization in settings"""
    settings.POSTGRES_ANON = {
        "ENABLED": True,
        "DEFAULT_MASKED_ROLE": "masked_reader",
        "AUTO_APPLY_RULES": False,
        "ENABLE_LOGGING": True,
    }
    return settings


@pytest.fixture
def anon_disabled_settings(settings):
    """Disable anonymization in settings"""
    settings.POSTGRES_ANON = {
        "ENABLED": False,
    }
    return settings


# Group fixtures
@pytest.fixture
def view_masked_data_group():
    """Create the view_masked_data group"""
    from django.contrib.auth.models import Group

    group, created = Group.objects.get_or_create(name="view_masked_data")
    yield group
    if created:
        try:
            group.delete()
        except Exception:
            pass


# Test control fixtures


@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()


# Essential autouse fixtures
@pytest.fixture(autouse=True)
def _clear_caches():
    """Clear all caches after each test"""
    yield
    try:
        from django.core.cache import cache

        cache.clear()

        # Clear function caches
        from django_postgres_anon.utils import get_table_columns

        if hasattr(get_table_columns, "cache_clear"):
            get_table_columns.cache_clear()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _configure_test_environment(request, settings):
    """Configure isolated test environment for pytest-xdist workers"""
    # Get worker_id if running with pytest-xdist
    worker_id = getattr(request.config, "workerinput", {}).get("workerid", "master")

    if worker_id != "master":
        # Use isolated cache for xdist workers
        worker_id = worker_id.replace("gw", "")
        try:
            caches = settings.CACHES.copy()
            caches["default"]["LOCATION"] = f"locmem://test_{worker_id}"
            settings.CACHES = caches
        except Exception:
            pass
    yield
    try:
        from django.core.cache import cache

        cache.clear()
    except Exception:
        pass


# Enhanced cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Auto-cleanup after each test with enhanced safety"""
    yield

    # Clean up test data after each test
    try:
        from django_postgres_anon.models import MaskedRole, MaskingLog, MaskingPreset, MaskingRule

        # Clean up in reverse dependency order
        MaskingRule.objects.filter(
            table_name__in=["test_table", "auth_user", "orders", "customers", "sample_table"]
        ).delete()

        MaskingLog.objects.filter(operation__in=["test", "init", "apply"]).delete()
        MaskedRole.objects.filter(role_name__startswith="test_").delete()
        MaskingPreset.objects.filter(name__startswith="test_").delete()

        # Clean up test users with more specific filters
        from django.contrib.auth.models import Group, User

        test_usernames = [
            "testuser",
            "masked_user",
            "staff",
            "test_user_1",
            "test_user_2",
            "admin_test",
            "regular_test",
        ]
        User.objects.filter(username__in=test_usernames).delete()
        User.objects.filter(email__contains="@example.com").exclude(is_superuser=True).delete()

        # Clean up test groups
        Group.objects.filter(name__in=["view_masked_data", "custom_masked_group", "test_group"]).delete()

    except Exception as e:
        # Log cleanup errors in development but don't fail tests
        import logging

        logging.getLogger("django_postgres_anon.tests").warning(f"Cleanup error: {e}")
        pass


# Legacy support for existing tests
@pytest.mark.django_db
class DatabaseTestMixin:
    """Mixin class for database-dependent tests (legacy support)"""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, db):
        """Set up test data for database tests"""
        from django.contrib.auth.models import User

        # Create test user
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", first_name="Test", last_name="User"
        )

        yield

        # Cleanup is handled by transaction rollback


# Command output capture fixtures
@pytest.fixture
def captured_output():
    """Capture command output for testing"""
    from io import StringIO

    return StringIO()


@pytest.fixture
def call_command_with_output():
    """Helper to call management commands and capture output"""
    from io import StringIO

    from django.core.management import call_command

    def _call_command(command_name, *args, **kwargs):
        out = StringIO()
        kwargs["stdout"] = out
        call_command(command_name, *args, **kwargs)
        return out.getvalue()

    return _call_command


# Collection hooks for automatic test categorization
def pytest_collection_modifyitems(config, items):
    """Enhanced collection hooks for automatic test categorization"""
    _ = config  # Unused but required by pytest
    for item in items:
        # Add markers based on file names
        filepath = str(item.fspath)

        # Integration test detection (keep markers but don't force skip)
        if (
            "test_integration" in filepath
            or "integration" in filepath
            or any("integration" in mark.name for mark in item.iter_markers())
        ):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)

        # API test detection
        elif "test_api" in filepath or "api" in filepath:
            item.add_marker(pytest.mark.api)
            item.add_marker(pytest.mark.functional)

        # Model test detection
        elif "test_models" in filepath:
            item.add_marker(pytest.mark.models)
            item.add_marker(pytest.mark.unit)

        # Command test detection
        elif "test_commands" in filepath:
            item.add_marker(pytest.mark.commands)
            item.add_marker(pytest.mark.functional)

        # Context manager and decorator tests
        elif "test_context_managers" in filepath or "test_decorators" in filepath:
            item.add_marker(pytest.mark.unit)
            item.add_marker(pytest.mark.functional)

        # Security test detection
        elif "security" in filepath or "test_security" in filepath:
            item.add_marker(pytest.mark.security)
            item.add_marker(pytest.mark.unit)

        # Performance test detection
        elif "performance" in filepath or "test_performance" in filepath:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)

        # Utils test detection
        elif "test_utils" in filepath:
            item.add_marker(pytest.mark.utils)
            item.add_marker(pytest.mark.unit)

        # Default to unit tests for unmatched patterns
        else:
            if not any(mark.name in ["integration", "functional", "slow"] for mark in item.iter_markers()):
                item.add_marker(pytest.mark.unit)


# Custom pytest markers are defined in pyproject.toml

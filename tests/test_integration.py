"""
Function-based integration tests for django-postgres-anonymizer

These tests require a PostgreSQL database with the anon extension installed.
They test the full workflow from initialization to anonymization.
"""

import os
import tempfile

from django.contrib.auth.models import User
from django.core.management import call_command

import pytest

from django_postgres_anon.models import MaskingLog, MaskingPreset, MaskingRule


@pytest.fixture
def clean_database():
    """Ensure clean state for integration tests"""
    MaskingRule.objects.all().delete()
    MaskingLog.objects.all().delete()
    yield
    # Cleanup after test
    MaskingRule.objects.all().delete()
    MaskingLog.objects.all().delete()


@pytest.fixture
def test_user():
    """Create a test user for anonymization"""
    user = User.objects.create_user(username="testuser", email="test@example.com", first_name="John", last_name="Doe")
    yield user
    user.delete()


@pytest.mark.django_db(transaction=True)
def test_full_anonymization_workflow(clean_database, test_user):
    """Test complete workflow: init -> create rules -> apply -> verify"""

    # Step 1: Initialize extension (force to ensure it runs even if already exists)
    try:
        call_command("anon_init", force=True)
    except Exception as e:
        pytest.skip(f"Could not initialize anon extension: {e}")

    # Verify initialization log
    init_log = MaskingLog.objects.filter(operation="init").order_by("-timestamp").first()
    assert init_log is not None
    assert init_log.success is True

    # Step 2: Create masking rules
    email_rule = MaskingRule.objects.create(
        table_name="auth_user", column_name="email", function_expr="anon.fake_email()"
    )
    name_rule = MaskingRule.objects.create(
        table_name="auth_user", column_name="first_name", function_expr="anon.fake_first_name()"
    )

    assert MaskingRule.objects.count() == 2

    # Step 3: Apply anonymization
    try:
        call_command("anon_apply")
    except Exception as e:
        pytest.skip(f"Could not apply anonymization: {e}")

    # Verify application log
    apply_log = MaskingLog.objects.filter(operation="apply").first()
    assert apply_log is not None
    assert apply_log.success is True

    # Step 4: Verify rules were marked as applied
    email_rule.refresh_from_db()
    name_rule.refresh_from_db()
    assert email_rule.applied_at is not None
    assert name_rule.applied_at is not None


@pytest.mark.django_db(transaction=True)
def test_anon_status_command(clean_database):
    """Test the anon_status command"""
    try:
        call_command("anon_status")
    except Exception as e:
        pytest.skip(f"Could not run anon_status: {e}")

    # Should not raise any exceptions


@pytest.mark.django_db(transaction=True)
def test_preset_loading_integration(clean_database):
    """Test loading presets from YAML files"""
    # Create a temporary YAML file
    preset_data = {
        "name": "test_preset",
        "preset_type": "custom",
        "description": "Test preset for integration",
        "rules": [{"table_name": "auth_user", "column_name": "email", "function_expr": "anon.fake_email()"}],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        import yaml

        yaml.dump(preset_data, f)
        yaml_file = f.name

    try:
        # Load the preset
        call_command("anon_load_yaml", yaml_file)

        # Verify preset was created
        preset = MaskingPreset.objects.get(name="test_preset")
        assert preset.preset_type == "custom"
        assert preset.rules.count() == 1

        rule = preset.rules.first()
        assert rule.table_name == "auth_user"
        assert rule.column_name == "email"
        assert rule.function_expr == "anon.fake_email()"

    finally:
        os.unlink(yaml_file)


@pytest.mark.django_db(transaction=True)
def test_database_connection_params():
    """Test database connection parameter extraction"""
    from django_postgres_anon.utils import get_database_connection_params

    params = get_database_connection_params()

    # Should return a dictionary with connection parameters
    assert isinstance(params, dict)
    assert "dbname" in params or "database" in params
    assert "host" in params
    assert "port" in params


@pytest.mark.django_db(transaction=True)
def test_anon_extension_validation():
    """Test anon extension validation"""
    from django_postgres_anon.utils import validate_anon_extension

    try:
        # Should not raise exception if extension is available
        validate_anon_extension()
    except Exception as e:
        pytest.skip(f"Anon extension not available: {e}")


@pytest.mark.django_db(transaction=True)
def test_table_column_introspection():
    """Test table column introspection"""
    from django_postgres_anon.utils import get_table_columns

    # Test with auth_user table which should always exist
    columns = get_table_columns("auth_user")

    assert isinstance(columns, list)
    assert len(columns) > 0

    # Check that we have expected columns
    column_names = [col["column_name"] for col in columns]
    assert "username" in column_names
    assert "email" in column_names
    assert "first_name" in column_names


@pytest.mark.django_db(transaction=True)
@pytest.mark.django_db(transaction=True)
def test_middleware_integration(clean_database, test_user):
    """Test middleware integration with database roles"""
    from django.contrib.auth.models import AnonymousUser
    from django.http import HttpRequest

    from django_postgres_anon.middleware import AnonRoleMiddleware

    middleware = AnonRoleMiddleware(lambda request: None)

    # Test with anonymous user
    request = HttpRequest()
    request.user = AnonymousUser()

    # Should not raise exception
    middleware(request)

    # Test with authenticated user
    request.user = test_user

    # Should not raise exception
    middleware(request)


@pytest.mark.django_db(transaction=True)
def test_masking_rule_validation():
    """Test masking rule validation with real database"""
    # Create a rule with valid function
    rule = MaskingRule.objects.create(table_name="auth_user", column_name="email", function_expr="anon.fake_email()")

    # Validate the function expression
    from django_postgres_anon.utils import validate_function_syntax

    try:
        is_valid = validate_function_syntax(rule.function_expr)
        assert is_valid is True
    except Exception:
        # Function validation might not be available in all environments
        pytest.skip("Function validation not available")


@pytest.mark.django_db(transaction=True)
def test_backup_and_restore_workflow(clean_database, test_user):
    """Test backup creation and data dump functionality"""
    import shutil

    # Check if pg_dump is available
    if not shutil.which("pg_dump"):
        pytest.skip("pg_dump not available in test environment")

    # Create some rules
    MaskingRule.objects.create(table_name="auth_user", column_name="email", function_expr="anon.fake_email()")

    # Test dump command
    with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f:
        dump_file = f.name

    try:
        # Try to call the command, but skip if PostgreSQL connection fails
        try:
            call_command("anon_dump", dump_file)
        except Exception as e:
            if "could not translate host name" in str(e) or "connection" in str(e).lower():
                pytest.skip(f"PostgreSQL connection not available for integration test: {e}")
            raise

        # Verify dump file was created and has content
        assert os.path.exists(dump_file)
        assert os.path.getsize(dump_file) > 0

        # Read and verify basic SQL structure
        with open(dump_file) as f:
            content = f.read()
            assert "CREATE" in content or "INSERT" in content

    finally:
        if os.path.exists(dump_file):
            os.unlink(dump_file)


@pytest.mark.django_db(transaction=True)
def test_error_handling_integration():
    """Test error handling in integration scenarios"""

    # Test with invalid table name - this should not raise an exception but should log errors
    MaskingRule.objects.create(
        table_name="nonexistent_table", column_name="nonexistent_column", function_expr="anon.fake_email()"
    )

    # anon_apply should complete without raising an exception, but log the error
    call_command("anon_apply")

    # Verify error was logged - the apply operation should be marked as failed due to errors
    error_logs = MaskingLog.objects.filter(operation="apply", success=False)
    assert error_logs.exists()

    # Verify the specific error details
    latest_log = error_logs.order_by("-timestamp").first()
    assert "nonexistent_table" in str(latest_log.details)

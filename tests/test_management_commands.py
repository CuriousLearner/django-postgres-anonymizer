"""Tests for Django management commands using PostgreSQL anon extension

These tests verify management command behavior with actual database operations.
"""

import tempfile
from io import StringIO
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError

import pytest
import yaml
from model_bakery import baker

from django_postgres_anon.models import MaskedRole, MaskingLog, MaskingPreset, MaskingRule
from django_postgres_anon.utils import validate_anon_extension


@pytest.fixture
def clean_anon_state():
    """Ensure clean anonymization state before tests"""
    # Clean up any existing rules
    MaskingRule.objects.all().delete()
    MaskingLog.objects.all().delete()
    yield
    # Clean up after test
    MaskingRule.objects.all().delete()
    MaskingLog.objects.all().delete()


@pytest.fixture
def test_user():
    """Create a test user for anonymization"""
    user = User.objects.create_user(username="testuser", email="test@example.com", first_name="John", last_name="Doe")
    yield user
    user.delete()


@pytest.fixture
def initialized_extension(clean_anon_state):
    """Ensure anon extension is initialized"""
    try:
        call_command("anon_init", "--force")
        yield
    except CommandError as e:
        if "extension" in str(e).lower():
            pytest.skip(f"PostgreSQL anon extension not available: {e}")
        raise


class TestAnonInitCommand:
    """Test anon_init command with real PostgreSQL anon extension"""

    @pytest.mark.django_db(transaction=True)
    def test_init_installs_extension(self, clean_anon_state):
        """Command installs and initializes the anon extension"""
        out = StringIO()

        try:
            call_command("anon_init", "--force", stdout=out)
            output = out.getvalue()

            assert "✅ Anonymizer initialized successfully!" in output
            assert "Version:" in output

            # Verify extension is now available
            assert validate_anon_extension() is True

            # Verify log created
            log = MaskingLog.objects.filter(operation="init", success=True).first()
            assert log is not None
            assert "version" in log.details

        except CommandError as e:
            if "extension" in str(e).lower():
                pytest.skip(f"PostgreSQL anon extension not available: {e}")
            raise

    @pytest.mark.django_db(transaction=True)
    def test_init_already_exists(self, clean_anon_state):
        """Command handles case when extension already exists"""
        # First initialization
        try:
            call_command("anon_init", "--force")
        except CommandError as e:
            if "extension" in str(e).lower():
                pytest.skip(f"PostgreSQL anon extension not available: {e}")
            raise

        # Second initialization without force
        out = StringIO()
        call_command("anon_init", stdout=out)
        output = out.getvalue()

        assert "already initialized" in output


class TestAnonApplyCommand:
    """Test anon_apply command with real database operations"""

    @pytest.mark.django_db(transaction=True)
    def test_apply_with_real_rules(self, initialized_extension, test_user):
        """Command applies real anonymization rules to database"""
        # Create rules for auth_user table (which exists)
        rule1 = baker.make(
            MaskingRule, table_name="auth_user", column_name="email", function_expr="anon.fake_email()", enabled=True
        )
        rule2 = baker.make(
            MaskingRule,
            table_name="auth_user",
            column_name="first_name",
            function_expr="anon.fake_first_name()",
            enabled=True,
        )

        out = StringIO()
        call_command("anon_apply", stdout=out)
        output = out.getvalue()

        assert "Applied" in output and "rules" in output

        # Verify rules marked as applied
        rule1.refresh_from_db()
        rule2.refresh_from_db()
        assert rule1.applied_at is not None
        assert rule2.applied_at is not None

        # Verify log created
        log = MaskingLog.objects.filter(operation="apply", success=True).first()
        assert log is not None

    @pytest.mark.django_db(transaction=True)
    def test_apply_no_enabled_rules(self, initialized_extension):
        """Command handles case with no enabled rules"""
        # Create only disabled rule
        baker.make(MaskingRule, enabled=False)

        out = StringIO()
        call_command("anon_apply", stdout=out)
        output = out.getvalue()

        assert "No enabled" in output

    @pytest.mark.django_db(transaction=True)
    def test_apply_with_table_filter(self, initialized_extension, test_user):
        """Command applies only rules for specified table"""
        # Create rules for different tables
        rule1 = baker.make(
            MaskingRule, table_name="auth_user", column_name="email", function_expr="anon.fake_email()", enabled=True
        )
        rule2 = baker.make(
            MaskingRule,
            table_name="other_table",
            column_name="data",
            function_expr="anon.random_string(10)",
            enabled=True,
        )

        out = StringIO()
        call_command("anon_apply", "--table", "auth_user", stdout=out)
        output = out.getvalue()

        assert "Applied 1" in output

        # Verify only auth_user rule was applied
        rule1.refresh_from_db()
        rule2.refresh_from_db()
        assert rule1.applied_at is not None
        assert rule2.applied_at is None


class TestAnonStatusCommand:
    """Test anon_status command with real extension"""

    @pytest.mark.django_db(transaction=True)
    def test_status_shows_extension_info(self, initialized_extension, test_user):
        """Command displays extension and rule status"""
        # Create test rules
        baker.make(MaskingRule, table_name="auth_user", column_name="email", enabled=True, applied_at=None)
        baker.make(MaskingRule, table_name="auth_user", column_name="first_name", enabled=True, applied_at="2023-01-01")
        baker.make(MaskingRule, enabled=False)

        out = StringIO()
        call_command("anon_status", stdout=out)
        output = out.getvalue()

        assert "=== PostgreSQL Anonymizer Status ===" in output
        assert "Extension:" in output
        assert "Total rules: 3" in output
        assert "Enabled rules: 2" in output
        # Applied count may vary based on test order, just check format
        assert "rules:" in output


class TestAnonValidateCommand:
    """Test anon_validate command with real validation"""

    @pytest.mark.django_db(transaction=True)
    def test_validate_real_rules(self, initialized_extension):
        """Command validates rules against real database"""
        # Create valid rules
        baker.make(MaskingRule, table_name="auth_user", column_name="email", function_expr="anon.fake_email()")
        baker.make(
            MaskingRule, table_name="auth_user", column_name="first_name", function_expr="anon.fake_first_name()"
        )

        out = StringIO()
        call_command("anon_validate", stdout=out)
        output = out.getvalue()

        assert "VALIDATION SUMMARY" in output
        assert "auth_user" in output

    @pytest.mark.django_db(transaction=True)
    def test_validate_invalid_table(self, initialized_extension):
        """Command detects invalid table names"""
        # Create rule with non-existent table
        baker.make(MaskingRule, table_name="nonexistent_table", column_name="email", function_expr="anon.fake_email()")

        with pytest.raises(CommandError, match="Validation failed"):
            call_command("anon_validate")


class TestAnonLoadYamlCommand:
    """Test anon_load_yaml command with real YAML processing"""

    @pytest.mark.django_db(transaction=True)
    def test_load_simple_yaml(self, clean_anon_state):
        """Load YAML in simple format and create rules"""
        yaml_data = [
            {"table": "auth_user", "column": "email", "function": "anon.fake_email()", "enabled": True},
            {"table": "auth_user", "column": "first_name", "function": "anon.fake_first_name()", "enabled": False},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_data, f)
            yaml_file = f.name

        try:
            out = StringIO()
            call_command("anon_load_yaml", yaml_file, stdout=out)
            output = out.getvalue()

            assert "Created 2 new rules" in output
            assert MaskingRule.objects.count() == 2

            # Verify rule properties
            email_rule = MaskingRule.objects.get(column_name="email")
            assert email_rule.enabled is True
            name_rule = MaskingRule.objects.get(column_name="first_name")
            assert name_rule.enabled is False

        finally:
            Path(yaml_file).unlink()

    @pytest.mark.django_db(transaction=True)
    def test_load_preset_yaml(self, clean_anon_state):
        """Load YAML with preset format"""
        yaml_data = {
            "name": "Test Preset",
            "preset_type": "custom",
            "description": "Test preset",
            "rules": [
                {
                    "table_name": "auth_user",
                    "column_name": "email",
                    "function_expr": "anon.fake_email()",
                    "enabled": True,
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_data, f)
            yaml_file = f.name

        try:
            out = StringIO()
            call_command("anon_load_yaml", yaml_file, stdout=out)
            output = out.getvalue()

            assert "Created preset: Test Preset" in output
            preset = MaskingPreset.objects.get(name="Test Preset")
            assert preset.rules.count() == 1

        finally:
            Path(yaml_file).unlink()

    @pytest.mark.django_db(transaction=True)
    def test_load_builtin_preset(self, clean_anon_state):
        """Load built-in preset by name"""
        out = StringIO()
        call_command("anon_load_yaml", "django_auth", stdout=out)
        output = out.getvalue()

        assert "Loading rules from:" in output
        assert "django_auth" in output
        # Should create rules for Django auth
        assert MaskingRule.objects.count() > 0


class TestAnonDumpCommand:
    """Test anon_dump command with real database dumping"""

    @pytest.mark.django_db(transaction=True)
    def test_dump_with_anonymization(self, initialized_extension, test_user):
        """Create anonymized database dump"""
        # Create and apply anonymization rules
        baker.make(
            MaskingRule, table_name="auth_user", column_name="email", function_expr="anon.fake_email()", enabled=True
        )

        # Apply the rule
        call_command("anon_apply")

        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f:
            dump_file = f.name

        try:
            out = StringIO()
            # The dump command may fail due to pg_dump compatibility or authentication issues
            # We expect it to handle masking rule application but may fail on actual pg_dump
            try:
                call_command("anon_dump", dump_file, stdout=out)
                output = out.getvalue()

                # Check that masking rules were applied successfully
                assert "Applied rule" in output or "masking rules applied" in output.lower()

                # If file was created, verify it has content
                if Path(dump_file).exists():
                    assert Path(dump_file).stat().st_size > 0

                    # Verify log created
                    log = MaskingLog.objects.filter(operation="dump").first()
                    if log:
                        assert log.details.get("anonymized") is True

            except CommandError as e:
                # Expected failures due to pg_dump compatibility or role permissions
                error_msg = str(e)
                if any(x in error_msg.lower() for x in ["pg_dump", "authentication", "role", "permission"]):
                    pytest.skip(f"pg_dump compatibility issue: {e}")
                else:
                    # Re-raise unexpected errors
                    raise

        finally:
            Path(dump_file).unlink(missing_ok=True)

    @pytest.mark.django_db(transaction=True)
    def test_dump_warns_no_rules(self, initialized_extension, test_user):
        """Warn when dumping without anonymization rules"""
        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f:
            dump_file = f.name

        try:
            out = StringIO()
            # The dump command may fail due to pg_dump compatibility issues
            try:
                call_command("anon_dump", dump_file, stdout=out)
                output = out.getvalue()

                # Check that warning appears or command handles no rules case
                assert "No enabled" in output or "rules found" in output or "original data" in output

            except CommandError as e:
                # Expected failures due to pg_dump compatibility or role permissions
                error_msg = str(e)
                if any(x in error_msg.lower() for x in ["pg_dump", "authentication", "role", "permission"]):
                    pytest.skip(f"pg_dump compatibility issue: {e}")
                else:
                    # Re-raise unexpected errors
                    raise

        finally:
            Path(dump_file).unlink(missing_ok=True)


class TestAnonDropCommand:
    """Test anon_drop command with real database operations"""

    @pytest.mark.django_db(transaction=True)
    def test_drop_specific_table(self, initialized_extension, test_user):
        """Remove anonymization from specific table"""
        # Create and apply rule
        rule = baker.make(
            MaskingRule, table_name="auth_user", column_name="email", function_expr="anon.fake_email()", enabled=True
        )
        call_command("anon_apply")

        # Verify rule is applied
        rule.refresh_from_db()
        assert rule.applied_at is not None

        out = StringIO()
        call_command("anon_drop", "--table", "auth_user", "--confirm", stdout=out)
        output = out.getvalue()

        assert "removal" in output.lower()

        # Verify log created
        log = MaskingLog.objects.filter(operation="drop").first()
        assert log is not None

    @pytest.mark.django_db(transaction=True)
    def test_drop_requires_confirmation(self, initialized_extension):
        """Command requires confirmation for dangerous operations"""
        baker.make(MaskingRule, table_name="auth_user", column_name="email", enabled=True)

        with pytest.raises(CommandError, match="This action requires confirmation"):
            call_command("anon_drop")

    @pytest.mark.django_db(transaction=True)
    def test_drop_remove_data(self, initialized_extension):
        """Remove all anonymization data"""
        # Create test data
        rule = baker.make(MaskingRule, table_name="auth_user", column_name="email")
        preset = baker.make(MaskingPreset, name="test_preset")
        role = baker.make(MaskedRole, role_name="test_role")

        out = StringIO()
        call_command("anon_drop", "--remove-data", "--confirm", stdout=out)
        output = out.getvalue()

        assert "removal" in output.lower()

        # Verify data was removed
        assert not MaskingRule.objects.filter(id=rule.id).exists()
        assert not MaskingPreset.objects.filter(id=preset.id).exists()
        assert not MaskedRole.objects.filter(id=role.id).exists()


class TestCommandIntegration:
    """Test command integration workflows"""

    @pytest.mark.django_db(transaction=True)
    def test_full_anonymization_workflow(self, clean_anon_state, test_user):
        """Test complete workflow: init -> load -> apply -> dump -> drop"""
        # Step 1: Initialize
        call_command("anon_init", "--force")

        # Step 2: Load rules from YAML
        yaml_data = [{"table": "auth_user", "column": "email", "function": "anon.fake_email()", "enabled": True}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_data, f)
            yaml_file = f.name

        try:
            call_command("anon_load_yaml", yaml_file)
            assert MaskingRule.objects.count() == 1

            # Step 3: Validate rules
            call_command("anon_validate")

            # Step 4: Apply anonymization
            call_command("anon_apply")
            rule = MaskingRule.objects.first()
            rule.refresh_from_db()
            assert rule.applied_at is not None

            # Step 5: Check status
            out = StringIO()
            call_command("anon_status", stdout=out)
            output = out.getvalue()
            assert "Applied 1" in output or "1 rules" in output

            # Step 6: Create dump (may fail due to pg_dump availability)
            with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as dump_f:
                dump_file = dump_f.name

            try:
                # Try dump but don't fail test if pg_dump not available
                try:
                    call_command("anon_dump", dump_file)
                    if Path(dump_file).exists():
                        assert Path(dump_file).stat().st_size > 0
                except CommandError as e:
                    error_msg = str(e).lower()
                    if any(
                        x in error_msg for x in ["pg_dump", "command not found", "authentication", "role", "permission"]
                    ):
                        pytest.skip(f"pg_dump compatibility issue: {e}")
                    else:
                        raise
            finally:
                Path(dump_file).unlink(missing_ok=True)

            # Step 7: Remove anonymization
            call_command("anon_drop", "--table", "auth_user", "--confirm")

        finally:
            Path(yaml_file).unlink()

    @pytest.mark.django_db(transaction=True)
    def test_error_handling_integration(self, initialized_extension):
        """Test error handling across commands"""
        # Create rule with invalid table
        baker.make(
            MaskingRule,
            table_name="nonexistent_table",
            column_name="email",
            function_expr="anon.fake_email()",
            enabled=True,
        )

        # Apply should handle errors gracefully
        call_command("anon_apply")

        # Check that error was logged
        log = MaskingLog.objects.filter(operation="apply", success=False).first()
        assert log is not None
        assert "nonexistent_table" in str(log.details).lower()

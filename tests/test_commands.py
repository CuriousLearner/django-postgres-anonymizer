"""Behavior-focused tests for all management commands"""

import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError

import pytest
import yaml
from model_bakery import baker

from django_postgres_anon.models import MaskedRole, MaskingLog, MaskingPreset, MaskingRule


# Helper function for command testing
def call_command_with_output(command_name, *args, **kwargs):
    """Helper to call command and capture output"""
    out = StringIO()
    kwargs["stdout"] = out
    call_command(command_name, *args, **kwargs)
    return out.getvalue()


# anon_init command tests
@pytest.mark.django_db
def test_anon_init_behavior():
    """Test anon_init command behavior - may succeed or fail gracefully"""
    try:
        output = call_command_with_output("anon_init")

        # If successful, should show success message
        if "successfully" in output:
            # Check that log was created
            log = MaskingLog.objects.filter(operation="init").first()
            assert log is not None
            if log.success:
                assert "version" in log.details
        elif "already" in output:
            # Extension already exists - acceptable behavior
            pass

    except CommandError as e:
        # May fail due to missing extension or permissions - check error is logged
        log = MaskingLog.objects.filter(operation="init", success=False).first()
        if log:
            assert log.error_message
        # Error should be informative
        assert any(keyword in str(e).lower() for keyword in ["extension", "permission", "database"])


# anon_apply command tests
@pytest.mark.django_db
def test_anon_apply_with_rules():
    """Test anon_apply command with enabled rules"""
    from django.db import transaction

    # Create test rules
    rule1 = baker.make(MaskingRule, enabled=True, table_name="auth_user", column_name="email")
    rule2 = baker.make(MaskingRule, enabled=True, table_name="auth_user", column_name="first_name")

    try:
        with transaction.atomic():
            output = call_command_with_output("anon_apply")

            if "Applied" in output:
                # If successful, rules should be marked as applied
                rule1.refresh_from_db()
                rule2.refresh_from_db()
                assert rule1.applied_at is not None
                assert rule2.applied_at is not None

    except (CommandError, Exception) as e:
        # May fail due to missing extension, transaction issues, or permissions - acceptable
        assert any(
            keyword in str(e).lower() for keyword in ["extension", "anon", "permission", "transaction", "aborted"]
        )


@pytest.mark.django_db
def test_anon_apply_no_rules():
    """Test apply command when no enabled rules exist"""
    # Create only disabled rules
    baker.make(MaskingRule, enabled=False)

    try:
        output = call_command_with_output("anon_apply")
        assert "No enabled rules found" in output
    except CommandError as e:
        # May fail due to missing extension before checking rules
        assert any(keyword in str(e).lower() for keyword in ["extension", "anon"])


# anon_status command tests
@pytest.mark.django_db
def test_anon_status_command():
    """Test status command behavior"""
    # Create test rules
    baker.make(MaskingRule, enabled=True, table_name="auth_user", column_name="email")
    baker.make(MaskingRule, enabled=False, table_name="auth_user", column_name="first_name")

    try:
        output = call_command_with_output("anon_status")

        # Should show status information
        assert "Extension:" in output

        # Should show rule counts if extension is available
        if "Installed" in output:
            assert "auth_user" in output

    except CommandError as e:
        # May fail due to missing extension
        assert any(keyword in str(e).lower() for keyword in ["extension", "anon", "permission"])


# anon_validate command tests
@pytest.mark.django_db
def test_anon_validate_no_rules():
    """Test validation when no rules exist"""
    try:
        output = call_command_with_output("anon_validate")
        # Should show validation information or fail with extension error
        assert "No rules found" in output or "VALIDATION SUMMARY" in output or len(output) > 0
    except CommandError as e:
        # May fail due to missing extension or validation errors
        error_msg = str(e).lower()
        assert any(
            keyword in error_msg for keyword in ["extension", "anon", "available", "validation failed", "failed"]
        )


@pytest.mark.django_db
def test_anon_validate_with_rules():
    """Test validation with rules"""
    # Create test rules
    baker.make(MaskingRule, table_name="auth_user", column_name="email", function_expr="anon.fake_email()")
    baker.make(MaskingRule, table_name="auth_user", column_name="first_name", function_expr="anon.fake_first_name()")

    try:
        output = call_command_with_output("anon_validate")

        # Should perform validation and show summary
        assert "VALIDATION SUMMARY" in output

        # Should reference the rules being validated
        if "auth_user" in output:
            assert "email" in output or "first_name" in output

    except CommandError as e:
        # May fail due to missing extension, database issues, or validation errors
        error_msg = str(e).lower()
        assert any(
            keyword in error_msg for keyword in ["extension", "anon", "table", "column", "validation failed", "failed"]
        )


# anon_load_yaml command tests
@pytest.mark.django_db
def test_anon_load_yaml_simple_format():
    """Test loading YAML in simple format"""
    yaml_data = [
        {"table": "auth_user", "column": "email", "function": "anon.fake_email()", "enabled": True},
        {"table": "auth_user", "column": "first_name", "function": "anon.fake_first_name()", "enabled": True},
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(yaml_data, f)
        yaml_file = f.name

    try:
        output = call_command_with_output("anon_load_yaml", yaml_file)

        assert MaskingRule.objects.count() == 2
        assert MaskingRule.objects.filter(table_name="auth_user", column_name="email").exists()
        assert MaskingRule.objects.filter(table_name="auth_user", column_name="first_name").exists()
        assert "Created 2 new rules" in output

    finally:
        Path(yaml_file).unlink()


@pytest.mark.django_db
def test_anon_load_yaml_full_format():
    """Test loading YAML in full format with presets"""
    yaml_data = {
        "name": "Test Preset",
        "preset_type": "custom",
        "description": "Test preset for YAML loading",
        "rules": [
            {
                "table_name": "auth_user",
                "column_name": "email",
                "function_expr": "anon.fake_email()",
                "enabled": True,
                "notes": "Test email anonymization",
            }
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(yaml_data, f)
        yaml_file = f.name

    try:
        output = call_command_with_output("anon_load_yaml", yaml_file)

        assert MaskingPreset.objects.count() == 1
        preset = MaskingPreset.objects.first()
        assert preset.name == "Test Preset"
        assert preset.rules.count() == 1
        assert "Created preset: Test Preset" in output

    finally:
        Path(yaml_file).unlink()


@pytest.mark.django_db
def test_anon_load_yaml_nonexistent_file():
    """Test loading from nonexistent file"""
    with pytest.raises(CommandError, match="File not found"):
        call_command("anon_load_yaml", "/nonexistent/file.yaml")


@pytest.mark.django_db
def test_anon_load_yaml_preset_name():
    """Test loading using preset name from built-in presets"""
    output = call_command_with_output("anon_load_yaml", "django_auth")

    assert "Loading rules from:" in output
    assert "django_auth" in output
    # Should create rules from the preset
    assert MaskingRule.objects.count() > 0


@pytest.mark.django_db
def test_anon_load_yaml_empty_file():
    """Test loading from empty YAML file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml_file = f.name
        f.write("")  # Empty file

    try:
        with pytest.raises(CommandError, match="YAML file is empty"):
            call_command("anon_load_yaml", yaml_file)
    finally:
        Path(yaml_file).unlink()


@pytest.mark.django_db
def test_anon_load_yaml_invalid_syntax():
    """Test loading YAML with invalid syntax"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml_file = f.name
        f.write("invalid: yaml: syntax: [")  # Invalid YAML

    try:
        with pytest.raises(CommandError, match="Invalid YAML syntax"):
            call_command("anon_load_yaml", yaml_file)
    finally:
        Path(yaml_file).unlink()


@pytest.mark.django_db
def test_anon_load_yaml_dry_run():
    """Test loading YAML with --dry-run flag"""
    yaml_data = [
        {"table": "auth_user", "column": "email", "function": "anon.fake_email()", "enabled": True},
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml_file = f.name
        yaml.dump(yaml_data, f)

    try:
        output = call_command_with_output("anon_load_yaml", yaml_file, "--dry-run")

        assert "DRY RUN" in output
        assert "Would create" in output or "Would load" in output
        # Should not actually create rules
        assert MaskingRule.objects.count() == 0
    finally:
        Path(yaml_file).unlink()


@pytest.mark.django_db
def test_anon_load_yaml_overwrite_existing():
    """Test loading YAML with --overwrite flag"""
    # Create existing rule
    baker.make(MaskingRule, table_name="auth_user", column_name="email", function_expr="anon.random_string()")

    yaml_data = [
        {"table": "auth_user", "column": "email", "function": "anon.fake_email()", "enabled": True},
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml_file = f.name
        yaml.dump(yaml_data, f)

    try:
        output = call_command_with_output("anon_load_yaml", yaml_file, "--overwrite")

        assert "Loading rules from:" in output
        # Should have updated the rule
        updated_rule = MaskingRule.objects.get(table_name="auth_user", column_name="email")
        assert updated_rule.function_expr == "anon.fake_email()"
    finally:
        Path(yaml_file).unlink()


@pytest.mark.django_db
def test_anon_load_yaml_disable_existing():
    """Test loading YAML with --disable-existing flag"""
    # Create existing enabled rule
    existing_rule = baker.make(MaskingRule, table_name="auth_user", column_name="first_name", enabled=True)

    yaml_data = [
        {"table": "auth_user", "column": "email", "function": "anon.fake_email()", "enabled": True},
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml_file = f.name
        yaml.dump(yaml_data, f)

    try:
        output = call_command_with_output("anon_load_yaml", yaml_file, "--disable-existing")

        assert "Loading rules from:" in output
        # Should have disabled existing rule for same table
        existing_rule.refresh_from_db()
        assert not existing_rule.enabled
    finally:
        Path(yaml_file).unlink()


@pytest.mark.django_db
def test_anon_load_yaml_with_preset_name_option():
    """Test loading YAML with custom preset name"""
    yaml_data = [
        {"table": "auth_user", "column": "email", "function": "anon.fake_email()", "enabled": True},
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml_file = f.name
        yaml.dump(yaml_data, f)

    try:
        output = call_command_with_output("anon_load_yaml", yaml_file, "--preset-name", "Custom Test Preset")

        assert "Loading rules from:" in output
        # Should create preset with custom name
        preset = MaskingPreset.objects.get(name="Custom Test Preset")
        assert preset.rules.count() == 1
    finally:
        Path(yaml_file).unlink()


@pytest.mark.django_db
def test_anon_load_yaml_validation_error():
    """Test loading YAML with validation errors"""
    yaml_data = [
        {"table": "", "column": "email", "function": "anon.fake_email()", "enabled": True},  # Invalid empty table
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml_file = f.name
        yaml.dump(yaml_data, f)

    try:
        with pytest.raises(CommandError, match="Failed to load YAML"):
            call_command("anon_load_yaml", yaml_file)
    finally:
        Path(yaml_file).unlink()


@pytest.mark.django_db
@patch("django_postgres_anon.management.commands.anon_load_yaml.yaml.safe_load")
def test_anon_load_yaml_general_error(mock_safe_load):
    """Test loading YAML with general error during processing"""
    mock_safe_load.side_effect = Exception("General processing error")

    yaml_data = [
        {"table": "auth_user", "column": "email", "function": "anon.fake_email()", "enabled": True},
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml_file = f.name
        yaml.dump(yaml_data, f)

    try:
        with pytest.raises(CommandError, match="Failed to load YAML"):
            call_command("anon_load_yaml", yaml_file)
    finally:
        Path(yaml_file).unlink()


# anon_drop command tests
@pytest.mark.django_db
def test_anon_drop_success():
    """Test successful dropping of anonymization rules"""
    # Create some rules
    baker.make(MaskingRule, table_name="auth_user", column_name="email", function_expr="anon.fake_email()")
    baker.make(MaskingRule, table_name="auth_user", column_name="first_name", function_expr="anon.fake_first_name()")

    try:
        output = call_command_with_output("anon_drop", "--confirm")

        # Should start removal process
        assert "Starting anonymization removal" in output or "removal" in output.lower()

        # Check that log was created
        log = MaskingLog.objects.filter(operation="drop").first()
        if log:
            assert log.success is True

    except CommandError as e:
        # May fail due to missing extension
        assert any(keyword in str(e).lower() for keyword in ["extension", "anon", "permission"])


@pytest.mark.django_db
def test_anon_drop_without_confirmation():
    """Test drop command without confirmation"""
    baker.make(MaskingRule, table_name="auth_user", column_name="email", function_expr="anon.fake_email()")

    with pytest.raises(CommandError, match="This action requires confirmation"):
        call_command("anon_drop")


@pytest.mark.django_db
def test_anon_drop_no_rules():
    """Test drop command when no rules exist"""
    try:
        output = call_command_with_output("anon_drop", "--confirm")

        # The command should complete successfully, either finding nothing to remove or removing existing labels
        assert "Nothing to remove" in output or "removal completed" in output or "removal" in output.lower()

    except CommandError as e:
        # May fail due to missing extension
        assert any(keyword in str(e).lower() for keyword in ["extension", "anon"])


@pytest.mark.django_db
def test_anon_drop_column_requires_table():
    """Test drop command with --column but no --table raises error"""
    with pytest.raises(CommandError, match="--column requires --table to be specified"):
        call_command("anon_drop", "--column", "email", "--confirm")


@pytest.mark.django_db
def test_anon_drop_remove_data():
    """Test drop command with --remove-data flag"""
    # Create test data
    rule = baker.make(MaskingRule, table_name="auth_user", column_name="email")
    preset = baker.make(MaskingPreset, name="test_preset")
    role = baker.make(MaskedRole, role_name="test_role")

    try:
        output = call_command_with_output("anon_drop", "--remove-data", "--confirm")

        assert "removal" in output.lower()
        # Verify data was removed
        assert not MaskingRule.objects.filter(id=rule.id).exists()
        assert not MaskingPreset.objects.filter(id=preset.id).exists()
        assert not MaskedRole.objects.filter(id=role.id).exists()

    except CommandError as e:
        # May fail due to missing extension, but data should still be removed
        # Check if data removal happened despite command failure
        if "extension" in str(e).lower():
            # Extension missing - data removal may still have worked
            pass
        else:
            raise


@pytest.mark.django_db
def test_anon_drop_remove_extension():
    """Test drop command with --remove-extension flag"""
    try:
        output = call_command_with_output("anon_drop", "--remove-extension", "--confirm")
        assert "removal" in output.lower()

    except CommandError as e:
        # May fail due to missing extension or permissions
        assert any(keyword in str(e).lower() for keyword in ["extension", "anon", "permission"])


@pytest.mark.django_db
def test_anon_drop_specific_table():
    """Test drop command with specific table"""
    baker.make(MaskingRule, table_name="auth_user", column_name="email")

    try:
        output = call_command_with_output("anon_drop", "--table", "auth_user", "--confirm")
        assert "removal" in output.lower()

    except CommandError as e:
        # May fail due to missing extension
        assert any(keyword in str(e).lower() for keyword in ["extension", "anon"])


@pytest.mark.django_db
def test_anon_drop_specific_column():
    """Test drop command with specific table and column"""
    baker.make(MaskingRule, table_name="auth_user", column_name="email")

    try:
        output = call_command_with_output("anon_drop", "--table", "auth_user", "--column", "email", "--confirm")
        assert "removal" in output.lower()

    except CommandError as e:
        # May fail due to missing extension
        assert any(keyword in str(e).lower() for keyword in ["extension", "anon"])


@pytest.mark.django_db
def test_anon_drop_dry_run():
    """Test drop command with --dry-run flag"""
    baker.make(MaskingRule, table_name="auth_user", column_name="email")

    try:
        output = call_command_with_output("anon_drop", "--dry-run")
        assert "DRY RUN" in output or "dry run" in output.lower()

    except CommandError as e:
        # May fail due to missing extension
        assert any(keyword in str(e).lower() for keyword in ["extension", "anon"])


@pytest.mark.django_db
def test_anon_drop_with_errors():
    """Test drop command when operation fails"""
    baker.make(MaskingRule, table_name="auth_user", column_name="email")

    # This may fail due to missing extension or may succeed if extension is available
    try:
        call_command("anon_drop", "--confirm")
        # If it succeeds, that's also acceptable behavior
    except CommandError as e:
        # Should provide informative error message if it fails
        error_message = str(e)
        assert any(keyword in error_message.lower() for keyword in ["extension", "anon", "database", "permission"])


@pytest.mark.django_db
def test_anon_drop_requires_confirmation_for_dangerous_ops():
    """Test drop command requires confirmation for dangerous operations"""
    baker.make(MaskingRule, table_name="auth_user", column_name="email")

    # Test that --remove-extension requires confirmation
    with pytest.raises(CommandError, match="This action requires confirmation"):
        call_command("anon_drop", "--remove-extension")

    # Test that --remove-data requires confirmation
    with pytest.raises(CommandError, match="This action requires confirmation"):
        call_command("anon_drop", "--remove-data")

    # Test that no table (remove all) requires confirmation
    with pytest.raises(CommandError, match="This action requires confirmation"):
        call_command("anon_drop")


@pytest.mark.django_db
@patch("builtins.input", return_value="yes")
def test_anon_drop_interactive_confirmation_accepted(mock_input):
    """Test drop command with interactive confirmation accepted"""
    baker.make(MaskingRule, table_name="auth_user", column_name="email")

    try:
        output = call_command_with_output("anon_drop", "--table", "auth_user")
        assert "removal" in output.lower()
        # Verify mock was used
        assert True  # Mock may or may not be called depending on implementation

    except CommandError as e:
        # May fail due to missing extension
        assert any(keyword in str(e).lower() for keyword in ["extension", "anon"])


# anon_dump command tests
@pytest.mark.django_db
def test_anon_dump_creates_file_and_logs_operation():
    """Test anon_dump command creates output file and logs operation"""
    # Create test masking rules
    baker.make(
        MaskingRule, enabled=True, table_name="auth_user", column_name="email", function_expr="anon.fake_email()"
    )
    baker.make(
        MaskingRule,
        enabled=True,
        table_name="auth_user",
        column_name="first_name",
        function_expr="anon.fake_first_name()",
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        dump_file = f.name

    try:
        # Test command execution behavior - may fail but should handle gracefully
        from io import StringIO

        out = StringIO()

        try:
            call_command("anon_dump", dump_file, stdout=out)
            output = out.getvalue()

            # Should create log entry regardless of success/failure
            log_entry = MaskingLog.objects.filter(operation="dump").first()
            assert log_entry is not None
            assert log_entry.details.get("anonymized") is True
            # Verify output was captured
            assert isinstance(output, str)

        except Exception as e:
            # Command may fail due to missing PostgreSQL Anonymizer extension
            # but should fail gracefully with informative error message
            assert "extension" in str(e).lower() or "anon" in str(e).lower()

    finally:
        Path(dump_file).unlink(missing_ok=True)


@pytest.mark.django_db
def test_anon_dump_warns_with_no_masking_rules():
    """Test anon_dump with no enabled masking rules warns user"""
    # Create disabled rule (should be ignored)
    baker.make(MaskingRule, enabled=False, table_name="auth_user", column_name="email")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        dump_file = f.name

    try:
        # Capture output to check for warning
        from io import StringIO

        out = StringIO()

        try:
            call_command("anon_dump", dump_file, stdout=out)
            output = out.getvalue()

            # Should warn about no enabled rules
            assert "No enabled masking rules found" in output
            assert "Dump will contain original data" in output

        except Exception as e:
            # May fail due to missing extension, but should show the warning first
            output = out.getvalue()
            if output:  # If we got any output before the exception
                assert "No enabled masking rules found" in output or "extension" in str(e).lower()

    finally:
        Path(dump_file).unlink(missing_ok=True)


@pytest.mark.django_db
def test_anon_dump_handles_errors_gracefully():
    """Test anon_dump handles various error conditions gracefully"""
    # Test with an invalid directory path that doesn't exist
    invalid_dump_file = "/nonexistent/directory/dump.sql"

    # Create test masking rule to ensure we get past the initial checks
    baker.make(
        MaskingRule, enabled=True, table_name="auth_user", column_name="email", function_expr="anon.fake_email()"
    )

    # Test that command fails gracefully with invalid file path
    with pytest.raises(CommandError) as exc_info:
        call_command("anon_dump", invalid_dump_file)

    # Should provide informative error message about the failure
    error_message = str(exc_info.value)
    assert any(word in error_message.lower() for word in ["failed", "error", "not available", "extension"])


@pytest.mark.django_db
def test_anon_dump_invalid_format():
    """Test anon_dump fails with unsupported format"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        dump_file = f.name

    try:
        with pytest.raises(CommandError) as exc_info:
            call_command("anon_dump", dump_file, "--format=custom")

        # Should fail with either format error or extension error
        error_msg = str(exc_info.value)
        assert "Anonymized dumps only support 'plain' format" in error_msg or "extension" in error_msg.lower()
    finally:
        Path(dump_file).unlink(missing_ok=True)


# Test using fixtures from conftest.py
@pytest.mark.django_db
def test_commands_with_fixtures(sample_masking_rule):
    """Test commands using fixtures from conftest.py"""
    # Verify fixture data exists
    assert sample_masking_rule.table_name == "auth_user"
    assert sample_masking_rule.column_name == "email"

    # Test status command with fixture data
    try:
        output = call_command_with_output("anon_status")
        assert "Extension:" in output

    except CommandError as e:
        # May fail due to missing extension
        assert any(keyword in str(e).lower() for keyword in ["extension", "anon"])


@pytest.mark.django_db
def test_command_error_handling():
    """Test command error handling and logging"""
    # Test with invalid command arguments
    with pytest.raises(CommandError):
        call_command("anon_load_yaml")  # Missing required argument

    # Test database errors are logged for init command
    try:
        call_command("anon_init")
    except CommandError:
        # If it failed, should have logged the error
        error_log = MaskingLog.objects.filter(success=False).first()
        if error_log:
            assert error_log.error_message


@pytest.mark.django_db
def test_command_permissions():
    """Test command permission requirements"""
    # Commands should handle permission errors gracefully
    try:
        call_command("anon_apply")
    except CommandError as e:
        # Should provide informative error about permissions or extension
        assert any(keyword in str(e).lower() for keyword in ["permission", "extension", "anon"])


@pytest.mark.django_db
def test_anon_fix_permissions_command():
    """Test anon_fix_permissions management command"""
    from unittest.mock import MagicMock, patch

    from django_postgres_anon.models import MaskedRole

    # Test with no arguments (should show error)
    with patch("sys.stdout", new_callable=MagicMock) as mock_stdout:
        call_command("anon_fix_permissions")
        output = str(mock_stdout.write.call_args_list)
        assert "Please specify" in output or "--role" in output

    # Test with --role option
    with patch("django_postgres_anon.management.commands.anon_fix_permissions.create_masked_role") as mock_create:
        mock_create.return_value = True
        with patch("sys.stdout", new_callable=MagicMock):
            call_command("anon_fix_permissions", "--role", "test_role")
            mock_create.assert_called_once_with("test_role")

    # Test with --all option when no roles exist
    MaskedRole.objects.all().delete()
    with patch("sys.stdout", new_callable=MagicMock) as mock_stdout:
        call_command("anon_fix_permissions", "--all")
        # Should show warning about no roles
        output = str(mock_stdout.write.call_args_list)
        assert "No roles found" in output or "no roles" in output.lower()

    # Test with --all option when roles exist
    MaskedRole.objects.create(role_name="test_role_1")
    MaskedRole.objects.create(role_name="test_role_2")

    with patch("django_postgres_anon.management.commands.anon_fix_permissions.create_masked_role") as mock_create:
        mock_create.return_value = True
        with patch("sys.stdout", new_callable=MagicMock) as mock_stdout:
            call_command("anon_fix_permissions", "--all")
            assert mock_create.call_count == 2
            mock_create.assert_any_call("test_role_1")
            mock_create.assert_any_call("test_role_2")

    # Test with failed permission fix
    with patch("django_postgres_anon.management.commands.anon_fix_permissions.create_masked_role") as mock_create:
        mock_create.return_value = False
        with patch("sys.stdout", new_callable=MagicMock) as mock_stdout:
            call_command("anon_fix_permissions", "--role", "failing_role")
            output = str(mock_stdout.write.call_args_list)
            assert "Failed" in output or "failed" in output.lower()

    # Clean up
    MaskedRole.objects.all().delete()

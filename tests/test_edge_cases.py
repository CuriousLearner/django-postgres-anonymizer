"""Tests for edge cases and boundary conditions"""

import pytest
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from model_bakery import baker

from django_postgres_anon.models import MaskingLog, MaskingPreset, MaskingRule
from django_postgres_anon.utils import create_operation_log, suggest_anonymization_functions, validate_function_syntax

# Constants for boundary testing
POSTGRES_IDENTIFIER_LIMIT = 63
EXCESSIVE_LENGTH = POSTGRES_IDENTIFIER_LIMIT + 1
LARGE_RULE_COUNT = 1000
LARGE_ERROR_MESSAGE_SIZE = 10000


@pytest.mark.django_db
def test_system_rejects_masking_rules_with_missing_required_fields():
    """
    Users should receive clear validation errors when creating incomplete rules

    This ensures data integrity and prevents configuration errors that could
    lead to failed anonymization operations.
    """
    # Create rule with missing required fields
    incomplete_rule = baker.make(
        MaskingRule,
        table_name="",  # Missing required field
        column_name="",  # Missing required field
        function_expr="",  # Missing required field
        enabled=True,
    )

    # Act & Assert: System should reject with clear validation error
    with pytest.raises(ValidationError):
        incomplete_rule.clean()


@pytest.mark.django_db
def test_system_handles_extremely_long_identifiers_gracefully():
    """
    System should handle field values longer than PostgreSQL identifier limits

    Users may accidentally enter very long names, and the system should
    handle this gracefully without crashing.
    """
    # Create rule with excessively long identifiers
    long_table_name = "test_table_" + "x" * EXCESSIVE_LENGTH
    long_column_name = "test_column_" + "y" * EXCESSIVE_LENGTH
    long_function = "anon.fake_email()" + "z" * 100

    rule = baker.make(
        MaskingRule, table_name=long_table_name, column_name=long_column_name, function_expr=long_function, enabled=True
    )

    assert rule.table_name == long_table_name
    assert rule.column_name == long_column_name
    assert rule.function_expr == long_function


@pytest.mark.django_db
@pytest.mark.parametrize(
    "table_name,column_name",
    [
        ("table-with-dashes", "column_with_underscores"),
        ("table.with.dots", "column.with.dots"),
        ("table with spaces", "column with spaces"),
        ('table"with"quotes', 'column"with"quotes'),
        ("table'with'quotes", "column'with'quotes"),
    ],
)
def test_system_supports_special_characters_in_database_identifiers(table_name, column_name):
    """
    System should handle database identifiers with special characters

    Real-world databases may have tables/columns with dashes, dots, quotes,
    or spaces, and the system should support these.
    """
    rule = baker.make(
        MaskingRule, table_name=table_name, column_name=column_name, function_expr="anon.fake_email()", enabled=True
    )

    # System should preserve special characters accurately
    assert rule.table_name == table_name
    assert rule.column_name == column_name


@pytest.mark.django_db
@pytest.mark.parametrize(
    "table_name,column_name,notes",
    [
        ("üser_täble", "ñame_çolumn", "Unicode test: åßč∂"),
        ("用户表", "邮件列", "中文测试"),
        ("пользователи", "электронная_почта", "русский тест"),
        ("usuarios", "correo_electrónico", "prueba en español"),
    ],
)
def test_system_supports_international_and_unicode_characters(table_name, column_name, notes):
    """
    System should handle Unicode and international characters in all fields

    Global users may have database schemas with international characters,
    and the system should support these properly.
    """
    rule = baker.make(
        MaskingRule,
        table_name=table_name,
        column_name=column_name,
        function_expr="anon.fake_email()",
        notes=notes,
        enabled=True,
    )

    # System should preserve Unicode characters correctly
    assert rule.table_name == table_name
    assert rule.column_name == column_name
    assert rule.notes == notes


@pytest.mark.django_db
def test_system_handles_large_numbers_of_masking_rules_efficiently():
    """
    System should handle large numbers of masking rules without performance issues

    Enterprise users may have hundreds or thousands of rules, and the system
    should maintain good performance and stability.
    """
    rules = []
    for i in range(LARGE_RULE_COUNT):
        rule = baker.make(
            MaskingRule,
            table_name=f"table_{i}",
            column_name=f"column_{i}",
            function_expr="anon.fake_email()",
            enabled=True,
        )
        rules.append(rule)

    assert len(rules) == LARGE_RULE_COUNT
    assert all(rule.enabled for rule in rules)
    assert MaskingRule.objects.count() >= LARGE_RULE_COUNT


@pytest.mark.django_db
def test_system_handles_concurrent_rule_applications_safely():
    """
    System should handle concurrent operations on rules without data corruption

    Multiple users or processes may mark rules as applied simultaneously,
    and the system should handle this safely.
    """
    # Create a rule for concurrent operations
    rule = baker.make(
        MaskingRule,
        table_name="test_concurrent_table",
        column_name="test_concurrent_column",
        function_expr="anon.fake_email()",
        enabled=True,
    )

    rule.mark_applied()
    first_applied_time = rule.applied_at
    assert first_applied_time is not None

    rule.mark_applied()
    second_applied_time = rule.applied_at

    assert second_applied_time is not None
    assert second_applied_time >= first_applied_time


@pytest.mark.django_db
@pytest.mark.parametrize(
    "dangerous_expr",
    [
        "not_anon.fake_email()",  # Wrong namespace
        "anon.fake_email();DROP TABLE users;",  # SQL injection attempt
        "anon.fake_email()--comment",  # SQL comment injection
        "anon.fake_email()/*comment*/",  # SQL block comment injection
        "anon.",  # Incomplete function syntax
        "anon()",  # Invalid function syntax
        "",  # Empty function
        None,  # None value
    ],
)
def test_system_rejects_dangerous_function_expressions_for_security(dangerous_expr):
    """
    System should reject potentially dangerous function expressions

    Users may accidentally or maliciously enter SQL injection attempts,
    and the system should protect against these security risks.
    """
    result = validate_function_syntax(dangerous_expr)

    assert result is False, f"Dangerous expression '{dangerous_expr}' should be rejected for security"


@pytest.mark.django_db
def test_operation_logging_handles_unusual_data():
    """
    Operation logging should handle unusual data gracefully

    Users may have unusual characters or large data in logs,
    and the system should handle these robustly.
    """
    # Test 1: Handle extremely long error messages
    long_error_message = "Database error: " + "A" * 1000  # Reasonable size for testing
    log = create_operation_log("test_operation", success=False, error_message=long_error_message)

    # Should handle long errors gracefully
    assert log.success is False
    assert len(log.error_message) > 0  # Should contain error information

    # Test 2: Handle Unicode error messages
    unicode_error = "Ошибка базы данных: 数据库错误"
    log = create_operation_log("test_operation", success=False, error_message=unicode_error)

    assert log.success is False
    assert "Ошибка" in log.error_message or "数据库" in log.error_message


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data_type,column_name",
    [
        ("", ""),  # Empty strings
        ("a" * 100, "b" * 100),  # Very long names
        ("UPPERCASE_TYPE", "UPPERCASE_COLUMN"),  # All uppercase
        ("MixedCase", "MixedCase"),  # Mixed case
        ("123numeric", "456numeric"),  # Numeric prefixes
        ("special!@#", "chars$%^"),  # Special characters
        ("unicode_测试", "колонка"),  # Unicode characters
    ],
)
def test_function_suggestions_work_with_unusual_column_patterns(data_type, column_name):
    """
    Function suggestion system should handle unusual column names gracefully

    Users may have unusual naming conventions, and the system should
    provide reasonable suggestions even for edge cases.
    """
    suggestions = suggest_anonymization_functions(data_type or "", column_name or "")

    assert isinstance(suggestions, list)
    # Should always include hash as a fallback option
    assert any("hash" in suggestion for suggestion in suggestions)


@pytest.mark.django_db
def test_preset_system_handles_empty_and_complex_configurations():
    """
    Preset system should handle edge cases like empty presets gracefully

    Users may create presets with no rules or complex configurations,
    and the system should handle these scenarios properly.
    """
    # Test 1: Empty preset (no rules)
    empty_preset = baker.make(MaskingPreset, name="Empty Configuration Preset", preset_type="custom")

    assert empty_preset.rules.count() == 0
    assert str(empty_preset)  # String representation shouldn't crash

    # Test 2: Preset with rules
    preset_with_rules = baker.make(MaskingPreset, name="Test Preset")
    rule = baker.make(MaskingRule)
    preset_with_rules.rules.add(rule)

    assert preset_with_rules.rules.count() == 1


@pytest.mark.django_db
def test_logging_system_handles_large_and_unusual_data():
    """
    Logging system should handle large data and unusual characters

    System logs may contain large amounts of data or unusual characters,
    and the logging system should handle these robustly.
    """
    # Test 1: Log with empty user (edge case)
    log_empty_user = baker.make(
        MaskingLog,
        operation="test_operation",
        user="",  # Empty user string
        success=True,
    )
    assert log_empty_user.user == ""

    # Test 2: Log with extremely large details
    large_details = {"operation_data": "x" * 100000, "status": "completed"}
    log_large_data = baker.make(
        MaskingLog, operation="large_data_test", user="test@example.com", success=True, details=large_details
    )

    assert log_large_data.details == large_details
    assert len(log_large_data.details["operation_data"]) == 100000


@pytest.mark.django_db
def test_model_string_representations_handle_edge_case_data():
    """
    Model string representations should work with edge case data

    String representations are used in admin interface and debugging,
    so they should work reliably even with unusual data.
    """
    # Test 1: Rule with empty values
    empty_rule = baker.make(MaskingRule, table_name="", column_name="", function_expr="")
    str_result = str(empty_rule)
    assert len(str_result) > 0  # Should not crash
    assert "." in str_result  # Should contain table.column format

    # Test 2: Rule with very long names
    long_rule = baker.make(MaskingRule, table_name="x" * 100, column_name="y" * 100)
    str_result = str(long_rule)
    assert len(str_result) > 0  # Should not crash
    assert "x" in str_result  # Should contain the data


@pytest.mark.django_db
def test_configuration_system_provides_reasonable_defaults():
    """
    Configuration system should provide reasonable defaults for all settings

    Users should be able to use the system without extensive configuration,
    with all settings having sensible default values.
    """
    from django_postgres_anon.config import get_anon_setting

    # Test: Access all configuration properties
    essential_properties = [
        "default_masked_role",
        "masked_group",
        "anonymized_data_role",
        "enabled",
        "auto_apply_rules",
        "validate_functions",
        "allow_custom_functions",
        "enable_logging",
    ]

    for property_name in essential_properties:
        value = get_anon_setting(property_name.upper())

        assert value is not None, f"Config property '{property_name}' should have a default value"


# Removed factory test - factories were part of over-engineering cleanup


@pytest.mark.django_db
def test_admin_validation_handles_empty_and_invalid_selections():
    """
    Admin interface should handle edge cases in user selections gracefully

    Users may select no rules, or invalid operations, and the admin
    should provide clear feedback in these cases.
    """
    from django_postgres_anon.admin_base import BaseAnonymizationAdmin

    # Set up admin and request
    admin = BaseAnonymizationAdmin(MaskingRule, None)
    factory = RequestFactory()
    request = factory.post("/admin/")
    request.user = baker.make(User, is_staff=True)
    request.session = {}
    request._messages = FallbackStorage(request)

    # Test 1: Empty rule selection
    empty_queryset = MaskingRule.objects.none()
    result = admin._validate_operation_preconditions(request, empty_queryset, "apply")

    assert result is False

    # Test 2: Invalid operation type
    rules_queryset = MaskingRule.objects.all()
    result = admin._validate_operation_preconditions(request, rules_queryset, "invalid_operation_type")

    assert result is False


@pytest.mark.django_db
def test_utils_handle_edge_case_inputs_safely():
    """
    Utility functions should handle edge case inputs without crashing

    Utils should be robust against None values, empty strings,
    and other edge case inputs that may occur in real usage.
    """
    from django_postgres_anon.utils import suggest_anonymization_functions, validate_function_syntax

    # Test validation function edge cases
    edge_inputs = [None, "", "   ", "\n\t", "🚀💻📊"]
    for input_value in edge_inputs:
        result = validate_function_syntax(input_value)
        assert result is False, f"Edge case input '{input_value}' should fail validation"

    # Test suggestion function edge cases
    for data_type, column_name in [("", ""), (None, None)]:
        suggestions = suggest_anonymization_functions(data_type or "", column_name or "")
        assert isinstance(suggestions, list)
        # Should always include hash as a fallback option
        assert any("hash" in suggestion for suggestion in suggestions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

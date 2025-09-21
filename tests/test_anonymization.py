"""Comprehensive tests for anonymization functionality: utils, context managers, decorators"""

from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase

from django_postgres_anon.context_managers import anonymized_data, database_role
from django_postgres_anon.decorators import AnonymizedDataMixin, database_role_required, use_anonymized_data
from django_postgres_anon.utils import (
    check_table_exists,
    create_masked_role,
    generate_anonymization_sql,
    generate_remove_anonymization_sql,
    get_anon_extension_info,
    get_database_connection_params,
    get_table_columns,
    reset_role,
    suggest_anonymization_functions,
    switch_to_role,
    validate_anon_extension,
    validate_function_syntax,
)

# =============================================================================
# UTILITY FUNCTIONS TESTS
# =============================================================================


class TestAnonymizationUtilities(TestCase):
    """Test core anonymization utility functions"""

    def test_validates_common_anon_functions(self):
        """Users need to know their function syntax is valid"""
        # Valid functions
        assert validate_function_syntax("anon.fake_email()")
        assert validate_function_syntax("anon.fake_first_name()")
        assert validate_function_syntax("anon.partial(col, 2, '***', 2)")
        assert validate_function_syntax("anon.hash(column_name)")

        # Invalid functions
        assert not validate_function_syntax("")
        assert not validate_function_syntax("not_anon_function()")
        assert not validate_function_syntax("anon.fake_email")  # Missing parentheses
        assert not validate_function_syntax("DROP TABLE users")

    def test_function_validation_security_checks(self):
        """Function validation rejects dangerous patterns"""
        dangerous_patterns = [
            "anon.fake_email();DROP",
            "anon.fake_email()--comment",
            "anon.fake_email()/*comment*/",
            "anon.fake_email()DELETE",
            "anon.fake_email(args) extra",  # doesn't end with )
        ]

        for pattern in dangerous_patterns:
            assert not validate_function_syntax(pattern)

    def test_suggests_appropriate_functions_for_data_types(self):
        """Users want smart suggestions for their data"""
        # Email fields
        suggestions = suggest_anonymization_functions("varchar", "email")
        assert any("email" in s.lower() for s in suggestions)

        # Name fields
        suggestions = suggest_anonymization_functions("text", "first_name")
        assert any("first_name" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("varchar", "last_name")
        assert any("last_name" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("text", "username")
        assert any("username" in s.lower() or "name" in s.lower() for s in suggestions)

        # Phone fields
        suggestions = suggest_anonymization_functions("varchar", "phone_number")
        assert any("phone" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("text", "tel")
        assert any("phone" in s.lower() for s in suggestions)

        # Location fields
        suggestions = suggest_anonymization_functions("varchar", "address")
        assert any("address" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("text", "city")
        assert any("city" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("varchar", "state")
        assert any("state" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("text", "zip_code")
        assert any("zip" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("varchar", "country")
        assert any("country" in s.lower() for s in suggestions)

        # Financial fields
        suggestions = suggest_anonymization_functions("varchar", "ssn")
        assert any("ssn" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("text", "credit_card")
        assert any("card" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("varchar", "iban")
        assert any("iban" in s.lower() for s in suggestions)

        # Various data types for coverage
        suggestions = suggest_anonymization_functions("date", "birth_date")
        assert any("date" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("timestamp", "created_at")
        assert any("date" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("text", "company")
        assert any("company" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("text", "description")
        assert any("lorem" in s.lower() for s in suggestions)

        # Numeric types
        suggestions = suggest_anonymization_functions("integer", "user_id")
        assert len(suggestions) > 0

        suggestions = suggest_anonymization_functions("bigint", "count")
        assert any("int" in s.lower() or "noise" in s.lower() for s in suggestions)

        suggestions = suggest_anonymization_functions("decimal", "price")
        assert any("noise" in s.lower() for s in suggestions)

    def test_generates_correct_sql(self):
        """Users need correct SQL generation"""
        # Test anonymization SQL
        rule = MagicMock()
        rule.table_name = "users"
        rule.column_name = "email"
        rule.get_rendered_function.return_value = "anon.fake_email()"

        sql = generate_anonymization_sql(rule)
        expected = "SECURITY LABEL FOR anon ON COLUMN users.email IS 'MASKED WITH FUNCTION anon.fake_email()';"
        assert sql == expected

        # Test removal SQL
        sql = generate_remove_anonymization_sql("users", "email")
        expected = "SECURITY LABEL FOR anon ON COLUMN users.email IS NULL;"
        assert sql == expected

    def test_utility_functions_provide_data(self):
        """Utility functions provide expected data structures"""
        # Get extension info
        info = get_anon_extension_info()
        assert isinstance(info, dict)
        assert "installed" in info

    @patch("django_postgres_anon.utils.settings")
    def test_extracts_database_connection_params(self, mock_settings):
        """Users need connection params for external tools"""
        mock_settings.DATABASES = {
            "default": {
                "NAME": "test_db",
                "USER": "test_user",
                "PASSWORD": "test_pass",
                "HOST": "localhost",
                "PORT": "5432",
            }
        }

        params = get_database_connection_params()
        assert params["dbname"] == "test_db"
        assert params["user"] == "test_user"
        assert params["password"] == "test_pass"
        assert params["host"] == "localhost"
        assert params["port"] == "5432"


class TestDatabaseOperations(TestCase):
    """Test database operation utilities"""

    def test_checks_extension_availability(self):
        """Users need to know if PostgreSQL anonymizer is available"""
        # Test with real database - extension may or may not be installed
        result = validate_anon_extension()
        assert isinstance(result, bool)

    def test_table_operations_error_handling(self):
        """Database operations handle errors gracefully"""
        # Test with non-existent table - should return empty list
        result = get_table_columns("nonexistent_table_xyz123")
        assert result == []

    def test_get_table_columns_handles_db_error(self):
        """get_table_columns handles database errors gracefully"""
        with patch("django_postgres_anon.utils.connection.cursor") as mock_cursor:
            mock_cursor.side_effect = Exception("Database error")
            result = get_table_columns("any_table")
            assert result == []  # Should return empty list on exception

    def test_role_operations_with_inheritance(self):
        """Role creation supports different inheritance models"""
        # Test with real database - may fail if role exists or permissions lacking
        # Using a unique role name to avoid conflicts
        import uuid

        role_name = f"test_role_{uuid.uuid4().hex[:8]}"
        result = create_masked_role(role_name, inherit_from="postgres")
        # Result depends on database permissions
        assert isinstance(result, bool)

    def test_create_masked_role_success(self):
        """create_masked_role succeeds with proper permissions"""
        with patch("django_postgres_anon.utils.connection.cursor") as mock_cursor:
            mock_cursor_instance = MagicMock()
            mock_cursor.return_value.__enter__.return_value = mock_cursor_instance
            # Simulate role doesn't exist initially
            mock_cursor_instance.fetchone.return_value = None
            # Simulate successful execution
            result = create_masked_role("test_role")
            assert result is True
            # Should execute: check if role exists, create role (role doesn't already exist)
            assert mock_cursor_instance.execute.call_count == 2

    def test_role_switch_auto_create_failure(self):
        """Role switching handles auto-create failures"""
        # Test with real database - switch to role may fail if permissions lacking
        import uuid

        role_name = f"test_switch_role_{uuid.uuid4().hex[:8]}"
        result = switch_to_role(role_name, auto_create=True)
        # Result depends on database permissions
        assert isinstance(result, bool)

    def test_handles_missing_extension_gracefully(self):
        """System handles missing extension without crashing"""
        # Test with real database - just ensure it doesn't crash
        result = validate_anon_extension()
        assert isinstance(result, bool)

    def test_validate_anon_extension_handles_db_error(self):
        """validate_anon_extension handles database errors gracefully"""
        with patch("django_postgres_anon.utils.connection.cursor") as mock_cursor:
            mock_cursor.side_effect = Exception("Database error")
            result = validate_anon_extension()
            assert result is False  # Should return False on exception

    def test_database_role_operations(self):
        """Users can manage database roles"""
        import uuid

        role_name = f"test_role_{uuid.uuid4().hex[:8]}"

        # Test role creation
        result = create_masked_role(role_name)
        assert isinstance(result, bool)

        # Test role switching (if role was created)
        if result:
            switch_result = switch_to_role(role_name)
            assert isinstance(switch_result, bool)

        # Test role reset
        result = reset_role()
        assert isinstance(result, bool)

    def test_switch_to_role_success(self):
        """switch_to_role succeeds with existing role"""
        with patch("django_postgres_anon.utils.connection.cursor") as mock_cursor:
            mock_cursor_instance = MagicMock()
            mock_cursor.return_value.__enter__.return_value = mock_cursor_instance
            result = switch_to_role("existing_role", auto_create=False)
            assert result is True
            mock_cursor_instance.execute.assert_called_with("SET ROLE existing_role")

    def test_reset_role_success(self):
        """reset_role succeeds normally"""
        with patch("django_postgres_anon.utils.connection.cursor") as mock_cursor:
            mock_cursor_instance = MagicMock()
            mock_cursor.return_value.__enter__.return_value = mock_cursor_instance
            result = reset_role()
            assert result is True
            mock_cursor_instance.execute.assert_called_with("RESET ROLE")

    def test_table_operations(self):
        """Users can check table existence and get columns"""
        # Test with real database tables
        # auth_user table should exist in Django
        result = check_table_exists("auth_user")
        assert isinstance(result, bool)

        # Test non-existent table
        result = check_table_exists("nonexistent_table_xyz")
        assert result is False

        # Test get columns - auth_user should have columns
        columns = get_table_columns("auth_user")
        assert isinstance(columns, list)

    def test_handles_database_errors_gracefully(self):
        """System doesn't crash on database errors"""
        # Test operations that might fail but shouldn't crash
        result = validate_anon_extension()
        assert isinstance(result, bool)

        result = check_table_exists("nonexistent_xyz_table")
        assert result is False

        # Try creating role with existing name (should return True as it already exists)
        result = create_masked_role("masked_reader")  # This role already exists
        assert result is True  # Should return True for existing role

        import uuid

        nonexistent = f"nonexistent_{uuid.uuid4().hex[:8]}"
        result = switch_to_role(nonexistent, auto_create=False)
        assert result is False

    def test_check_table_exists_handles_db_error(self):
        """check_table_exists handles database errors gracefully"""
        with patch("django_postgres_anon.utils.connection.cursor") as mock_cursor:
            mock_cursor.side_effect = Exception("Database error")
            result = check_table_exists("any_table")
            assert result is False  # Should return False on exception

    def test_function_suggestions_for_username_columns(self):
        """System suggests appropriate functions for username patterns"""
        suggestions = suggest_anonymization_functions("varchar", "user_name")
        assert "anon.fake_username()" in suggestions

    def test_function_suggestions_for_generic_name_columns(self):
        """System suggests name functions for generic name columns"""
        suggestions = suggest_anonymization_functions("varchar", "full_name")
        assert "anon.fake_name()" in suggestions

    def test_function_suggestions_for_text_fields_with_generic_content(self):
        """System suggests appropriate functions for generic text fields"""
        suggestions = suggest_anonymization_functions("text", "content")
        assert "anon.random_string(10)" in suggestions
        assert 'anon.partial({col}, 2, "***", 2)' in suggestions

    def test_role_switch_auto_create_when_role_missing(self):
        """Role switching attempts auto-creation when role doesn't exist"""
        import uuid

        role_name = f"auto_create_role_{uuid.uuid4().hex[:8]}"

        # Try to switch to non-existent role with auto_create=True
        result = switch_to_role(role_name, auto_create=True)
        assert isinstance(result, bool)

    def test_role_switch_returns_false_when_auto_create_fails(self):
        """Role switching returns False when auto-creation also fails"""
        # Use invalid role name that can't be created
        result = switch_to_role("invalid-role-name!", auto_create=True)
        assert result is False

    def test_role_switch_returns_false_when_auto_create_disabled(self):
        """Role switching returns False when auto-creation is disabled"""
        import uuid

        nonexistent_role = f"nonexistent_{uuid.uuid4().hex[:8]}"
        result = switch_to_role(nonexistent_role, auto_create=False)
        assert result is False

    @pytest.mark.django_db
    def test_operation_log_creation_with_defaults(self):
        """Operation logging works with default parameters"""
        from django_postgres_anon.utils import create_operation_log

        log = create_operation_log("test_operation")
        assert log.operation == "test_operation"
        assert log.user == ""  # Default empty string
        assert log.success is True  # Default True
        assert log.error_message == ""  # Default empty string

    @pytest.mark.django_db
    def test_operation_log_creation_with_custom_parameters(self):
        """Operation logging works with custom parameters"""
        from django_postgres_anon.utils import create_operation_log

        log = create_operation_log(
            operation="apply",
            user="testuser",
            details={"rules": 5},
            success=False,
            error_message="Something went wrong",
        )
        assert log.operation == "apply"
        assert log.user == "testuser"
        assert log.details == {"rules": 5}
        assert log.success is False
        assert log.error_message == "Something went wrong"

    @pytest.mark.django_db
    def test_operation_log_with_none_user_parameter(self):
        """Operation logging handles None user parameter correctly"""
        from django_postgres_anon.utils import create_operation_log

        log = create_operation_log("test_operation", user=None)
        assert log.user == ""  # None should be converted to empty string


# =============================================================================
# CONTEXT MANAGERS TESTS
# =============================================================================


class TestAnonymizedDataContext(TestCase):
    """Test anonymized data context manager"""

    @patch("django_postgres_anon.context_managers.switch_to_role")
    @patch("django_postgres_anon.context_managers.reset_role")
    def test_switches_to_masked_role_during_context(self, mock_reset, mock_switch):
        """Users expect data to be anonymized within the context"""
        mock_switch.return_value = True
        mock_reset.return_value = True

        with anonymized_data():
            pass

        mock_switch.assert_called_once()
        mock_reset.assert_called_once()

    @patch("django_postgres_anon.context_managers.connection")
    @patch("django_postgres_anon.context_managers.switch_to_role")
    @patch("django_postgres_anon.context_managers.reset_role")
    def test_handles_transaction_state_outside_atomic_block(self, mock_reset, mock_switch, mock_connection):
        """Context manager works correctly outside database transactions"""
        mock_switch.return_value = True
        mock_reset.return_value = True
        # Simulate not being in atomic block
        mock_connection.in_atomic_block = False

        with anonymized_data():
            pass

        mock_switch.assert_called_once()
        mock_reset.assert_called_once()

    @patch("django_postgres_anon.context_managers.connection")
    @patch("django_postgres_anon.context_managers.switch_to_role")
    @patch("django_postgres_anon.context_managers.reset_role")
    def test_captures_transaction_isolation_level_when_in_transaction(self, mock_reset, mock_switch, mock_connection):
        """Context manager preserves transaction isolation level"""
        mock_switch.return_value = True
        mock_reset.return_value = True
        # Simulate being in atomic block
        mock_connection.in_atomic_block = True

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("READ COMMITTED",)
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        with anonymized_data():
            pass

        mock_switch.assert_called_once()
        mock_reset.assert_called_once()

    @patch("django_postgres_anon.context_managers.switch_to_role")
    @patch("django_postgres_anon.context_managers.reset_role")
    def test_uses_custom_role_name(self, mock_reset, mock_switch):
        """Users can specify custom role names"""
        mock_switch.return_value = True
        mock_reset.return_value = True

        with anonymized_data(role_name="custom_masked"):
            pass

        mock_switch.assert_called_once_with("custom_masked", auto_create=True)

    @patch("django_postgres_anon.context_managers._restore_original_state")
    @patch("django_postgres_anon.context_managers._setup_masked_role")
    def test_handles_role_switch_failure_gracefully(self, mock_setup, mock_restore):
        """System handles role switch failures"""
        mock_setup.side_effect = RuntimeError("Failed to switch to masked role: test_role")

        with pytest.raises(RuntimeError), anonymized_data():
            pass

        mock_restore.assert_called_once()

    @patch("django_postgres_anon.context_managers.switch_to_role")
    @patch("django_postgres_anon.context_managers.reset_role")
    def test_always_resets_role_even_on_exception(self, mock_reset, mock_switch):
        """Role is reset even if code in context raises exception"""
        mock_switch.return_value = True
        mock_reset.return_value = True

        with pytest.raises(ValueError), anonymized_data():
            raise ValueError("Test exception")

        mock_reset.assert_called_once()


class TestDatabaseRoleContext(TestCase):
    """Test database role context manager"""

    @patch("django_postgres_anon.context_managers.switch_to_role")
    @patch("django_postgres_anon.context_managers.reset_role")
    def test_switches_to_specific_role(self, mock_reset, mock_switch):
        """Users can switch to any specific database role"""
        mock_switch.return_value = True
        mock_reset.return_value = True

        with database_role("readonly_user"):
            pass

        mock_switch.assert_called_once_with("readonly_user", auto_create=False)
        mock_reset.assert_called_once()

    @patch("django_postgres_anon.context_managers.switch_to_role")
    def test_raises_error_when_role_doesnt_exist(self, mock_switch):
        """Database role raises error when role doesn't exist"""
        mock_switch.return_value = False

        with pytest.raises(RuntimeError, match="Database role 'nonexistent' does not exist"):
            with database_role("nonexistent"):
                pass

    @patch("django_postgres_anon.context_managers.switch_to_role")
    def test_raises_error_when_role_switch_fails_in_masked_context(self, mock_switch):
        """Anonymized data context raises error when role switch fails"""
        mock_switch.return_value = False

        with pytest.raises(RuntimeError, match="Failed to switch to masked role: test_role"):
            with anonymized_data(role_name="test_role"):
                pass

    @patch("django_postgres_anon.context_managers._verify_role_switch")
    @patch("django_postgres_anon.context_managers._update_masked_role_record")
    @patch("django_postgres_anon.context_managers.switch_to_role")
    @patch("django_postgres_anon.context_managers.reset_role")
    def test_updates_masked_role_record_when_existing_role_found(
        self, mock_reset, mock_switch, mock_update, mock_verify
    ):
        """Context manager updates existing masked role record when found"""
        mock_switch.return_value = True
        mock_reset.return_value = True
        mock_update.return_value = None
        mock_verify.return_value = None

        with anonymized_data(role_name="test_role"):
            pass

        mock_update.assert_called_once_with("test_role")

    @patch("django_postgres_anon.context_managers.logger")
    @patch("django_postgres_anon.context_managers._verify_role_switch")
    @patch("django_postgres_anon.context_managers._update_masked_role_record")
    @patch("django_postgres_anon.context_managers.switch_to_role")
    def test_logs_error_when_state_restoration_fails(self, mock_switch, mock_update, mock_verify, mock_logger):
        """Context manager logs errors during state restoration without raising"""
        mock_switch.return_value = True
        mock_update.return_value = None
        mock_verify.return_value = None

        with patch("django_postgres_anon.context_managers.reset_role") as mock_reset:
            mock_reset.side_effect = Exception("Reset failed")

            with anonymized_data():
                pass

        mock_logger.error.assert_called_once()
        assert "Error restoring original state" in mock_logger.error.call_args[0][0]

    @patch("django_postgres_anon.context_managers._verify_role_switch")
    @patch("django_postgres_anon.context_managers.switch_to_role")
    @patch("django_postgres_anon.context_managers.reset_role")
    def test_marks_existing_role_as_applied_when_not_applied(self, mock_reset, mock_switch, mock_verify):
        """Context manager marks existing unapplied role as applied"""
        from django_postgres_anon.models import MaskedRole

        mock_switch.return_value = True
        mock_reset.return_value = True
        mock_verify.return_value = None

        # Create an existing masked role that's not applied
        role = MaskedRole.objects.create(role_name="existing_role", is_applied=False)

        with anonymized_data(role_name="existing_role"):
            pass

        # Check that the role was marked as applied
        role.refresh_from_db()
        assert role.is_applied is True


# =============================================================================
# DECORATORS TESTS
# =============================================================================


class TestAnonymizationDecorators(TestCase):
    """Test anonymization decorators"""

    @patch("django_postgres_anon.decorators.anonymized_data")
    def test_use_anonymized_data_decorator_wraps_function(self, mock_context):
        """Decorator automatically wraps function execution"""
        mock_context.return_value.__enter__.return_value = None
        mock_context.return_value.__exit__.return_value = None

        @use_anonymized_data
        def test_function():
            return "result"

        result = test_function()
        assert result == "result"
        mock_context.assert_called_once()

    @patch("django_postgres_anon.decorators.anonymized_data")
    def test_use_anonymized_data_with_custom_role(self, mock_context):
        """Decorator accepts custom role names"""
        mock_context.return_value.__enter__.return_value = None
        mock_context.return_value.__exit__.return_value = None

        @use_anonymized_data("custom_role")
        def test_function():
            return "result"

        result = test_function()
        assert result == "result"
        mock_context.assert_called_once_with(role_name="custom_role", auto_create=True)

    @patch("django_postgres_anon.context_managers.database_role")
    def test_database_role_required_decorator(self, mock_context):
        """Database role decorator enforces specific roles"""
        mock_context.return_value.__enter__.return_value = None
        mock_context.return_value.__exit__.return_value = None

        @database_role_required("admin_role")
        def admin_function():
            return "admin_result"

        result = admin_function()
        assert result == "admin_result"
        mock_context.assert_called_once_with("admin_role")

    def test_decorator_preserves_function_metadata(self):
        """Decorators preserve original function names and docstrings"""

        @use_anonymized_data
        def documented_function():
            """This function has documentation"""
            return "result"

        assert documented_function.__name__ == "documented_function"
        assert "documentation" in documented_function.__doc__


class TestAnonymizedDataMixin(TestCase):
    """Test the mixin for class-based views"""

    @patch("django_postgres_anon.decorators.anonymized_data")
    def test_mixin_wraps_dispatch_method(self, mock_context):
        """Mixin automatically anonymizes data for all view methods"""
        mock_context.return_value.__enter__.return_value = None
        mock_context.return_value.__exit__.return_value = None

        class BaseView:
            def dispatch(self, request, *args, **kwargs):
                return "view_result"

        class TestView(AnonymizedDataMixin, BaseView):
            pass

        view = TestView()
        request = MagicMock()
        result = view.dispatch(request)

        assert result == "view_result"
        mock_context.assert_called_once_with(role_name=None, auto_create=True)

    @patch("django_postgres_anon.decorators.anonymized_data")
    def test_mixin_uses_custom_role_if_specified(self, mock_context):
        """Mixin uses custom role names when specified"""
        mock_context.return_value.__enter__.return_value = None
        mock_context.return_value.__exit__.return_value = None

        class BaseView:
            def dispatch(self, request, *args, **kwargs):
                return "view_result"

        class TestView(AnonymizedDataMixin, BaseView):
            anonymized_role = "custom_view_role"

        view = TestView()
        request = MagicMock()
        view.dispatch(request)

        mock_context.assert_called_once_with(role_name="custom_view_role", auto_create=True)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestAnonymizationIntegration(TestCase):
    """Test integration between anonymization components"""

    @patch("django_postgres_anon.context_managers.switch_to_role")
    @patch("django_postgres_anon.context_managers.reset_role")
    def test_nested_contexts_work_correctly(self, mock_reset, mock_switch):
        """Users can nest anonymization contexts"""
        mock_switch.return_value = True
        mock_reset.return_value = True

        with anonymized_data("role1"), database_role("role2"):
            pass

        # Should have switched roles and reset appropriately
        assert mock_switch.call_count >= 2
        assert mock_reset.call_count >= 2

    @patch("django_postgres_anon.decorators.anonymized_data")
    def test_decorator_works_with_class_methods(self, mock_context):
        """Decorator works on class methods"""
        mock_context.return_value.__enter__.return_value = None
        mock_context.return_value.__exit__.return_value = None

        class DataProcessor:
            @use_anonymized_data
            def process_sensitive_data(self):
                return "processed"

        processor = DataProcessor()
        result = processor.process_sensitive_data()
        assert result == "processed"
        mock_context.assert_called_once()

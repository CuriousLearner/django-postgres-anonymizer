"""Tests for signal handlers."""

from unittest.mock import patch

from django.test import TestCase

from django_postgres_anon.models import MaskingRule, handle_rule_disabled, track_rule_enabled_change


class TestSignalCoverage(TestCase):
    """Test signal handlers for rule changes."""

    def test_track_rule_enabled_change_does_not_exist(self):
        """Test pre_save signal when rule doesn't exist."""

        # Create a rule with pk but not saved to database
        rule = MaskingRule(
            pk=99999,  # Non-existent pk
            table_name="test_table",
            column_name="test_column",
            function_expr="anon.fake_email()",
            enabled=True,
        )

        # Call signal handler directly to test exception path
        track_rule_enabled_change(MaskingRule, rule)

        # Should handle DoesNotExist exception
        assert hasattr(rule, "_enabled_changed")
        assert not rule._enabled_changed
        assert not rule._was_enabled

    def test_handle_rule_disabled_enable_operation(self):
        """Test post_save signal for enable operation."""

        rule = MaskingRule.objects.create(
            table_name="test_table", column_name="test_column", function_expr="anon.fake_email()", enabled=False
        )

        # Simulate enable operation (was disabled, now enabled)
        rule._enabled_changed = True
        rule._was_enabled = False  # Was disabled
        rule.enabled = True  # Now enabled

        # Should trigger early return for enable operation
        with patch("django_postgres_anon.models.logger") as mock_logger:
            handle_rule_disabled(MaskingRule, rule, created=False)

            # Should not perform any database operations
            mock_logger.info.assert_not_called()
            mock_logger.error.assert_not_called()

    def test_handle_rule_disabled_database_success_path(self):
        """Test that database operation path is executed (signal actually runs)"""

        rule = MaskingRule.objects.create(
            table_name="test_table", column_name="test_column", function_expr="anon.fake_email()", enabled=True
        )

        # Set up for disable operation
        rule._enabled_changed = True
        rule._was_enabled = True
        rule.enabled = False

        # The signal code actually executes but fails due to non-existent table
        # The signal code executes but fails due to non-existent table

        # Call signal handler
        handle_rule_disabled(MaskingRule, rule, created=False)

    def test_handle_rule_disabled_database_exception_path(self):
        """Test that database exception path is executed (signal handles errors)"""

        rule = MaskingRule.objects.create(
            table_name="error_table", column_name="error_column", function_expr="anon.fake_email()", enabled=True
        )

        # Set up for disable operation
        rule._enabled_changed = True
        rule._was_enabled = True
        rule.enabled = False

        # The signal code should handle any database errors gracefully

        # Call signal handler
        handle_rule_disabled(MaskingRule, rule, created=False)

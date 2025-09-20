"""Base admin classes with common patterns extracted"""

import logging
from typing import Any, Callable, Dict, List

from django.contrib import admin, messages
from django.db import connection, transaction
from django.db.models import QuerySet
from django.http import HttpRequest

from django_postgres_anon.constants import (
    ADMIN_ERROR_EMOJI,
    ADMIN_WARNING_EMOJI,
    EXTENSION_REQUIRED_OPERATIONS,
    VALID_ADMIN_OPERATIONS,
)

# Simplified error handling
from django_postgres_anon.utils import create_operation_log, generate_anonymization_sql, validate_anon_extension

# Admin-specific constants
logger = logging.getLogger(__name__)
MAX_RULES_TO_VALIDATE = 100
ANON_FUNCTION_PREFIX = "anon."
LARGE_OPERATION_THRESHOLD = 50
MAX_ERRORS_TO_SHOW = 5
MAX_ERROR_SUMMARY_COUNT = 3
MAX_ERRORS_BEFORE_ROLLBACK = 10

# Field name constants for operation results
APPLIED_COUNT_FIELD = "applied_count"
ERRORS_FIELD = "errors"
SUCCESS_FIELD = "success"
ERROR_FIELD = "error"
MASKED_ROLE_MARK_APPLIED_METHOD = "mark_applied"


class BaseAnonymizationAdmin(admin.ModelAdmin):
    """Base admin class with common anonymization patterns"""

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)

    def execute_database_operation(
        self,
        request: HttpRequest,
        operation_name: str,
        rules: QuerySet,
        operation_func: Callable,
        dry_run: bool = False,
    ) -> None:
        """
        Execute database operations on rules with proper error handling.

        This method coordinates validation, execution, and result handling.
        """
        # Error handling simplified

        # Validate preconditions
        if not self._validate_operation_preconditions(request, rules, operation_name):
            return

        # Execute the operation
        results = self._execute_rules_batch(rules, operation_func, operation_name, dry_run)

        # Handle and display results
        self._handle_operation_results(request, operation_name, results, dry_run)

        # Log the operation
        self._log_operation(request, operation_name, rules, results, dry_run)

    def _validate_operation_preconditions(self, request: HttpRequest, rules: QuerySet, operation_name: str) -> bool:
        """
        Validate that operation can proceed with comprehensive input validation.

        Returns:
            bool: True if operation can proceed, False otherwise
        """
        # Validate request and user
        if not self._validate_request_and_user(request):
            return False

        # Validate operation parameters
        if not self._validate_operation_parameters(request, operation_name, rules):
            return False

        # Validate rule integrity
        if not self._validate_rule_integrity(request, rules, operation_name):
            return False

        # Show warning for large operations
        if rules.count() > 10:
            self._show_large_operation_warning(request, rules.count(), operation_name)

        # Check extension availability for database operations
        if operation_name in EXTENSION_REQUIRED_OPERATIONS and not self._validate_extension_available(request):
            return False

        return True

    def _validate_request_and_user(self, request: HttpRequest) -> bool:
        """Validate request object and user permissions."""
        # Validate request object
        if not request or not hasattr(request, "user"):
            messages.error(request, "Error occurred")
            return False

        # Validate user permissions
        if not request.user or not request.user.is_authenticated:
            messages.error(request, "Error occurred")
            return False

        if not request.user.is_staff:
            messages.error(request, "Error occurred")
            return False

        return True

    def _validate_operation_parameters(self, request: HttpRequest, operation_name: str, rules: QuerySet) -> bool:
        """Validate operation name and rules selection."""
        # Validate operation name
        if operation_name not in VALID_ADMIN_OPERATIONS:
            messages.error(request, "Error occurred".format())
            return False

        # Check if rules exist
        if not rules.exists():
            messages.error(request, "Error occurred".format())
            return False

        return True

    def _validate_rule_integrity(self, request: HttpRequest, rules: QuerySet, operation_name: str) -> bool:
        """Validate the integrity of rules before operation."""
        invalid_rules = []

        for rule in rules[:MAX_RULES_TO_VALIDATE]:  # Check limited rules to avoid performance issues
            # Validate required fields
            invalid_rules.extend(self._validate_single_rule_fields(rule))

            # Validate function expression format
            if rule.function_expr and not rule.function_expr.startswith(ANON_FUNCTION_PREFIX):
                invalid_rules.append(f"Rule {rule.id}: function must start with '{ANON_FUNCTION_PREFIX}'")

            # For apply operations, ensure rules are enabled
            if operation_name == "apply" and not rule.enabled:
                invalid_rules.append(f"Rule {rule.id}: disabled rules cannot be applied")

        if invalid_rules:
            self._show_rule_validation_errors(request, invalid_rules)
            return False

        return True

    def _validate_single_rule_fields(self, rule: Any) -> List[str]:
        """Validate required fields for a single rule."""
        errors = []

        if not rule.table_name or not rule.table_name.strip():
            errors.append(f"Rule {rule.id}: missing table name")

        if not rule.column_name or not rule.column_name.strip():
            errors.append(f"Rule {rule.id}: missing column name")

        if not rule.function_expr or not rule.function_expr.strip():
            errors.append(f"Rule {rule.id}: missing function expression")

        return errors

    def _show_rule_validation_errors(self, request: HttpRequest, invalid_rules: List[str]) -> None:
        """Display formatted rule validation errors."""
        error_msg = f"{ADMIN_ERROR_EMOJI} Invalid rules found:\n" + "\n".join(invalid_rules[:MAX_ERRORS_TO_SHOW])
        if len(invalid_rules) > MAX_ERRORS_TO_SHOW:
            error_msg += f"\n... and {len(invalid_rules) - MAX_ERRORS_TO_SHOW} more validation errors"

        messages.error(request, error_msg)

    def _show_large_operation_warning(self, request: HttpRequest, count: int, operation_name: str) -> None:
        """Display warning for operations affecting many rules."""
        warning_message = (
            f"{ADMIN_WARNING_EMOJI} You are about to {operation_name} {count} rules. "
            f"This will modify your database schema."
        )
        messages.warning(request, warning_message)

    def _validate_extension_available(self, request: HttpRequest) -> bool:
        """Check if PostgreSQL Anonymizer extension is available."""
        if not validate_anon_extension():
            messages.error(
                request,
                "❌ PostgreSQL Anonymizer extension is not available. Please run 'python manage.py anon_init' first.",
            )
            return False
        return True

    def _execute_rules_batch(
        self, rules: QuerySet, operation_func: Callable, operation_name: str, dry_run: bool
    ) -> Dict[str, Any]:
        """
        Execute operation on all rules and collect results with transaction management.

        Returns:
            Dict containing applied_count and errors list
        """
        if dry_run:
            return self._execute_dry_run_batch(rules, operation_func, operation_name)
        else:
            return self._execute_transaction_batch(rules, operation_func, operation_name)

    def _execute_dry_run_batch(self, rules: QuerySet, operation_func: Callable, operation_name: str) -> Dict[str, Any]:
        """Execute rules in dry-run mode without transactions."""
        applied_count = 0
        errors = []

        try:
            with connection.cursor() as cursor:
                for rule in rules:
                    result = self._execute_single_rule(rule, cursor, operation_func, operation_name, dry_run=True)
                    if result[SUCCESS_FIELD]:
                        applied_count += 1
                    else:
                        errors.append(result[ERROR_FIELD])
        except Exception as e:
            errors.append(f"Database error: {e}")

        return {APPLIED_COUNT_FIELD: applied_count, ERRORS_FIELD: errors}

    def _execute_transaction_batch(
        self, rules: QuerySet, operation_func: Callable, operation_name: str
    ) -> Dict[str, Any]:
        """Execute rules with atomic transactions."""
        applied_count = 0
        errors = []

        try:
            with transaction.atomic(), connection.cursor() as cursor:
                for rule in rules:
                    result = self._execute_single_rule(rule, cursor, operation_func, operation_name, dry_run=False)
                    if result[SUCCESS_FIELD]:
                        applied_count += 1
                        self._mark_rule_applied_if_applicable(rule, operation_name)
                    else:
                        errors.append(result[ERROR_FIELD])
                        if len(errors) >= MAX_ERRORS_BEFORE_ROLLBACK:
                            break
        except Exception as e:
            errors.append(f"Transaction failed: {e}")

        return {APPLIED_COUNT_FIELD: applied_count, ERRORS_FIELD: errors}

    def _mark_rule_applied_if_applicable(self, rule: Any, operation_name: str) -> None:
        """Mark rule as applied if the operation supports it."""
        if hasattr(rule, MASKED_ROLE_MARK_APPLIED_METHOD) and "apply" in operation_name:
            rule.mark_applied()

    def _execute_single_rule(
        self, rule: Any, cursor: Any, operation_func: Callable, operation_name: str, dry_run: bool
    ) -> Dict[str, Any]:
        """Execute operation on a single rule."""
        try:
            result = operation_func(rule, cursor, dry_run)
            return {SUCCESS_FIELD: result.get(SUCCESS_FIELD, True), ERROR_FIELD: result.get(ERROR_FIELD, "")}
        except Exception as e:
            return {SUCCESS_FIELD: False, ERROR_FIELD: f"Failed to {operation_name} {rule}: {e}"}

    def _handle_operation_results(
        self, request: HttpRequest, operation_name: str, results: Dict[str, Any], dry_run: bool
    ) -> None:
        """Process and display operation results to user."""
        applied_count = results["applied_count"]
        errors = results["errors"]

        # Show success message if any rules were processed
        if applied_count > 0:
            self._show_success_message(request, applied_count, dry_run)

        # Show error summary if there were failures
        if errors:
            self._show_error_summary(request, operation_name, errors)

    def _show_success_message(self, request: HttpRequest, count: int, dry_run: bool) -> None:
        """Display success message for processed rules."""
        action_verb = "would be applied" if dry_run else "applied"
        message = f"Operation successful: {count} rules {action_verb}"
        messages.success(request, message)

    def _show_error_summary(self, request: HttpRequest, operation_name: str, errors: List[str]) -> None:
        """Display formatted error summary."""
        error_summary = f"{ADMIN_ERROR_EMOJI} Failed to {operation_name} {len(errors)} rules:"

        # Show first few errors
        for error in errors[:MAX_ERROR_SUMMARY_COUNT]:
            error_summary += f"\n  • {error}"

        # Add count of remaining errors if any
        if len(errors) > MAX_ERROR_SUMMARY_COUNT:
            error_summary += f"\n  • ... and {len(errors) - MAX_ERROR_SUMMARY_COUNT} more errors"

        messages.error(request, error_summary)

    def _log_operation(
        self, request: HttpRequest, operation_name: str, rules: QuerySet, results: Dict[str, Any], dry_run: bool
    ) -> None:
        """Log the operation for audit trail."""
        username = getattr(request.user, "username", "")

        create_operation_log(
            operation=operation_name,
            user=username,
            details={
                "applied_count": results["applied_count"],
                "errors": results["errors"],
                "source": "admin_interface",
                "rules_selected": list(rules.values_list("id", flat=True)),
                "dry_run": dry_run,
            },
            success=len(results["errors"]) == 0,
            error_message=results["errors"][0] if results["errors"] else "",
        )

    def apply_rule_operation(self, rule, cursor, dry_run=False):
        """Apply anonymization rule to database"""
        if dry_run:
            return {"success": True, "message": f"Would apply rule to {rule}"}

        sql = generate_anonymization_sql(rule)
        cursor.execute(sql)
        return {"success": True, "message": f"Applied rule to {rule}"}

    def enable_rules_operation(self, request, queryset):
        """Enable selected rules (staging only - ready to apply)"""
        count = queryset.filter(enabled=False).update(enabled=True)
        if count > 0:
            message = f"✅ Enabled {count} rule(s) - ready to apply to database"
            self.message_user(request, message)
        else:
            self.message_user(request, "No rules were enabled", level=messages.WARNING)

    def disable_rules_operation(self, request, queryset):
        """Disable selected rules and remove security labels"""
        disabled_count = 0
        failed_count = 0

        for rule in queryset.filter(enabled=True):
            try:
                rule.enabled = False
                rule.save()  # This triggers the signal to remove security label
                disabled_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to disable rule {rule}: {e}")

        if disabled_count > 0:
            message = f"⏸️ Disabled {disabled_count} rule(s) (removed from database if applied)"
            if failed_count > 0:
                message += f" ({failed_count} failed)"
            self.message_user(request, message)
        else:
            self.message_user(request, "No rules were disabled", level=messages.WARNING)


class BaseLogAdmin(admin.ModelAdmin):
    """Base admin for log models - read-only by default"""

    def has_add_permission(self, request):
        return False  # Logs are created automatically

    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be editable

    def has_delete_permission(self, request, obj=None):
        return False  # Logs should be preserved

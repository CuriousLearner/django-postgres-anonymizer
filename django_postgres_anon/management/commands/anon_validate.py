import logging

from django.core.management.base import BaseCommand, CommandError

from django_postgres_anon.config import get_anon_setting
from django_postgres_anon.models import MaskingLog, MaskingRule
from django_postgres_anon.utils import (
    check_table_exists,
    get_table_columns,
    validate_anon_extension,
    validate_function_syntax,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Validate anonymization rules and database setup"

    def add_arguments(self, parser):
        parser.add_argument("--table", type=str, help="Validate rules only for specific table")
        parser.add_argument("--fix", action="store_true", help="Attempt to fix validation issues automatically")
        parser.add_argument("--strict", action="store_true", help="Fail on any validation warnings")

    def handle(self, *args, **options):
        self.stdout.write("🔍 Starting validation...")

        validation_errors = []
        validation_warnings = []
        fixes_applied = []

        try:
            # 1. Check if anon extension is available
            self.stdout.write("Checking PostgreSQL Anonymizer extension...")
            if not validate_anon_extension():
                validation_errors.append("PostgreSQL Anonymizer extension is not installed or initialized")
                self.stdout.write(self.style.ERROR("❌ Extension not found"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Extension available"))

            # 2. Get rules to validate
            rules = MaskingRule.objects.all()
            if options["table"]:
                rules = rules.filter(table_name=options["table"])

            if not rules.exists():
                message = f"No rules found{' for table ' + options['table'] if options['table'] else ''}"
                validation_warnings.append(message)
                self.stdout.write(self.style.WARNING(f"⚠️ {message}"))

            self.stdout.write(f"Validating {rules.count()} rules...")

            # 3. Validate each rule
            for rule in rules:
                rule_errors = self._validate_rule(rule, options, fixes_applied)
                validation_errors.extend(rule_errors)

            # 4. Check for orphaned rules (tables that no longer exist)
            self.stdout.write("Checking for orphaned rules...")
            orphaned_count = self._check_orphaned_rules(rules, options, fixes_applied)
            if orphaned_count > 0:
                validation_warnings.append(f"Found {orphaned_count} rules for non-existent tables")

            # 5. Summary
            self._print_summary(validation_errors, validation_warnings, fixes_applied, options)

            # Log the validation
            MaskingLog.objects.create(
                operation="validate",
                details={
                    "table_filter": options.get("table"),
                    "rules_checked": rules.count(),
                    "errors": len(validation_errors),
                    "warnings": len(validation_warnings),
                    "fixes_applied": len(fixes_applied),
                    "strict_mode": options["strict"],
                },
                success=len(validation_errors) == 0 and (not options["strict"] or len(validation_warnings) == 0),
            )

        except Exception as e:
            MaskingLog.objects.create(operation="validate", success=False, error_message=str(e))
            raise CommandError(f"Validation failed: {e}")

    def _validate_rule(self, rule, options, fixes_applied):
        """Validate a single masking rule"""
        errors = []

        self.stdout.write(f"  Validating {rule}...")

        # Check if table exists
        if not check_table_exists(rule.table_name):
            error = f"Table '{rule.table_name}' does not exist"
            errors.append(error)
            self.stdout.write(f"    ❌ {error}")

            if options["fix"]:
                rule.enabled = False
                rule.save()
                fixes_applied.append(f"Disabled rule for non-existent table {rule.table_name}")
                self.stdout.write("    🔧 Disabled rule for non-existent table")
        else:
            # Check if column exists
            columns = get_table_columns(rule.table_name)
            column_names = [col["column_name"] for col in columns]

            if rule.column_name not in column_names:
                error = f"Column '{rule.column_name}' does not exist in table '{rule.table_name}'"
                errors.append(error)
                self.stdout.write(f"    ❌ {error}")

                if options["fix"]:
                    rule.enabled = False
                    rule.save()
                    fixes_applied.append(f"Disabled rule for non-existent column {rule.table_name}.{rule.column_name}")
                    self.stdout.write("    🔧 Disabled rule for non-existent column")
            else:
                self.stdout.write("    ✅ Table and column exist")

        # Validate function syntax if enabled
        if get_anon_setting("VALIDATE_FUNCTIONS"):
            if not validate_function_syntax(rule.function_expr):
                error = f"Invalid function syntax: '{rule.function_expr}'"
                errors.append(error)
                self.stdout.write(f"    ❌ {error}")
            else:
                self.stdout.write("    ✅ Function syntax valid")
        else:
            self.stdout.write("    ⚠️  Function validation disabled (VALIDATE_FUNCTIONS=False)")

        # Check for potential issues
        try:
            rendered = rule.get_rendered_function()
            self.stdout.write(f"    ✅ Function renders correctly: {rendered}")
        except Exception as e:
            error = f"Function rendering failed: {e}"
            errors.append(error)
            self.stdout.write(f"    ❌ {error}")

        return errors

    def _check_orphaned_rules(self, rules, options, fixes_applied):
        """Check for rules pointing to non-existent tables"""
        orphaned_count = 0

        # Get unique table names from rules
        table_names = set(rules.values_list("table_name", flat=True))

        for table_name in table_names:
            if not check_table_exists(table_name):
                orphaned_rules = rules.filter(table_name=table_name)
                orphaned_count += orphaned_rules.count()

                self.stdout.write(f"  ⚠️ Found {orphaned_rules.count()} orphaned rules for table '{table_name}'")

                if options["fix"]:
                    updated = orphaned_rules.update(enabled=False)
                    fixes_applied.append(f"Disabled {updated} orphaned rules for table {table_name}")
                    self.stdout.write(f"    🔧 Disabled {updated} orphaned rules")

        return orphaned_count

    def _print_summary(self, errors, warnings, fixes_applied, options):
        """Print validation summary"""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("VALIDATION SUMMARY")
        self.stdout.write("=" * 50)

        if not errors and not warnings:
            self.stdout.write(self.style.SUCCESS("🎉 All validations passed!"))
        else:
            if errors:
                self.stdout.write(self.style.ERROR(f"❌ {len(errors)} ERRORS:"))
                for error in errors:
                    self.stdout.write(f"  • {error}")

            if warnings:
                self.stdout.write(self.style.WARNING(f"⚠️ {len(warnings)} WARNINGS:"))
                for warning in warnings:
                    self.stdout.write(f"  • {warning}")

        if fixes_applied:
            self.stdout.write(self.style.SUCCESS(f"\n🔧 {len(fixes_applied)} FIXES APPLIED:"))
            for fix in fixes_applied:
                self.stdout.write(f"  • {fix}")

        # Exit with error code if there are errors or strict warnings
        if errors or (options["strict"] and warnings):
            if errors:
                raise CommandError("Validation failed with errors")
            else:
                raise CommandError("Validation failed in strict mode due to warnings")

import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from django_postgres_anon.models import MaskedRole, MaskingPreset, MaskingRule
from django_postgres_anon.utils import create_operation_log, generate_remove_anonymization_sql, validate_anon_extension

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Remove anonymization from database (remove masking labels, rules, and optionally extension)"

    def add_arguments(self, parser):
        parser.add_argument("--table", type=str, help="Remove anonymization only for specific table")
        parser.add_argument(
            "--column", type=str, help="Remove anonymization only for specific column (requires --table)"
        )
        parser.add_argument(
            "--remove-extension", action="store_true", help="Also remove the anon extension (DANGEROUS)"
        )
        parser.add_argument(
            "--remove-data", action="store_true", help="Remove masking rules and presets from Django models"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Show what would be removed without actually removing"
        )
        parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")
        parser.add_argument("--confirm", action="store_true", help="Confirm the operation without interactive prompt")

    def handle(self, *args, **options):
        if options["column"] and not options["table"]:
            raise CommandError("--column requires --table to be specified")

        # Check if confirmation is required
        if not options["force"] and not options["dry_run"]:
            # For dangerous operations, require explicit confirmation
            if not options["confirm"]:
                # When no --confirm is provided, require interactive confirmation or error
                if options["remove_extension"] or options["remove_data"] or not options["table"]:
                    raise CommandError("This action requires confirmation. Use --confirm or --force to proceed.")
                else:
                    self._confirm_operation(options)

        self.stdout.write("🗑️ Starting anonymization removal...")

        removed_labels = []
        removed_rules = []
        removed_presets = []
        removed_roles = []
        errors = []

        try:
            # 1. Check if anon extension exists
            if not validate_anon_extension():
                self.stdout.write(self.style.WARNING("⚠️ PostgreSQL Anonymizer extension not found"))
            else:
                # 2. Remove security labels from database
                removed_labels = self._remove_security_labels(options, errors)

            # 3. Remove Django model data if requested
            if options["remove_data"]:
                removed_rules = self._remove_masking_rules(options)
                removed_presets = self._remove_masking_presets(options)
                removed_roles = self._remove_masked_roles(options)

            # 4. Remove extension if requested (DANGEROUS)
            if options["remove_extension"]:
                self._remove_extension(options)

            # 5. Summary
            self._print_summary(removed_labels, removed_rules, removed_presets, removed_roles, errors, options)

            # Log the operation
            create_operation_log(
                operation="drop",
                details={
                    "table_filter": options.get("table"),
                    "column_filter": options.get("column"),
                    "labels_removed": len(removed_labels),
                    "rules_removed": len(removed_rules),
                    "presets_removed": len(removed_presets),
                    "roles_removed": len(removed_roles),
                    "errors": len(errors),
                    "remove_extension": options["remove_extension"],
                    "remove_data": options["remove_data"],
                    "dry_run": options["dry_run"],
                },
                success=len(errors) == 0,
            )

        except Exception as e:
            create_operation_log(operation="drop", success=False, error_message=str(e))
            raise CommandError(f"Failed to remove anonymization: {e}")

    def _confirm_operation(self, options):
        """Confirm dangerous operations"""
        warnings = []

        if options["remove_extension"]:
            warnings.append("⚠️ DANGEROUS: This will remove the PostgreSQL Anonymizer extension entirely!")

        if options["remove_data"]:
            warnings.append("⚠️ This will permanently delete masking rules and presets from Django")

        if not options["table"]:
            warnings.append("⚠️ This will remove ALL anonymization from the database")

        if warnings:
            self.stdout.write(self.style.ERROR("WARNING:"))
            for warning in warnings:
                self.stdout.write(f"  {warning}")

            response = input("\nAre you sure you want to continue? Type 'yes' to confirm: ")
            if response.lower() != "yes":
                raise CommandError("Operation cancelled")

    def _remove_security_labels(self, options, errors):
        """Remove SECURITY LABEL statements from database columns"""
        removed_labels = []

        if not validate_anon_extension():
            return removed_labels

        try:
            with connection.cursor() as cursor:
                # Get all columns with anon labels
                if options["table"] and options["column"]:
                    # Specific column
                    table_column_pairs = [(options["table"], options["column"])]
                elif options["table"]:
                    # All columns in specific table
                    cursor.execute(
                        """
                        SELECT t.tablename, c.column_name
                        FROM pg_catalog.pg_tables t
                        JOIN information_schema.columns c ON c.table_name = t.tablename
                        JOIN pg_catalog.pg_seclabels s ON s.objoid = (
                            SELECT c.oid FROM pg_catalog.pg_class c
                            WHERE c.relname = t.tablename
                        )
                        WHERE t.schemaname = 'public'
                        AND t.tablename = %s
                        AND s.provider = 'anon'
                    """,
                        [options["table"]],
                    )
                    table_column_pairs = cursor.fetchall()
                else:
                    # All columns with anon labels
                    cursor.execute(
                        """
                        SELECT t.tablename, c.column_name
                        FROM pg_catalog.pg_tables t
                        JOIN information_schema.columns c ON c.table_name = t.tablename
                        JOIN pg_catalog.pg_seclabels s ON s.objoid = (
                            SELECT c.oid FROM pg_catalog.pg_class c
                            WHERE c.relname = t.tablename
                        )
                        WHERE t.schemaname = 'public'
                        AND s.provider = 'anon'
                    """
                    )
                    table_column_pairs = cursor.fetchall()

                # Remove labels
                for table_name, column_name in table_column_pairs:
                    try:
                        sql = generate_remove_anonymization_sql(table_name, column_name)

                        if options["dry_run"]:
                            self.stdout.write(f"Would remove: {table_name}.{column_name}")
                        else:
                            cursor.execute(sql)
                            removed_labels.append(f"{table_name}.{column_name}")
                            self.stdout.write(f"✅ Removed label: {table_name}.{column_name}")

                    except Exception as e:
                        error_msg = f"Failed to remove label {table_name}.{column_name}: {e}"
                        errors.append(error_msg)
                        self.stdout.write(self.style.ERROR(f"❌ {error_msg}"))

        except Exception as e:
            error_msg = f"Failed to query security labels: {e}"
            errors.append(error_msg)
            self.stdout.write(self.style.ERROR(f"❌ {error_msg}"))

        return removed_labels

    def _remove_masking_rules(self, options):
        """Remove masking rules from Django models"""
        rules = MaskingRule.objects.all()

        if options["table"] and options["column"]:
            rules = rules.filter(table_name=options["table"], column_name=options["column"])
        elif options["table"]:
            rules = rules.filter(table_name=options["table"])

        if options["dry_run"]:
            self.stdout.write(f"Would remove {rules.count()} masking rules")
            for rule in rules:
                self.stdout.write(f"  - {rule}")
            return []

        removed_rules = list(rules.values_list("table_name", "column_name"))
        count = rules.count()
        rules.delete()

        self.stdout.write(f"🗑️ Removed {count} masking rules from Django")
        return removed_rules

    def _remove_masking_presets(self, options):
        """Remove masking presets that have no rules"""
        # Find presets with no rules - use annotate to avoid distinct() issue with delete()
        from django.db.models import Count

        empty_presets = MaskingPreset.objects.annotate(rules_count=Count("rules")).filter(rules_count=0)

        if options["dry_run"]:
            self.stdout.write(f"Would remove {empty_presets.count()} empty presets")
            for preset in empty_presets:
                self.stdout.write(f"  - {preset.name}")
            return []

        removed_presets = list(empty_presets.values_list("name", flat=True))
        count = empty_presets.count()
        empty_presets.delete()

        if count > 0:
            self.stdout.write(f"🗑️ Removed {count} empty presets from Django")

        return removed_presets

    def _remove_masked_roles(self, options):
        """Remove masked roles from Django models"""
        roles = MaskedRole.objects.all()

        if options["dry_run"]:
            self.stdout.write(f"Would remove {roles.count()} masked roles")
            for role in roles:
                self.stdout.write(f"  - {role.role_name}")
            return []

        removed_roles = list(roles.values_list("role_name", flat=True))
        count = roles.count()
        roles.delete()

        if count > 0:
            self.stdout.write(f"🗑️ Removed {count} masked roles from Django")

        return removed_roles

    def _remove_extension(self, options):
        """Remove the anon extension (DANGEROUS)"""
        if options["dry_run"]:
            self.stdout.write("Would remove PostgreSQL Anonymizer extension")
            return

        try:
            with connection.cursor() as cursor:
                cursor.execute("DROP EXTENSION IF EXISTS anon CASCADE;")
                self.stdout.write(self.style.ERROR("⚠️ Removed PostgreSQL Anonymizer extension"))

        except Exception as e:
            raise CommandError(f"Failed to remove extension: {e}")

    def _print_summary(self, removed_labels, removed_rules, removed_presets, removed_roles, errors, options):
        """Print operation summary"""
        self.stdout.write("\n" + "=" * 50)
        if options["dry_run"]:
            self.stdout.write("DRY RUN SUMMARY")
        else:
            self.stdout.write("REMOVAL SUMMARY")
        self.stdout.write("=" * 50)

        if removed_labels:
            self.stdout.write(f"🏷️ Security labels removed: {len(removed_labels)}")

        if removed_rules:
            self.stdout.write(f"📋 Masking rules removed: {len(removed_rules)}")

        if removed_presets:
            self.stdout.write(f"📦 Presets removed: {len(removed_presets)}")

        if removed_roles:
            self.stdout.write(f"👤 Masked roles removed: {len(removed_roles)}")

        if errors:
            self.stdout.write(self.style.ERROR(f"❌ Errors: {len(errors)}"))
            for error in errors:
                self.stdout.write(f"  • {error}")

        if not any([removed_labels, removed_rules, removed_presets, removed_roles]):
            self.stdout.write(self.style.WARNING("ℹ️ Nothing to remove"))
        elif not options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("\n🧹 Anonymization removal completed!"))

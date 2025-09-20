import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from django_postgres_anon.models import MaskingLog, MaskingRule
from django_postgres_anon.utils import create_operation_log, generate_anonymization_sql, validate_anon_extension

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Apply masking rules to the database"

    def add_arguments(self, parser):
        parser.add_argument("--table", type=str, help="Apply rules only for specific table")
        parser.add_argument(
            "--dry-run", action="store_true", help="Show what would be applied without actually applying"
        )
        parser.add_argument("--force", action="store_true", help="Apply even if validation fails")

    def handle(self, *_args, **options):
        # Validate anon extension first
        try:
            validate_anon_extension()
        except Exception as e:
            raise CommandError(str(e))

        rules = MaskingRule.objects.filter(enabled=True)

        if options["table"]:
            rules = rules.filter(table_name=options["table"])

        if not rules.exists():
            self.stdout.write(self.style.WARNING("No enabled rules found"))
            return

        self.stdout.write(f"Found {rules.count()} rules to apply")

        applied_count = 0
        errors = []

        try:
            with connection.cursor() as cursor:
                for rule in rules:
                    try:
                        sql = generate_anonymization_sql(rule)

                        if options["dry_run"]:
                            self.stdout.write(f"Would apply: {sql}")
                        else:
                            cursor.execute(sql)
                            rule.mark_applied()
                            applied_count += 1
                            self.stdout.write(f"✅ Applied: {rule}")

                    except Exception as e:
                        error_msg = f"Failed to apply {rule}: {e}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        if not options["force"]:
                            continue

            if not options["dry_run"]:
                create_operation_log(
                    operation="apply",
                    details={
                        "applied_count": applied_count,
                        "errors": errors,
                        "table_filter": options.get("table"),
                        "dry_run": False,
                    },
                    success=len(errors) == 0,
                )

                self.stdout.write(self.style.SUCCESS(f"Applied {applied_count} masking rules"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Dry run complete - {rules.count()} rules would be applied"))

            if errors:
                self.stdout.write(self.style.ERROR(f"{len(errors)} errors occurred"))
                for error in errors:
                    self.stdout.write(f"  - {error}")

        except Exception as e:
            MaskingLog.objects.create(operation="apply", success=False, error_message=str(e))
            raise CommandError(f"Failed to apply rules: {e}")

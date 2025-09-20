from django.core.management.base import BaseCommand
from django.db import connection

from django_postgres_anon.models import MaskedRole, MaskingLog, MaskingRule


class Command(BaseCommand):
    help = "Show anonymizer status and configuration"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== PostgreSQL Anonymizer Status ===\n"))

        # Check extension
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_extension WHERE extname='anon';")
                extension_installed = cursor.fetchone() is not None

                if extension_installed:
                    cursor.execute("SELECT anon.version();")
                    version = cursor.fetchone()[0]
                    self.stdout.write(f"Extension: ✅ Installed (v{version})")
                else:
                    self.stdout.write("Extension: ❌ Not installed")
                    return

                # Check privacy settings
                cursor.execute("SHOW anon.privacy_by_default;")
                privacy_default = cursor.fetchone()[0]
                self.stdout.write(f"Privacy by default: {privacy_default}")

                # Count masking labels
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM pg_seclabel
                    WHERE provider = 'anon'
                """
                )
                labels_count = cursor.fetchone()[0]
                self.stdout.write(f"Applied security labels: {labels_count}")

        except Exception as e:
            self.stdout.write(f"Database error: {e}")
            return

        # Show model statistics
        self.stdout.write("\n=== Rules & Configuration ===")
        total_rules = MaskingRule.objects.count()
        enabled_rules = MaskingRule.objects.filter(enabled=True).count()
        self.stdout.write(f"Total rules: {total_rules}")
        self.stdout.write(f"Enabled rules: {enabled_rules}")

        roles_count = MaskedRole.objects.count()
        self.stdout.write(f"Masked roles: {roles_count}")

        # Show recent activity
        self.stdout.write("\n=== Recent Activity ===")
        recent_logs = MaskingLog.objects.order_by("-timestamp")[:5]
        if recent_logs:
            for log in recent_logs:
                status = "✅" if log.success else "❌"
                self.stdout.write(f"{status} {log.get_operation_display()} - {log.timestamp}")
        else:
            self.stdout.write("No recent activity")

        # Show tables with rules
        self.stdout.write("\n=== Tables with Rules ===")
        tables = MaskingRule.objects.filter(enabled=True).values("table_name").distinct()
        for table in tables:
            table_name = table["table_name"]
            rule_count = MaskingRule.objects.filter(table_name=table_name, enabled=True).count()
            self.stdout.write(f"  {table_name}: {rule_count} rules")

            # Show detailed rules in verbose mode
            if options["verbosity"] >= 2:
                rules = MaskingRule.objects.filter(table_name=table_name, enabled=True)
                for rule in rules:
                    self.stdout.write(f"    {rule.table_name}.{rule.column_name}: {rule.function_expr}")

import os
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from django_postgres_anon.models import MaskingLog, MaskingRule
from django_postgres_anon.utils import create_masked_role, validate_anon_extension


class Command(BaseCommand):
    help = "Create anonymized database dump using PostgreSQL Anonymizer extension"

    def add_arguments(self, parser):
        parser.add_argument("output_file", type=str, help="Output file path")
        parser.add_argument("--tables", type=str, nargs="+", help="Specific tables to dump")
        parser.add_argument("--exclude-tables", type=str, nargs="+", help="Tables to exclude from dump")
        parser.add_argument(
            "--format",
            type=str,
            default="plain",
            help="Output format for pg_dump (only 'plain' supported for anonymized dumps)",
        )
        parser.add_argument(
            "--masked-role",
            type=str,
            help="Database role to use for anonymized dump (defaults to ANON_DEFAULT_MASKED_ROLE)",
        )

    def handle(self, *args, **options):
        # Validate that PostgreSQL Anonymizer extension is available
        if not validate_anon_extension():
            raise CommandError(
                "PostgreSQL Anonymizer extension is not available. "
                "Install the extension and run 'python manage.py anon_init' first."
            )

        # Validate format - anonymized dumps only work with plain format
        if options["format"] and options["format"] != "plain":
            raise CommandError(
                "Anonymized dumps only support 'plain' format due to PostgreSQL Anonymizer limitations. "
                "Use --format=plain or omit the --format option."
            )

        db_settings = settings.DATABASES["default"]

        # Get masked role name
        masked_role = options.get("masked_role") or getattr(settings, "ANON_DEFAULT_MASKED_ROLE", "masked_reader")

        # Ensure masked role exists and is properly configured
        if not self._ensure_masked_role(masked_role):
            raise CommandError(f"Failed to create or configure masked role '{masked_role}'")

        # Apply masking rules to ensure anonymization works during dump
        if not self._apply_masking_rules():
            raise CommandError("Failed to apply masking rules required for anonymized dump")

        # Build pg_dump command with anonymization settings
        host = db_settings.get("HOST") or "localhost"
        port = db_settings.get("PORT") or 5432
        dbname = db_settings.get("NAME") or "postgres"

        cmd = [
            "pg_dump",
            f"--host={host}",
            f"--port={port}",
            f"--username={masked_role}",  # Use masked role instead of default user
            f"--dbname={dbname}",
            "--no-password",
            "--verbose",
            "--no-security-labels",  # Required for anonymized dumps
            "--file",
            options["output_file"],
        ]

        # Try to exclude anon extension if pg_dump supports it
        try:
            # Test if --exclude-extension option is available
            test_cmd = ["pg_dump", "--help"]
            result = subprocess.run(test_cmd, capture_output=True, text=True, check=False)
            if "--exclude-extension" in result.stdout:
                cmd.append("--exclude-extension=anon")
        except Exception:
            # If we can't test, just skip the exclude option
            pass

        if options["tables"]:
            for table in options["tables"]:
                cmd.extend(["--table", table])

        if options["exclude_tables"]:
            for table in options["exclude_tables"]:
                cmd.extend(["--exclude-table", table])

        # Set password via environment
        env = os.environ.copy()
        if db_settings.get("PASSWORD"):
            env["PGPASSWORD"] = db_settings["PASSWORD"]

        try:
            self.stdout.write(f"Creating anonymized dump using masked role '{masked_role}'...")
            self.stdout.write(f"Output file: {options['output_file']}")

            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS(f"✅ Anonymized dump created: {options['output_file']}"))
                self.stdout.write("⚠️  This dump contains anonymized data - do not use for production restore!")

                MaskingLog.objects.create(
                    operation="dump",
                    details={
                        "output_file": options["output_file"],
                        "masked_role": masked_role,
                        "tables": options.get("tables"),
                        "excluded_tables": options.get("exclude_tables"),
                        "anonymized": True,
                    },
                    success=True,
                )
            else:
                raise CommandError(f"pg_dump failed: {result.stderr}")

        except Exception as e:
            MaskingLog.objects.create(
                operation="dump",
                success=False,
                error_message=str(e),
                details={
                    "output_file": options["output_file"],
                    "masked_role": masked_role,
                    "anonymized": True,
                },
            )
            raise CommandError(f"Failed to create anonymized dump: {e}")

    def _apply_masking_rules(self):
        """Apply all enabled masking rules to the database for anonymized dumps"""
        try:
            enabled_rules = MaskingRule.objects.filter(enabled=True)

            if not enabled_rules.exists():
                self.stdout.write(
                    self.style.WARNING("⚠️  No enabled masking rules found. Dump will contain original data.")
                )
                return True  # Continue with dump, but warn user

            self.stdout.write(f"Applying {enabled_rules.count()} masking rules for anonymized dump...")

            with connection.cursor() as cursor:
                for rule in enabled_rules:
                    try:
                        # Apply security label for anonymization
                        table_name = connection.ops.quote_name(rule.table_name)
                        column_name = connection.ops.quote_name(rule.column_name)

                        security_label_sql = f"""
                            SECURITY LABEL FOR anon ON COLUMN {table_name}.{column_name}
                            IS 'MASKED WITH FUNCTION {rule.function_expr}'
                        """

                        cursor.execute(security_label_sql)

                        self.stdout.write(f"  ✅ Applied rule: {rule.table_name}.{rule.column_name}")

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Failed to apply rule {rule.table_name}.{rule.column_name}: {e}")
                        )
                        return False

            self.stdout.write(self.style.SUCCESS("✅ All masking rules applied successfully"))
            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to apply masking rules: {e}"))
            return False

    def _ensure_masked_role(self, role_name):
        """Ensure the masked role exists and is properly configured for anonymized dumps"""
        try:
            with connection.cursor() as cursor:
                # Check if role exists
                cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role_name])
                if not cursor.fetchone():
                    self.stdout.write(f"Creating masked role '{role_name}'...")
                    if not create_masked_role(role_name):
                        return False

                # Configure role for anonymized dumps
                self.stdout.write(f"Configuring role '{role_name}' for anonymized dumps...")

                # Set transparent dynamic masking
                cursor.execute(
                    f"ALTER ROLE {connection.ops.quote_name(role_name)} SET anon.transparent_dynamic_masking = True"
                )

                # Apply masked security label
                cursor.execute(f"SECURITY LABEL FOR anon ON ROLE {connection.ops.quote_name(role_name)} IS 'MASKED'")

                # Grant read permissions (pg_read_all_data available in PG 14+, fallback to manual grants)
                try:
                    cursor.execute(f"GRANT pg_read_all_data TO {connection.ops.quote_name(role_name)}")
                except Exception:
                    # Fallback for older PostgreSQL versions
                    cursor.execute(
                        f"GRANT CONNECT ON DATABASE {connection.settings_dict['NAME']} TO {connection.ops.quote_name(role_name)}"
                    )
                    cursor.execute(f"GRANT USAGE ON SCHEMA public TO {connection.ops.quote_name(role_name)}")
                    cursor.execute(
                        f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {connection.ops.quote_name(role_name)}"
                    )

                self.stdout.write(self.style.SUCCESS(f"✅ Masked role '{role_name}' configured successfully"))
                return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to configure masked role: {e}"))
            return False

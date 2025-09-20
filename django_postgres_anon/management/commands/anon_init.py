from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from django_postgres_anon.models import MaskingLog


class Command(BaseCommand):
    help = "Initialize PostgreSQL anonymizer extension"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Force re-initialization even if already setup")

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                # Check if extension exists
                cursor.execute("SELECT 1 FROM pg_extension WHERE extname='anon';")
                exists = cursor.fetchone() is not None

                if exists and not options["force"]:
                    self.stdout.write(self.style.SUCCESS("PostgreSQL Anonymizer extension already initialized"))
                    return

                if not exists:
                    self.stdout.write("Installing anon extension...")
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS anon CASCADE;")

                # Initialize anon
                self.stdout.write("Initializing anonymizer...")
                cursor.execute("SELECT anon.init();")

                # Get version info
                cursor.execute("SELECT anon.version();")
                version = cursor.fetchone()[0]

                # Check configuration
                cursor.execute("SHOW anon.privacy_by_default;")
                privacy_default = cursor.fetchone()[0]

                self.stdout.write(self.style.SUCCESS("✅ Anonymizer initialized successfully!"))
                self.stdout.write(f"   Version: {version}")
                self.stdout.write(f"   Privacy by default: {privacy_default}")

                # Log the operation
                MaskingLog.objects.create(
                    operation="init",
                    details={"version": version, "privacy_by_default": privacy_default, "forced": options["force"]},
                    success=True,
                )

        except Exception as e:
            # Log the error
            MaskingLog.objects.create(operation="init", success=False, error_message=str(e))
            raise CommandError(f"Failed to initialize anonymizer: {e}")

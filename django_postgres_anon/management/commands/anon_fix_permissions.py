"""
Management command to fix permissions for anonymized roles
"""

from django.core.management.base import BaseCommand
from django.db import connection

from django_postgres_anon.models import MaskedRole
from django_postgres_anon.utils import create_masked_role


class Command(BaseCommand):
    help = "Fix permissions for existing anonymized roles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--role",
            type=str,
            help="Specific role name to fix permissions for",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Fix permissions for all known roles",
        )

    def handle(self, *args, **options):
        if options["role"]:
            # Fix specific role
            role_name = options["role"]
            if self.fix_role_permissions(role_name):
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully fixed permissions for role: {role_name}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to fix permissions for role: {role_name}")
                )
        elif options["all"]:
            # Fix all known roles
            roles = MaskedRole.objects.all()
            if not roles:
                self.stdout.write(
                    self.style.WARNING("No roles found in database")
                )
                return

            success_count = 0
            for role in roles:
                if self.fix_role_permissions(role.role_name):
                    success_count += 1
                    self.stdout.write(f"Fixed permissions for: {role.role_name}")
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to fix permissions for: {role.role_name}")
                    )

            self.stdout.write(
                self.style.SUCCESS(f"Fixed permissions for {success_count}/{len(roles)} roles")
            )
        else:
            self.stdout.write(
                self.style.ERROR("Please specify --role <name> or --all")
            )

    def fix_role_permissions(self, role_name):
        """Fix permissions for a specific role"""
        try:
            # Use the create_masked_role function which now includes permission fixing
            return create_masked_role(role_name)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error fixing permissions for {role_name}: {e}")
            )
            return False
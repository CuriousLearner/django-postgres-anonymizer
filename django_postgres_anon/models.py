import os
from typing import Optional

from django.db import models
from django.utils import timezone

import yaml


class MaskingRule(models.Model):
    """Store masking rules for database columns"""

    table_name = models.CharField(max_length=128, help_text="Database table name")
    column_name = models.CharField(max_length=128, help_text="Column to mask")
    function_expr = models.CharField(
        max_length=512,
        help_text='Anonymization function (e.g., "anon.fake_email()" or "anon.partial({col}, 2, \'***\', 2)")',
    )
    enabled = models.BooleanField(default=True)
    notes = models.TextField(blank=True, help_text="Internal notes about this rule")

    # Validation metadata
    depends_on_unique = models.BooleanField(
        default=False, help_text="Column has UNIQUE constraint - may cause conflicts"
    )
    performance_heavy = models.BooleanField(default=False, help_text="Function is computationally expensive")

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    applied_at = models.DateTimeField(null=True, blank=True, help_text="When rule was last applied")

    class Meta:
        unique_together = ("table_name", "column_name")
        ordering = ["table_name", "column_name"]

    def __str__(self) -> str:
        return f"{self.table_name}.{self.column_name}"

    def clean(self) -> None:
        """Validate the masking rule"""
        # Check for problematic column names that could cause SQL issues
        if not self.column_name or not self.column_name.strip():
            from django.core.exceptions import ValidationError

            raise ValidationError("Column name cannot be empty or whitespace only")

    def get_rendered_function(self) -> str:
        """Get function expression with {col} placeholder replaced"""
        function_expr = self.function_expr.replace("{col}", f'"{self.column_name}"')
        return function_expr

    def mark_applied(self) -> None:
        """Mark rule as applied"""
        self.applied_at = timezone.now()
        self.save(update_fields=["applied_at"])


class MaskedRole(models.Model):
    """Database roles for dynamic masking"""

    role_name = models.CharField(max_length=64, unique=True, default="masked_reader")
    inherits_from = models.CharField(
        max_length=64, default="postgres", help_text="Parent role to inherit permissions from"
    )
    is_applied = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.role_name

    class Meta:
        ordering = ["role_name"]


class MaskingPreset(models.Model):
    """Pre-defined rule sets for common scenarios"""

    PRESET_CHOICES = [
        ("django_auth", "Django Auth User"),
        ("ecommerce", "E-commerce"),
        ("finance", "Financial Data"),
        ("healthcare", "Healthcare/Medical"),
        ("custom", "Custom"),
    ]

    name = models.CharField(max_length=100, unique=True)
    preset_type = models.CharField(max_length=50, choices=PRESET_CHOICES, default="custom")
    description = models.TextField(blank=True)
    rules = models.ManyToManyField(MaskingRule, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["name"]

    @classmethod
    def load_from_yaml(cls, yaml_path: str, preset_name: Optional[str] = None) -> "MaskingPreset":
        """Load rules from YAML file and create preset"""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        if not preset_name:
            preset_name = os.path.splitext(os.path.basename(yaml_path))[0]

        preset, created = cls.objects.get_or_create(
            name=preset_name, defaults={"description": f"Loaded from {yaml_path}"}
        )

        rules_created = 0
        for rule_data in data:
            rule, rule_created = MaskingRule.objects.update_or_create(
                table_name=rule_data["table"],
                column_name=rule_data["column"],
                defaults={
                    "function_expr": rule_data["function"],
                    "enabled": rule_data.get("enabled", True),
                    "notes": rule_data.get("notes", ""),
                    "depends_on_unique": rule_data.get("depends_on_unique", False),
                    "performance_heavy": rule_data.get("performance_heavy", False),
                },
            )
            preset.rules.add(rule)
            if rule_created:
                rules_created += 1

        return preset, rules_created


class MaskingLog(models.Model):
    """Log of anonymization operations"""

    OPERATION_CHOICES = [
        ("init", "Extension Initialization"),
        ("apply", "Rules Applied"),
        ("drop", "Rules Dropped"),
        ("dump", "Anonymous Dump Created"),
        ("static_mask", "Static Masking Applied"),
        ("role_create", "Masked Role Created"),
    ]

    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES)
    details = models.JSONField(default=dict, help_text="JSON details about the operation")
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    user = models.CharField(max_length=150, blank=True)  # Username who performed operation
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        status = "✅" if self.success else "❌"
        return f"{status} {self.get_operation_display()} - {self.timestamp}"


import logging

from django.db import connection

# Signal handlers for automatic security label management
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=MaskingRule)
def track_rule_enabled_change(sender, instance, **kwargs):
    """Track if the enabled field is changing"""
    if instance.pk:
        try:
            old_instance = MaskingRule.objects.get(pk=instance.pk)
            instance._enabled_changed = old_instance.enabled != instance.enabled
            instance._was_enabled = old_instance.enabled
        except MaskingRule.DoesNotExist:
            instance._enabled_changed = False
            instance._was_enabled = False
    else:
        instance._enabled_changed = False
        instance._was_enabled = False


@receiver(post_save, sender=MaskingRule)
def handle_rule_disabled(sender, instance, created, **kwargs):
    """Remove security labels when rule is disabled (if it was applied)"""
    if created or not hasattr(instance, "_enabled_changed") or not instance._enabled_changed:
        return

    # Only handle disable operations (not enable - that should be staging only)
    if not (not instance.enabled and instance._was_enabled):
        return

    # Clear applied_at when rule is disabled since it's no longer applied
    if instance.applied_at:
        MaskingRule.objects.filter(pk=instance.pk).update(applied_at=None)

    # Skip if we're in a test environment with fake table names
    import sys

    from django.conf import settings

    # Check various test indicators
    if (hasattr(settings, "TESTING") and settings.TESTING) or "test" in sys.argv or "pytest" in sys.modules:
        return

    try:
        with connection.cursor() as cursor:
            # Rule was disabled - remove security label if it exists
            from django_postgres_anon.utils import generate_remove_anonymization_sql

            sql = generate_remove_anonymization_sql(instance.table_name, instance.column_name)
            cursor.execute(sql)
            logger.info(f"Removed security label for disabled rule {instance.table_name}.{instance.column_name}")

    except Exception as e:
        logger.error(
            f"Failed to remove security label for disabled rule {instance.table_name}.{instance.column_name}: {e}"
        )
        # Don't raise exception to avoid breaking the save operation
        # In test environments or when tables don't exist, this is expected

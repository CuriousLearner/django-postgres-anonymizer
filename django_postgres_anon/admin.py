from typing import ClassVar, Optional

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils.html import format_html

import yaml

from django_postgres_anon.admin_base import BaseAnonymizationAdmin, BaseLogAdmin

# Removed constants - using inline values
from django_postgres_anon.models import MaskedRole, MaskingLog, MaskingPreset, MaskingRule


@admin.register(MaskingRule)
class MaskingRuleAdmin(BaseAnonymizationAdmin):
    """
    Admin interface for managing anonymization rules.

    Workflow:
    1. Create/Edit rules to define which columns to anonymize
    2. Enable rules to mark them ready for application
    3. Select enabled rules and use "Apply selected rules to database" action
    4. Monitor the 'Database Status' column to see which rules are applied

    Alternative: Use 'python manage.py anon_apply' command for batch operations
    """

    list_display = ("table_name", "column_name", "function_expr", "enabled_status", "applied_status", "created_at")
    list_filter = ("enabled", "depends_on_unique", "performance_heavy", "table_name")
    search_fields = ("table_name", "column_name", "function_expr")
    readonly_fields = ("applied_at", "created_at", "updated_at")

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": ("table_name", "column_name", "function_expr", "enabled"),
                "description": "Define which table.column to anonymize and with what function. "
                "Enable rules to make them ready for application.",
            },
        ),
        (
            "Metadata",
            {
                "fields": ("notes", "depends_on_unique", "performance_heavy"),
                "description": "Additional metadata about the rule for better management.",
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at", "applied_at"),
                "classes": ("collapse",),
                "description": "Tracking when the rule was created, modified, and applied to the database.",
            },
        ),
    )

    def enabled_status(self, obj: MaskingRule) -> str:
        if obj.enabled:
            return format_html('<span style="color: green;">{}</span>', "✅ Enabled")
        return format_html('<span style="color: orange;">{}</span>', "⏸️ Disabled")

    enabled_status.short_description = "Rule Status"

    def applied_status(self, obj: MaskingRule) -> str:
        if obj.applied_at:
            return format_html(
                '<span style="color: blue;">✅ Applied {}</span>', obj.applied_at.strftime("%Y-%m-%d %H:%M")
            )
        elif obj.enabled:
            return format_html('<span style="color: orange;">{}</span>', "⏳ Ready to Apply")
        else:
            return format_html('<span style="color: gray;">{}</span>', "⏸️ Disabled")

    applied_status.short_description = "Database Status"

    actions: ClassVar = [
        "enable_selected_rules",
        "disable_selected_rules",
        "apply_rules_to_database",
        "mark_rules_for_application",
    ]

    def enable_selected_rules(self, request: HttpRequest, queryset: QuerySet) -> None:
        self.enable_rules_operation(request, queryset)

    enable_selected_rules.short_description = "Enable selected rules (mark as ready to apply)"

    def disable_selected_rules(self, request: HttpRequest, queryset: QuerySet) -> None:
        self.disable_rules_operation(request, queryset)

    disable_selected_rules.short_description = "Disable selected rules (removes from database if applied)"

    def apply_rules_to_database(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Apply selected enabled rules to the database"""
        enabled_rules = queryset.filter(enabled=True)
        if not enabled_rules.exists():
            self.message_user(request, "❌ No enabled rules selected. Please enable rules first.", level=messages.ERROR)
            return

        self.execute_database_operation(
            request=request, operation_name="apply", rules=enabled_rules, operation_func=self.apply_rule_operation
        )

    apply_rules_to_database.short_description = (
        "🚀 Apply selected rules to database (⚠️ modifies database - only enabled rules)"
    )

    def mark_rules_for_application(self, request: HttpRequest, queryset: QuerySet) -> None:
        enabled_count = queryset.filter(enabled=True).count()
        total_count = queryset.count()

        if enabled_count == 0:
            self.message_user(
                request,
                "❌ No enabled rules selected. Please enable rules first, then use the 'Apply selected rules to database' action.",
                level=messages.WARNING,
            )
        else:
            self.message_user(
                request,
                f"Info: {enabled_count} of {total_count} selected rules are enabled and ready for application. "
                f"Use the 'Apply selected rules to database' action or run 'python manage.py anon_apply'.",
                level=messages.INFO,
            )

    mark_rules_for_application.short_description = "Check rules ready for database application"

    def changelist_view(self, request: HttpRequest, extra_context: Optional[dict] = None) -> HttpResponse:
        """Add helpful context to the changelist view"""
        extra_context = extra_context or {}

        # Count enabled vs disabled rules
        enabled_count = MaskingRule.objects.filter(enabled=True).count()
        total_count = MaskingRule.objects.count()
        applied_count = MaskingRule.objects.filter(applied_at__isnull=False).count()

        extra_context.update(
            {
                "enabled_rules_count": enabled_count,
                "total_rules_count": total_count,
                "applied_rules_count": applied_count,
                "rules_ready_for_application": enabled_count - applied_count if enabled_count > applied_count else 0,
            }
        )

        return super().changelist_view(request, extra_context=extra_context)


@admin.register(MaskedRole)
class MaskedRoleAdmin(admin.ModelAdmin):
    list_display = ("role_name", "inherits_from", "is_applied", "created_at")
    list_filter = ("is_applied",)
    readonly_fields = ("created_at",)


@admin.register(MaskingPreset)
class MaskingPresetAdmin(admin.ModelAdmin):
    list_display = ("name", "preset_type", "rules_count", "is_active", "created_at")
    list_filter = ("preset_type", "is_active")
    filter_horizontal = ("rules",)
    readonly_fields = ("created_at",)

    def rules_count(self, obj: MaskingPreset) -> int:
        return obj.rules.count()

    rules_count.short_description = "Rules"

    actions: ClassVar = ["export_preset_yaml", "activate_preset"]

    def export_preset_yaml(self, request: HttpRequest, queryset: QuerySet) -> Optional[HttpResponse]:
        if not self._require_single_selection(request, queryset, "export"):
            return None

        preset = queryset.first()
        yaml_content = self._generate_preset_yaml(preset)
        return self._create_yaml_response(yaml_content, preset.name)

    export_preset_yaml.short_description = "Export preset as YAML"

    def activate_preset(self, request: HttpRequest, queryset: QuerySet) -> None:
        if not self._require_single_selection(request, queryset, "activate"):
            return

        preset = self._activate_single_preset(queryset.first())
        self.message_user(request, f"Activated preset: {preset.name}")

    activate_preset.short_description = "Activate preset (deactivates others)"

    def _require_single_selection(self, request: HttpRequest, queryset: QuerySet, action: str) -> bool:
        """Validate that exactly one preset is selected for the given action"""
        if queryset.count() > 1:
            self.message_user(request, f"Please select only one preset to {action}", level=messages.ERROR)
            return False
        return True

    def _generate_preset_yaml(self, preset: MaskingPreset) -> str:
        """Generate YAML content for a preset's rules"""
        rules_data = [self._serialize_rule(rule) for rule in preset.rules.select_related()]
        return yaml.dump(rules_data, default_flow_style=False)

    def _serialize_rule(self, rule: MaskingRule) -> dict:
        """Serialize a masking rule to dictionary format for export"""
        return {
            "table": rule.table_name,
            "column": rule.column_name,
            "function": rule.function_expr,
            "enabled": rule.enabled,
            "notes": rule.notes,
            "depends_on_unique": rule.depends_on_unique,
            "performance_heavy": rule.performance_heavy,
        }

    def _create_yaml_response(self, yaml_content: str, filename: str) -> HttpResponse:
        """Create HTTP response for YAML file download"""
        response = HttpResponse(yaml_content, content_type="application/x-yaml")
        response["Content-Disposition"] = f'attachment; filename="{filename}.yaml"'
        return response

    def _activate_single_preset(self, preset: MaskingPreset) -> MaskingPreset:
        """Activate a single preset and deactivate all others"""
        # Deactivate all presets first
        MaskingPreset.objects.update(is_active=False)

        # Activate selected preset
        preset.is_active = True
        preset.save()
        return preset


@admin.register(MaskingLog)
class MaskingLogAdmin(BaseLogAdmin):
    list_display = ("timestamp", "operation_display", "success_status", "user", "short_details")
    list_filter = ("operation", "success", "timestamp")
    readonly_fields = ("operation", "details", "success", "error_message", "user", "timestamp")
    search_fields = ("user", "error_message")

    def operation_display(self, obj: MaskingLog) -> str:
        """Display operation with appropriate icon for better UX"""
        # Simple icon mapping
        icons = {"init": "🔧", "apply": "✅", "drop": "🗑️", "dump": "📁"}
        icon = icons.get(obj.operation, "❓")
        return f"{icon} {obj.get_operation_display()}"

    operation_display.short_description = "Operation"

    def success_status(self, obj: MaskingLog) -> str:
        """Display success status with colored indicators"""
        if obj.success:
            return format_html('<span style="color: green;">{}</span>', "✅ Success")
        return format_html('<span style="color: red;">{}</span>', "❌ Failed")

    success_status.short_description = "Status"

    def short_details(self, obj: MaskingLog) -> str:
        """Display truncated details for list view readability"""
        if obj.details:
            details_str = str(obj.details)[:100]
            if len(str(obj.details)) > 100:
                details_str += "..."
            return details_str
        return "-"

    short_details.short_description = "Details"


# Custom admin views could be added here for dashboard functionality

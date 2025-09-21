import logging
import os
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand, CommandError

from django_postgres_anon.models import MaskingPreset, MaskingRule
from django_postgres_anon.utils import create_operation_log, validate_function_syntax

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Load anonymization rules from YAML presets"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="Path to YAML file or preset name")
        parser.add_argument("--preset-name", type=str, help="Name for the created preset")
        parser.add_argument("--preset-type", type=str, default="custom", help="Type of preset (default: custom)")
        parser.add_argument("--overwrite", action="store_true", help="Overwrite existing rules")
        parser.add_argument("--disable-existing", action="store_true", help="Disable existing rules for same tables")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be loaded without actually loading")
        parser.add_argument("--validate", action="store_true", help="Validate rules before loading", default=True)

    def handle(self, *args, **options):
        file_path = options["file_path"]

        # Check if it's a preset name or file path
        if not os.path.exists(file_path):
            # Try to find it in the presets directory
            preset_path = self._find_preset_file(file_path)
            if preset_path:
                file_path = preset_path
            else:
                raise CommandError(f"File not found: {file_path}")

        self.stdout.write(f"📥 Loading rules from: {file_path}")

        try:
            # Load and parse YAML
            rules_data = self._load_yaml_file(file_path)

            # Validate structure
            validated_rules = self._validate_yaml_structure(rules_data, options)

            if options["dry_run"]:
                self._print_dry_run_summary(validated_rules, options)
                return

            # Handle existing rules
            if options["disable_existing"]:
                self._disable_existing_rules(validated_rules)

            # Create preset
            preset = self._create_preset(options, file_path)

            # Create rules
            created_rules = self._create_rules(validated_rules, preset, options)

            # Summary
            self._print_summary(created_rules, preset, options)

            # Log the operation
            create_operation_log(
                operation="load_yaml",
                details={
                    "file_path": file_path,
                    "preset_name": preset.name if preset else None,
                    "rules_loaded": len(created_rules),
                    "overwrite": options["overwrite"],
                    "disable_existing": options["disable_existing"],
                },
                success=True,
            )

        except Exception as e:
            create_operation_log(
                operation="load_yaml", success=False, error_message=str(e), details={"file_path": file_path}
            )
            raise CommandError(f"Failed to load YAML: {e}")

    def _find_preset_file(self, preset_name):
        """Find preset file in the config/presets directory"""
        base_dir = Path(__file__).parent.parent.parent
        presets_dir = base_dir / "config" / "presets"

        # Try with .yaml extension
        preset_file = presets_dir / f"{preset_name}.yaml"
        if preset_file.exists():
            return str(preset_file)

        # Try with .yml extension
        preset_file = presets_dir / f"{preset_name}.yml"
        if preset_file.exists():
            return str(preset_file)

        return None

    def _load_yaml_file(self, file_path):
        """Load and parse YAML file"""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                raise CommandError("YAML file is empty")

            return data

        except yaml.YAMLError as e:
            raise CommandError(f"Invalid YAML syntax: {e}")
        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
        except Exception as e:
            raise CommandError(f"Error reading file: {e}")

    def _validate_yaml_structure(self, rules_data, options):
        """Validate YAML structure and rule syntax"""
        # Handle both simple list format and full preset format
        if isinstance(rules_data, dict):
            # Full preset format with metadata
            if "rules" not in rules_data:
                raise CommandError("YAML preset format must contain 'rules' key")

            # Extract rules from preset format
            rules_list = rules_data["rules"]

            # Store preset metadata for later use
            options["_preset_metadata"] = {
                "name": rules_data.get("name"),
                "preset_type": rules_data.get("preset_type", "custom"),
                "description": rules_data.get("description", ""),
            }
        elif isinstance(rules_data, list):
            # Simple list format
            rules_list = rules_data
        else:
            raise CommandError("YAML must contain either a list of rules or a preset dictionary")

        validated_rules = []
        errors = []

        for i, rule_data in enumerate(rules_list):
            try:
                # Handle both simplified format (table, column, function) and model format (table_name, column_name, function_expr)
                table_name = rule_data.get("table_name") or rule_data.get("table")
                column_name = rule_data.get("column_name") or rule_data.get("column")
                function_expr = rule_data.get("function_expr") or rule_data.get("function")

                if not all([table_name, column_name, function_expr]):
                    errors.append(
                        f"Rule {i + 1}: Missing required fields (table/table_name, column/column_name, function/function_expr)"
                    )
                    continue

                # Validate function syntax if enabled
                if options["validate"]:
                    if not validate_function_syntax(function_expr):
                        errors.append(f"Rule {i + 1}: Invalid function syntax: {function_expr}")
                        continue

                # Set defaults
                validated_rule = {
                    "table_name": table_name,
                    "column_name": column_name,
                    "function_expr": function_expr,
                    "enabled": rule_data.get("enabled", True),
                    "notes": rule_data.get("notes", ""),
                    "depends_on_unique": rule_data.get("depends_on_unique", False),
                    "performance_heavy": rule_data.get("performance_heavy", False),
                }

                validated_rules.append(validated_rule)

            except Exception as e:
                errors.append(f"Rule {i + 1}: {e}")

        if errors:
            self.stdout.write(self.style.ERROR("Validation errors:"))
            for error in errors:
                self.stdout.write(f"  ❌ {error}")
            raise CommandError(f"Found {len(errors)} validation errors")

        self.stdout.write(self.style.SUCCESS(f"✅ Validated {len(validated_rules)} rules"))
        return validated_rules

    def _disable_existing_rules(self, rules_data):
        """Disable existing rules for the same tables"""
        table_names = {rule["table_name"] for rule in rules_data}

        if table_names:
            disabled_count = MaskingRule.objects.filter(table_name__in=table_names).update(enabled=False)

            if disabled_count > 0:
                self.stdout.write(f"🔄 Disabled {disabled_count} existing rules for {len(table_names)} tables")

    def _create_preset(self, options, file_path):
        """Create or update preset"""
        # Check if we have preset metadata from YAML
        preset_metadata = options.get("_preset_metadata")

        if preset_metadata and preset_metadata.get("name"):
            # Use name from YAML metadata
            preset_name = preset_metadata["name"]
            preset_type = preset_metadata.get("preset_type", "custom")
            description = preset_metadata.get("description", f"Loaded from {file_path}")
        else:
            # Fallback to command options or generate from file
            preset_name = options.get("preset_name") or Path(file_path).stem
            preset_type = options.get("preset_type", "custom")
            description = f"Loaded from {file_path}"

        preset, created = MaskingPreset.objects.get_or_create(
            name=preset_name,
            defaults={"preset_type": preset_type, "description": description},
        )

        action = "Created" if created else "Using existing"
        self.stdout.write(f"📋 {action} preset: {preset.name}")

        return preset

    def _create_rules(self, rules_data, preset, options):
        """Create masking rules"""
        created_rules = []
        updated_rules = []
        skipped_rules = []

        for rule_data in rules_data:
            # Check if rule already exists
            existing_rule = MaskingRule.objects.filter(
                table_name=rule_data["table_name"], column_name=rule_data["column_name"]
            ).first()

            if existing_rule and not options["overwrite"]:
                skipped_rules.append(existing_rule)
                continue

            if existing_rule and options["overwrite"]:
                # Update existing rule
                for key, value in rule_data.items():
                    setattr(existing_rule, key, value)
                existing_rule.save()

                if preset:
                    preset.rules.add(existing_rule)

                updated_rules.append(existing_rule)
            else:
                # Create new rule
                rule = MaskingRule.objects.create(**rule_data)

                if preset:
                    preset.rules.add(rule)

                created_rules.append(rule)

        # Print progress
        if created_rules:
            self.stdout.write(f"✅ Created {len(created_rules)} new rules")

        if updated_rules:
            self.stdout.write(f"🔄 Updated {len(updated_rules)} existing rules")

        if skipped_rules:
            self.stdout.write(f"⏭️ Skipped {len(skipped_rules)} existing rules (use --overwrite to update)")

        return created_rules + updated_rules

    def _print_dry_run_summary(self, rules_data, options):
        """Print what would be done in dry run mode"""
        self.stdout.write(self.style.SUCCESS("\n🔍 DRY RUN SUMMARY"))
        self.stdout.write(f"Would load {len(rules_data)} rules:")

        for rule in rules_data:
            status = "✅" if rule["enabled"] else "⏸️"
            self.stdout.write(f"  {status} {rule['table_name']}.{rule['column_name']} -> {rule['function_expr']}")

        if options["disable_existing"]:
            table_names = {rule["table_name"] for rule in rules_data}
            existing_count = MaskingRule.objects.filter(table_name__in=table_names).count()
            self.stdout.write(f"\nWould disable {existing_count} existing rules")

    def _print_summary(self, created_rules, preset, options):
        """Print operation summary"""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("LOAD SUMMARY")
        self.stdout.write("=" * 50)

        self.stdout.write(f"📋 Preset: {preset.name} ({preset.preset_type})")
        self.stdout.write(f"📊 Rules loaded: {len(created_rules)}")

        enabled_count = sum(1 for rule in created_rules if rule.enabled)
        disabled_count = len(created_rules) - enabled_count

        self.stdout.write(f"✅ Enabled: {enabled_count}")
        if disabled_count > 0:
            self.stdout.write(f"⏸️ Disabled: {disabled_count}")

        self.stdout.write(self.style.SUCCESS("\n🎉 YAML preset loaded successfully!"))

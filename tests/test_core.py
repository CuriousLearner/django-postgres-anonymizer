"""Comprehensive tests for core functionality: models, config, and exceptions"""

import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from django_postgres_anon.config import anon_config
from django_postgres_anon.models import MaskedRole, MaskingLog, MaskingPreset, MaskingRule

# =============================================================================
# MODELS TESTS
# =============================================================================


class TestMaskingRuleBehavior:
    """Test masking rule model behavior"""

    @pytest.mark.django_db
    def test_masking_rule_creation_with_defaults(self):
        """Users can create masking rules with essential fields"""
        rule = baker.make(MaskingRule)
        assert rule.table_name
        assert rule.column_name
        assert rule.function_expr
        assert rule.created_at
        assert rule.updated_at

    @pytest.mark.django_db
    def test_masking_rule_string_representation(self):
        """Rules display clearly in admin and logs"""
        rule = baker.make(MaskingRule, table_name="users", column_name="email")
        str_repr = str(rule)
        assert "users.email" in str_repr

    @pytest.mark.django_db
    def test_masking_rule_mark_applied_behavior(self):
        """Users can mark rules as applied to track database state"""
        rule = baker.make(MaskingRule, applied_at=None)
        assert rule.applied_at is None

        rule.mark_applied()
        assert rule.applied_at is not None

    @pytest.mark.django_db
    def test_masking_rule_applied_at_cleared_on_disable(self):
        """applied_at field is cleared when rule is disabled"""
        # Create an enabled rule
        rule = baker.make(MaskingRule, enabled=True, applied_at=None)

        # Mark it as applied
        rule.mark_applied()
        rule.refresh_from_db()
        assert rule.applied_at is not None
        assert rule.enabled is True

        # Disable the rule - should clear applied_at
        rule.enabled = False
        rule.save()
        rule.refresh_from_db()

        assert rule.enabled is False
        assert rule.applied_at is None  # Should be cleared when disabled

    @pytest.mark.django_db
    def test_masking_rule_enable_disable_workflow(self):
        """Test full enable -> apply -> disable -> re-enable workflow"""
        rule = baker.make(MaskingRule, enabled=False, applied_at=None)

        # Step 1: Enable (staging)
        rule.enabled = True
        rule.save()
        rule.refresh_from_db()
        assert rule.enabled is True
        assert rule.applied_at is None  # Staging, not applied

        # Step 2: Apply
        rule.mark_applied()
        rule.refresh_from_db()
        assert rule.enabled is True
        assert rule.applied_at is not None  # Now applied

        # Step 3: Disable (should clear applied_at)
        rule.enabled = False
        rule.save()
        rule.refresh_from_db()
        assert rule.enabled is False
        assert rule.applied_at is None  # Cleared when disabled

        # Step 4: Re-enable (staging again)
        rule.enabled = True
        rule.save()
        rule.refresh_from_db()
        assert rule.enabled is True
        assert rule.applied_at is None  # Back to staging

    @pytest.mark.django_db
    def test_masking_rule_get_rendered_function(self):
        """Rules render function expressions with column substitution"""
        rule = baker.make(MaskingRule, column_name="user_id", function_expr="anon.hash({col})")

        rendered = rule.get_rendered_function()
        assert "user_id" in rendered
        assert "{col}" not in rendered

    @pytest.mark.django_db
    def test_masking_rule_validation(self):
        """Rules validate required fields and function syntax"""
        rule = MaskingRule(table_name="users", column_name="email", function_expr="anon.fake_email()")

        # Should not raise validation error for valid data
        try:
            rule.clean()
        except ValidationError:
            pytest.fail("Valid rule should not raise ValidationError")

        # Test behavior with empty fields
        empty_rule = MaskingRule(table_name="", column_name="", function_expr="")
        try:
            empty_rule.clean()
        except ValidationError:
            pass  # Expected for empty fields

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "function_expr",
        [
            "anon.fake_email()",
            "anon.fake_first_name()",
            "anon.fake_last_name()",
            "anon.fake_phone()",
            "anon.fake_company()",
            'anon.partial({col}, 2, "***", 2)',
            "anon.hash({col})",
            "anon.noise({col}, 0.1)",
            "anon.random_string(10)",
            "anon.lorem_ipsum()",
        ],
    )
    def test_anonymization_functions(self, function_expr):
        """Common anonymization functions are supported"""
        rule = baker.make(MaskingRule, function_expr=function_expr)
        assert rule.function_expr == function_expr


class TestMaskingPresetBehavior:
    """Test masking preset model behavior"""

    @pytest.mark.django_db
    def test_preset_creation_and_relationships(self):
        """Users can create presets and associate rules"""
        preset = baker.make(MaskingPreset, name="Test Preset")
        rule = baker.make(MaskingRule)
        preset.rules.add(rule)

        assert preset.name == "Test Preset"
        assert preset.rules.count() == 1
        assert rule in preset.rules.all()

    @pytest.mark.django_db
    def test_preset_yaml_loading(self):
        """Users can load presets from YAML configuration"""
        import os
        import tempfile

        yaml_content = """- table: users
  column: email
  function: anon.fake_email()
  enabled: true
"""

        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            preset, rules_created = MaskingPreset.load_from_yaml(yaml_path, preset_name="YAML Test")

            assert preset.name == "YAML Test"
            assert preset.rules.count() == 1
            assert rules_created == 1

            rule = preset.rules.first()
            assert rule.table_name == "users"
            assert rule.column_name == "email"
        finally:
            os.unlink(yaml_path)

    @pytest.mark.django_db
    def test_preset_yaml_loading_uses_filename_as_default_name(self):
        """When no preset name provided, uses filename as preset name"""
        import os
        import tempfile

        yaml_content = """- table: users
  column: name
  function: anon.fake_name()
  enabled: true
"""

        # Create temporary YAML file with specific name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, prefix="my_preset_") as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Don't provide preset_name - should use filename
            preset, _rules_created = MaskingPreset.load_from_yaml(yaml_path)

            # Should use the filename (without extension) as preset name
            expected_name = os.path.splitext(os.path.basename(yaml_path))[0]
            assert preset.name == expected_name
            assert "my_preset_" in preset.name
        finally:
            os.unlink(yaml_path)

    @pytest.mark.django_db
    def test_preset_string_representation(self):
        """Preset displays name in string representation"""
        preset = baker.make(MaskingPreset, name="Test Preset")
        assert str(preset) == "Test Preset"


class TestMaskingLogBehavior:
    """Test masking log model behavior"""

    @pytest.mark.django_db
    def test_log_creation_and_details(self):
        """System logs operations with details"""
        log = baker.make(
            MaskingLog, operation="apply", user="test@example.com", success=True, details={"rules_applied": 5}
        )

        assert log.operation == "apply"
        assert log.user == "test@example.com"
        assert log.success is True
        assert log.details["rules_applied"] == 5

    @pytest.mark.django_db
    def test_log_string_representation(self):
        """Logs display useful information"""
        log = baker.make(MaskingLog, operation="apply", success=True)
        str_repr = str(log)
        assert "applied" in str_repr.lower()  # The actual string shows "applied"
        assert "✅" in str_repr  # Success emoji should be present


class TestMaskedRoleBehavior:
    """Test masked role model behavior"""

    @pytest.mark.django_db
    def test_masked_role_creation(self):
        """Users can create and track database roles"""
        role = baker.make(MaskedRole, role_name="test_masked", is_applied=True)

        assert role.role_name == "test_masked"
        assert role.is_applied is True

    @pytest.mark.django_db
    def test_masked_role_string_representation(self):
        """Masked roles display clearly in admin and logs"""
        role = baker.make(MaskedRole, role_name="analytics_reader")
        assert str(role) == "analytics_reader"


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================


class TestAnonConfiguration:
    """Test anonymization configuration behavior"""

    def test_config_has_essential_properties(self):
        """Configuration provides all essential settings"""
        essential_properties = [
            "default_masked_role",
            "masked_group",
            "anonymized_data_role",
            "enabled",
            "auto_apply_rules",
            "validate_functions",
            "allow_custom_functions",
            "enable_logging",
        ]

        for prop in essential_properties:
            assert hasattr(anon_config, prop)

    def test_config_provides_sensible_defaults(self):
        """Configuration has reasonable default values"""
        # These should not be None
        non_null_defaults = [
            "default_masked_role",
            "masked_group",
            "anonymized_data_role",
            "enabled",
            "auto_apply_rules",
            "validate_functions",
            "allow_custom_functions",
            "enable_logging",
        ]

        for prop in non_null_defaults:
            value = getattr(anon_config, prop)
            assert value is not None, f"Config {prop} should have a default value"

    def test_config_types_are_correct(self):
        """Configuration values have expected types"""
        assert isinstance(anon_config.default_masked_role, str)
        assert isinstance(anon_config.enabled, bool)
        assert isinstance(anon_config.validate_functions, bool)

    def test_global_config_accessibility(self):
        """Global config instance is accessible"""
        from django_postgres_anon.config import anon_config as global_config

        assert global_config is not None
        assert hasattr(global_config, "default_masked_role")


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestCoreIntegration:
    """Test integration between core components"""

    @pytest.mark.django_db
    def test_rule_preset_integration(self):
        """Rules and presets work together correctly"""
        # Create rules
        email_rule = baker.make(MaskingRule, table_name="users", column_name="email", function_expr="anon.fake_email()")

        name_rule = baker.make(
            MaskingRule, table_name="users", column_name="first_name", function_expr="anon.fake_first_name()"
        )

        # Create preset and associate rules
        preset = baker.make(MaskingPreset, name="User Anonymization")
        preset.rules.add(email_rule, name_rule)

        # Test relationships
        assert preset.rules.count() == 2
        assert email_rule in preset.rules.all()
        assert name_rule in preset.rules.all()

    @pytest.mark.django_db
    def test_config_model_integration(self):
        """Configuration integrates with model behavior"""
        # Create rule with default role from config
        baker.make(MaskingRule)

        # Config should provide the default role name
        default_role = anon_config.default_masked_role
        assert isinstance(default_role, str)
        assert len(default_role) > 0

        # Create a masked role with the default name
        role = baker.make(MaskedRole, role_name=default_role)
        assert role.role_name == default_role

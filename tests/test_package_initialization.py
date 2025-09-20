"""Tests for package initialization, version checking, and preset utilities"""

import sys
from unittest.mock import patch

import pytest

import django_postgres_anon


class TestVersionValidation:
    """Test package version validation during import"""

    def test_raises_error_for_unsupported_python_version(self):
        """Package raises error when Python version is too old"""

        from django.core.exceptions import ImproperlyConfigured

        # Mock the version check logic
        with patch.object(sys, "version_info", (3, 7, 0)), patch(
            "django_postgres_anon.PACKAGE_CONFIG", {"min_python_version": (3, 8), "min_django_version": (4, 2)}
        ), pytest.raises(ImproperlyConfigured, match="django-postgres-anonymizer requires Python 3.8+"):
            django_postgres_anon.check_dependencies()

    @patch("django_postgres_anon.PACKAGE_CONFIG", {"min_python_version": (3, 8), "min_django_version": (4, 2)})
    @patch("django.VERSION", (4, 1, 0, "final", 0))
    def test_raises_error_for_unsupported_django_version(self):
        """Package raises error when Django version is too old"""
        from django.core.exceptions import ImproperlyConfigured

        with pytest.raises(ImproperlyConfigured, match="django-postgres-anonymizer requires Django 4.2+"):
            django_postgres_anon.check_dependencies()


class TestPresetUtilities:
    """Test preset path and discovery utilities"""

    def test_get_preset_path_returns_valid_path_for_existing_preset(self):
        """Preset path utility finds existing preset files"""
        # Test with a preset that should exist
        with patch("os.path.exists", return_value=True):
            path = django_postgres_anon.get_preset_path("django_auth")
            assert "django_auth.yaml" in path

    def test_get_preset_path_raises_error_for_missing_preset(self):
        """Preset path utility raises error for non-existent presets"""
        with patch("os.path.exists", return_value=False):
            with patch("django_postgres_anon.get_available_presets", return_value=["existing1", "existing2"]):
                with pytest.raises(FileNotFoundError, match="Preset 'nonexistent' not found"):
                    django_postgres_anon.get_preset_path("nonexistent")

    def test_get_available_presets_returns_empty_when_directory_missing(self):
        """Available presets returns empty list when presets directory doesn't exist"""
        with patch("os.path.exists", return_value=False):
            presets = django_postgres_anon.get_available_presets()
            assert presets == []

    def test_get_available_presets_finds_yaml_files(self):
        """Available presets discovers YAML files in presets directory"""
        mock_files = ["preset1.yaml", "preset2.yml", "not_preset.txt", "preset3.yaml"]

        with patch("os.path.exists", return_value=True), patch("os.listdir", return_value=mock_files):
            presets = django_postgres_anon.get_available_presets()

        expected = ["preset1", "preset2", "preset3"]
        assert sorted(presets) == sorted(expected)


class TestPackageFunctionality:
    """Test package-level functionality and initialization"""

    def test_check_dependencies_passes_with_compatible_versions(self):
        """Dependency check passes when versions are compatible"""
        # Should not raise any exception with current test environment
        django_postgres_anon.check_dependencies()

    def test_package_exports_essential_functions(self):
        """Package exports all essential functions at top level"""
        essential_functions = [
            "get_version",
            "get_version_info",
            "get_preset_path",
            "get_available_presets",
            "check_dependencies",
        ]

        for func_name in essential_functions:
            assert hasattr(django_postgres_anon, func_name)
            assert callable(getattr(django_postgres_anon, func_name))

    def test_package_version_info_structure(self):
        """Package version info has expected structure"""
        version_info = django_postgres_anon.get_version_info()

        required_keys = ["version", "author", "package_config"]
        for key in required_keys:
            assert key in version_info

        # Check package config structure
        package_config = version_info["package_config"]
        assert "name" in package_config
        assert "description" in package_config

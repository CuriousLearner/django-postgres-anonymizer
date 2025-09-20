"""Comprehensive tests for package metadata, version info, and initialization"""

import pytest

import django_postgres_anon


class TestPackageMetadata:
    """Test package metadata and version information"""

    def test_package_has_version(self):
        """Users can access package version information"""
        assert hasattr(django_postgres_anon, "__version__")
        assert isinstance(django_postgres_anon.__version__, str)
        assert len(django_postgres_anon.__version__) > 0

    def test_package_version_functions(self):
        """Users can get version info programmatically"""
        version = django_postgres_anon.get_version()
        assert isinstance(version, str)
        assert version == django_postgres_anon.__version__

        version_info = django_postgres_anon.get_version_info()
        assert isinstance(version_info, dict)
        assert "version" in version_info

    def test_package_metadata(self):
        """Package provides essential metadata"""
        assert hasattr(django_postgres_anon, "__author__")
        assert hasattr(django_postgres_anon, "__email__")
        assert hasattr(django_postgres_anon, "version_info")
        assert isinstance(django_postgres_anon.version_info, tuple)

    def test_package_config(self):
        """Package configuration is accessible"""
        assert hasattr(django_postgres_anon, "PACKAGE_CONFIG")
        config = django_postgres_anon.PACKAGE_CONFIG
        assert isinstance(config, dict)
        assert "name" in config
        assert "version" in config


class TestVersionUtilities:
    """Test version utility functions"""

    def test_get_version_function(self):
        """get_version() returns current package version"""
        from django_postgres_anon import get_version

        version = get_version()
        assert isinstance(version, str)
        assert "." in version  # Should be in format like '0.1.0'

    def test_get_version_info_function(self):
        """get_version_info() returns comprehensive version details"""
        from django_postgres_anon import get_version_info

        info = get_version_info()
        assert isinstance(info, dict)

        required_keys = ["version", "author"]
        for key in required_keys:
            assert key in info

        # Check package config contains description
        assert "package_config" in info
        assert "description" in info["package_config"]

    def test_version_info_tuple(self):
        """version_info tuple allows easy version comparison"""
        assert hasattr(django_postgres_anon, "version_info")
        version_tuple = django_postgres_anon.version_info
        assert isinstance(version_tuple, tuple)
        assert len(version_tuple) >= 3  # major.minor.patch


class TestPackageInitialization:
    """Test package initialization and imports"""

    def test_package_imports_cleanly(self):
        """Package can be imported without errors"""
        # This test passes if the import at the top works
        assert django_postgres_anon is not None

    def test_essential_attributes_available(self):
        """Essential package attributes are available after import"""
        essential_attrs = ["__version__", "__author__", "__email__", "version_info", "PACKAGE_CONFIG"]

        for attr in essential_attrs:
            assert hasattr(django_postgres_anon, attr), f"Missing attribute: {attr}"

    def test_version_consistency(self):
        """Version is consistent across different access methods"""
        direct_version = django_postgres_anon.__version__
        function_version = django_postgres_anon.get_version()
        config_version = django_postgres_anon.PACKAGE_CONFIG["version"]

        assert direct_version == function_version == config_version


class TestPresetUtilities:
    """Test preset-related utilities"""

    def test_get_available_presets(self):
        """Users can get list of available presets"""
        from django_postgres_anon import get_available_presets

        presets = get_available_presets()
        assert isinstance(presets, list)

    def test_get_preset_path(self):
        """Users can get path to preset files"""
        from django_postgres_anon import get_preset_path

        path = get_preset_path("django_auth")
        assert isinstance(path, str)
        assert "django_auth" in path or path is None  # May not exist in simplified version


class TestDependencyChecks:
    """Test dependency checking functionality"""

    def test_check_dependencies_runs_without_error(self):
        """Dependency check should pass in current environment"""
        from django_postgres_anon import check_dependencies

        # Should not raise an exception in our test environment
        try:
            check_dependencies()
        except Exception:
            pytest.fail("Dependency check should pass in test environment")

    def test_get_available_presets_returns_list(self):
        """get_available_presets returns list of available presets"""
        from django_postgres_anon import get_available_presets

        result = get_available_presets()
        assert isinstance(result, list)

    def test_get_preset_path_behavior(self):
        """get_preset_path returns path for preset files"""
        from django_postgres_anon import get_preset_path

        # Test with an available preset name
        result = get_preset_path("django_auth")
        assert isinstance(result, str)
        assert "django_auth" in result

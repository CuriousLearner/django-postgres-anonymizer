"""Django PostgreSQL Anonymizer - A comprehensive Django app for database anonymization
using PostgreSQL Anonymizer extension.

This package provides:
- Django models for managing anonymization rules and presets
- Management commands for initializing, applying, and managing anonymization
- Middleware for dynamic role switching
- Context managers for temporary role switching (anonymized_data, database_role)
- Decorators for automatic anonymization in views/functions (use_anonymized_data, database_role_required)
- Class-based view mixins for anonymized data access (AnonymizedDataMixin)
- Utilities for database schema introspection
- Pre-built presets for common use cases

For more information, see: https://github.com/CuriousLearner/django-postgres-anonymizer
"""

import os
from typing import Any, Dict

__version__ = "0.1.0-alpha.1"
__author__ = "Sanyam Khurana"
__email__ = "sanyam@sanyamkhurana.com"
__license__ = "BSD-3-Clause"
__url__ = "https://github.com/CuriousLearner/django-postgres-anonymizer"

# Version info tuple for easy comparison (SemVer compatible)
import re

# Parse SemVer format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILDMETADATA]
_version_match = re.match(
    r"(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?",
    __version__,
)
if _version_match:
    major, minor, patch, prerelease, build = _version_match.groups()
    version_info = (int(major), int(minor), int(patch))
    if prerelease:
        version_info += (prerelease,)
    if build:
        version_info += (build,)
else:
    version_info = (0, 1, 0)

# Django 3.2+ no longer uses default_app_config
# Keep for backward compatibility
default_app_config = "django_postgres_anon.apps.DjangoPostgresAnonConfig"

# Package configuration
PACKAGE_CONFIG = {
    "name": "django-postgres-anonymizer",
    "version": __version__,
    "author": __author__,
    "description": "A comprehensive Django app for PostgreSQL database anonymization",
    "min_django_version": (3, 2),
    "min_python_version": (3, 8),
    "required_extensions": ["anon"],
}


def get_version() -> str:
    """Return the package version string."""
    return __version__


def get_version_info() -> Dict[str, Any]:
    """Return detailed version information."""
    return {
        "version": __version__,
        "version_info": version_info,
        "author": __author__,
        "license": __license__,
        "url": __url__,
        "package_config": PACKAGE_CONFIG,
    }


def check_dependencies():
    """Check if required dependencies are available."""
    import sys

    import django
    from django.core.exceptions import ImproperlyConfigured

    # Check Python version
    if sys.version_info < PACKAGE_CONFIG["min_python_version"]:
        min_version = PACKAGE_CONFIG["min_python_version"]
        current_version = sys.version_info
        raise ImproperlyConfigured(
            f"django-postgres-anonymizer requires Python {min_version[0]}.{min_version[1]}+ "
            f"but you are using Python {current_version[0]}.{current_version[1]}.{current_version[2]}"
        )

    # Check Django version
    django_version = tuple(map(int, django.VERSION[:2]))
    if django_version < PACKAGE_CONFIG["min_django_version"]:
        min_django = PACKAGE_CONFIG["min_django_version"]
        current_django = django.VERSION
        raise ImproperlyConfigured(
            f"django-postgres-anonymizer requires Django {min_django[0]}.{min_django[1]}+ "
            f"but you are using Django {current_django[0]}.{current_django[1]}"
        )


def get_preset_path(preset_name: str) -> str:
    """Get the file path for a built-in preset."""
    import os

    package_dir = os.path.dirname(__file__)
    preset_path = os.path.join(package_dir, "config", "presets", f"{preset_name}.yaml")

    if not os.path.exists(preset_path):
        available_presets = get_available_presets()
        raise FileNotFoundError(f"Preset '{preset_name}' not found. Available presets: {', '.join(available_presets)}")

    return preset_path


def get_available_presets() -> list:
    """Get list of available built-in presets."""
    package_dir = os.path.dirname(__file__)
    presets_dir = os.path.join(package_dir, "config", "presets")

    if not os.path.exists(presets_dir):
        return []

    presets = []
    for filename in os.listdir(presets_dir):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            preset_name = os.path.splitext(filename)[0]
            presets.append(preset_name)

    return sorted(presets)


# Expose commonly used classes and functions at package level
__all__ = [
    "__version__",
    "check_dependencies",
    "get_available_presets",
    "get_preset_path",
    "get_version",
    "get_version_info",
    "version_info",
]

# These will be available for import when Django is configured
try:
    import django

    if django.VERSION >= (3, 2):
        # Lazy imports - only import when accessed
        __all__.extend(
            [
                "AnonymizedDataMixin",
                "MaskedRole",
                "MaskingLog",
                "MaskingPreset",
                "MaskingRule",
                "anonymized_data",
                "database_role",
                "database_role_required",
                "get_table_columns",
                "use_anonymized_data",
                "validate_function_syntax",
            ]
        )
except ImportError:  # pragma: no cover
    pass  # pragma: no cover

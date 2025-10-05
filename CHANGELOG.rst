Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

0.1.0b1 - 2025-01-XX
--------------------

⚠️ **Beta Release** - Feature complete, ready for testing. API may still change before 1.0.

**Added**

* Multiple user groups support via ``MASKED_GROUPS`` configuration
* Environment variable configuration following 12-factor principles
* Comprehensive documentation with examples and deployment guides

**Changed**

* Improved documentation structure and clarity
* Contributing and changelog docs use RST include directives for single source of truth

**Fixed**

* ``ALLOW_CUSTOM_FUNCTIONS`` setting now properly controls validation
* ``ENABLE_LOGGING`` setting now properly controls operation logging
* ``VALIDATE_FUNCTIONS`` setting now properly controls function validation in management commands
* API reference now documents only public-facing functions (``get_anon_setting``, ``validate_anon_extension``)

**Removed**

* ``database_role()`` context manager - unsafe arbitrary role switching
* ``@database_role_required()`` decorator - potential security risk
* Direct role manipulation utilities - use ``anonymized_data()`` instead
* ``AUTO_APPLY_RULES`` setting - feature was never implemented, removed to avoid confusion

0.1.0-alpha.1 - 2025-09-20
--------------------------

⚠️ **Alpha Release** - Initial preview release.

**Core Features**

* Django models: ``MaskingRule``, ``MaskingPreset``, ``MaskedRole``, ``MaskingLog``
* Management commands: ``anon_init``, ``anon_apply``, ``anon_status``, ``anon_dump``, ``anon_validate``, ``anon_load_yaml``, ``anon_drop``, ``anon_fix_permissions``
* Middleware (``AnonRoleMiddleware``) for automatic role switching based on user groups
* Context managers (``anonymized_data``) for manual control
* Decorators (``@use_anonymized_data``) for view-level anonymization
* Class-based view mixins (``AnonymizedDataMixin``)
* Django admin integration with bulk actions

**Pre-built Presets**

* Django Auth, E-commerce, Healthcare, Finance, Social Media, Education

**Security**

* SQL injection prevention with function validation
* Role-based access control
* Audit logging
* Parameterized queries

**Requirements**

* Python 3.8+
* Django 3.2+
* PostgreSQL 12+ with Anonymizer extension

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0-alpha.1] - 2025-09-20

⚠️ **Alpha Release** - This is an early preview release for testing and feedback.

### Added

- **Core Features**
  - Django models for managing anonymization rules (`MaskingRule`, `MaskingPreset`, `MaskedRole`, `MaskingLog`)
  - Management commands for PostgreSQL Anonymizer integration
    - `anon_init` - Initialize PostgreSQL Anonymizer extension
    - `anon_apply` - Apply anonymization rules
    - `anon_status` - Show anonymization status
    - `anon_dump` - Create anonymized database dumps
    - `anon_validate` - Validate anonymization rules
    - `anon_load_yaml` - Load rules from YAML presets
    - `anon_drop` - Remove anonymization
  - Middleware for dynamic role switching (`AnonRoleMiddleware`)
  - Django admin integration with bulk actions
  - Comprehensive utility functions for database introspection

- **Pre-built Presets**
  - Django Auth User anonymization
  - E-commerce platform anonymization
  - Healthcare/Medical data anonymization (HIPAA-compliant)
  - Financial services anonymization
  - Social media platform anonymization
  - Education system anonymization

- **Security Features**
  - Function syntax validation to prevent SQL injection
  - Safe SQL execution with security checks
  - Role-based access control for anonymized data
  - Comprehensive audit logging of all operations

- **Development Tools**
  - Comprehensive test suite with >95% coverage
  - Docker configuration for testing and development
  - GitHub Actions CI/CD pipeline
  - Example Django project demonstrating usage
  - Development Makefile with common tasks
  - Type hints throughout the codebase

- **Documentation**
  - Complete README with installation and usage instructions
  - Example project with interactive demo
  - Comprehensive docstrings for all public APIs
  - YAML preset documentation and examples

### Technical Details

- **Supported Python versions**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Supported Django versions**: 3.2, 4.0, 4.1, 4.2, 5.0
- **Database**: PostgreSQL with postgresql-anonymizer extension
- **Dependencies**: Django, psycopg2-binary, PyYAML

### Security

- All anonymization functions are validated to prevent code injection
- SQL execution includes security checks and parameterization
- Role-based access ensures proper data isolation
- Audit logging tracks all anonymization operations

### Performance

- Optimized database queries with proper indexing
- Batch processing support for large datasets
- Efficient schema introspection utilities
- Memory-conscious processing for large tables

[Unreleased]: https://github.com/CuriousLearner/django-postgres-anonymizer/compare/v0.1.0-alpha.1...HEAD
[0.1.0-alpha.1]: https://github.com/CuriousLearner/django-postgres-anonymizer/releases/tag/v0.1.0-alpha.1

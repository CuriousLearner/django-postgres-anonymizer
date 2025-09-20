# Django PostgreSQL Anonymizer

[![Tests](https://github.com/CuriousLearner/django-postgres-anonymizer/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/CuriousLearner/django-postgres-anonymizer/actions/workflows/test.yml)
[![Coverage](https://codecov.io/gh/CuriousLearner/django-postgres-anonymizer/branch/main/graph/badge.svg)](https://codecov.io/gh/CuriousLearner/django-postgres-anonymizer)
[![License](https://img.shields.io/pypi/l/django-postgres-anonymizer)](https://pypi.python.org/pypi/django-postgres-anonymizer/)
[![Downloads](https://static.pepy.tech/badge/django-postgres-anonymizer?period=total&units=international_system&left_color=black&right_color=darkgreen&left_text=Downloads)](https://pepy.tech/project/django-postgres-anonymizer)
[![Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/CuriousLearner/django-postgres-anonymizer/graphs/commit-activity)
[![PyPI version](https://badge.fury.io/py/django-postgres-anonymizer.svg)](https://pypi.python.org/pypi/django-postgres-anonymizer/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Python versions](https://img.shields.io/pypi/pyversions/django-postgres-anonymizer.svg)](https://pypi.org/project/django-postgres-anonymizer/)
[![Django versions](https://img.shields.io/pypi/djversions/django-postgres-anonymizer.svg)](https://pypi.org/project/django-postgres-anonymizer/)
[![GitHub stars](https://img.shields.io/github/stars/CuriousLearner/django-postgres-anonymizer?style=social)](https://github.com/CuriousLearner/django-postgres-anonymizer)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

> [!CAUTION]
> This package is under heavy development and is currently in alpha stage. APIs may change without notice. Not recommended for production use until stable release.

Database anonymization for Django using [PostgreSQL Anonymizer](https://postgresql-anonymizer.readthedocs.io/).

**🔒 Secure • 🚀 Fast • 🎯 Precise • 📊 Production-Ready (coming-soon)**

A comprehensive Django integration for PostgreSQL Anonymizer that provides database anonymization with advanced role management, context-aware data masking, and production-ready security features.

## 📋 Table of Contents

- [🚀 Quick Reference](#-quick-reference)
- [✨ Features](#-features)
- [🎯 Use Cases](#-use-cases)
- [⚡ Quick Start](#-quick-start)
- [📖 Usage Examples](#-usage-examples)
- [🔧 Configuration](#-configuration)
- [📚 API Reference](#-api-reference)
- [🎭 Advanced Features](#-advanced-features)
- [🛠️ Development](#️-development)
- [🧪 Testing](#-testing)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)

## 🎯 Use Cases

- ✅ **GDPR Compliance** - Anonymize personal data for non-production environments
- ✅ **Development & Testing** - Safe realistic data for development teams
- ✅ **Data Analytics** - Enable analytics on anonymized datasets
- ✅ **Third-party Integrations** - Share anonymized data with external services
- ✅ **Regulatory Compliance** - Meet HIPAA, SOX, PCI-DSS requirements
- ✅ **Staging Environments** - Production-like data without privacy risks

## 🚀 Quick Reference

```python
# Context Manager (Recommended)
from django_postgres_anon.context_managers import anonymized_data

def my_view(request):
    with anonymized_data():
        users = User.objects.all()  # ← Automatically anonymized!
        return render(request, 'template.html', {'users': users})

# Decorator
from django_postgres_anon.decorators import use_anonymized_data

@use_anonymized_data
def api_endpoint(request):
    return JsonResponse({'users': list(User.objects.values())})

# Class-Based View Mixin
from django_postgres_anon.decorators import AnonymizedDataMixin

class ReportView(AnonymizedDataMixin, ListView):
    model = SensitiveModel  # ← All queries automatically anonymized!

# Automatic Group-Based (Middleware)
# Users in 'analysts' group see anonymized data everywhere
POSTGRES_ANON = {'MASKED_GROUP': 'analysts'}
```

**Installation**: `pip install django-postgres-anonymizer` → Add to `INSTALLED_APPS` → `python manage.py migrate`

## ✨ Features

### 🎯 **Core Capabilities**

- 🚀 **Zero-Downtime Anonymization** - Apply anonymization rules without service interruption
- 🔄 **Dynamic Role Switching** - Context-aware data access with automatic role management
- 🛡️ **Enterprise Security** - SQL injection prevention, audit logging, permission controls
- 📊 **Smart Function Suggestions** - AI-powered anonymization function recommendations
- 🎭 **Preset Collections** - Pre-built rules for Django Auth, Healthcare, Finance, E-commerce
- ⚡ **Performance Optimized** - Efficient bulk operations and minimal overhead

### 🎭 **Dynamic Data Access**

- 🎯 **Context Managers** - `anonymized_data()` and `database_role()` for temporary role switching
- 🎨 **Decorators** - `@use_anonymized_data` and `@database_role_required` for view-level control
- 🧩 **Class-Based Mixins** - `AnonymizedDataMixin` for automatic anonymization in CBVs
- 🔀 **Smart Middleware** - Group-based automatic role switching for seamless user experience

### 🛠️ **Developer Experience**

- ⚙️ **7 Management Commands** - Complete CLI toolkit for all anonymization operations
- 🖥️ **Rich Admin Interface** - Full Django admin with batch operations and real-time validation
- 🔍 **Schema Introspection** - Automatic table/column discovery and constraint detection
- 📋 **Function Validation** - Real-time SQL syntax checking and security validation
- 📊 **Audit Logging** - Comprehensive operation tracking and compliance reporting

### 🎯 **Rule Management**

- 📚 **YAML Presets** - Industry-standard configurations (Healthcare, Finance, E-commerce)
- 🤖 **AI Suggestions** - Smart function recommendations based on data types and column names
- 🔧 **Bulk Operations** - Efficient mass rule application and management
- ✅ **Constraint Awareness** - Intelligent handling of unique constraints and foreign keys
- 🎨 **Custom Functions** - Support for domain-specific anonymization requirements

## ⚡ Quick Start

### Prerequisites

PostgreSQL with PostgreSQL Anonymizer extension installed.
See: <https://postgresql-anonymizer.readthedocs.io/en/latest/installation/>

### Installation

```bash
pip install django-postgres-anonymizer
```

### Django Configuration

Add to INSTALLED_APPS:

```python
INSTALLED_APPS = [
    # ...
    'django_postgres_anon',
]
```

Add middleware (optional, for dynamic role switching):

```python
MIDDLEWARE = [
    # ...
    'django_postgres_anon.middleware.AnonRoleMiddleware',
]
```

Configure settings:

```python
# Django PostgreSQL Anonymizer Settings
POSTGRES_ANON = {
    'DEFAULT_MASKED_ROLE': 'masked_reader',
    'AUTO_APPLY_RULES': False,
    'VALIDATE_FUNCTIONS': True,
    'ALLOW_CUSTOM_FUNCTIONS': False,
    'ENABLE_LOGGING': True,
}
```

Run migrations:

```bash
python manage.py migrate
```

### Initialize Anonymization

```bash
# Initialize PostgreSQL Anonymizer extension
python manage.py anon_init

# Load a preset (optional) - use preset name, not file path
python manage.py anon_load_yaml django_auth

# Apply anonymization rules
python manage.py anon_apply

# Check status
python manage.py anon_status
```

## 📖 Usage Examples

### Creating Anonymization Rules

#### Via Django Admin

Navigate to `/admin/django_postgres_anon/maskingrule/` and create rules.

#### Via Python Code

```python
from django_postgres_anon.models import MaskingRule

# Create a rule to anonymize email addresses
rule = MaskingRule.objects.create(
    table_name='auth_user',
    column_name='email',
    function_expr='anon.fake_email()',
    notes='Anonymize user email addresses'
)

# Apply the rule
from django.core.management import call_command
call_command('anon_apply')
```

#### Via YAML Presets

```yaml
# my_rules.yaml
- table: auth_user
  column: email
  function: anon.fake_email()
  enabled: true
  notes: "Anonymize user emails"

- table: auth_user
  column: first_name
  function: anon.fake_first_name()
  enabled: true
```

```bash
python manage.py anon_load_yaml my_rules.yaml --preset-name "my_preset"
```

### Available Presets

The package includes several pre-built presets:

- **`django_auth`**: Django's built-in User model
- **`ecommerce`**: E-commerce platforms (orders, payments, customers)
- **`healthcare`**: Healthcare data (HIPAA-compliant)
- **`finance`**: Financial services data
- **`social_media`**: Social media platforms
- **`education`**: Educational institutions

```bash
# Load a preset
python manage.py anon_load_yaml django_auth

# List available presets
make list-presets
```

### Management Commands

```bash
# Initialize extension
python manage.py anon_init [--force]

# Apply anonymization rules
python manage.py anon_apply [--table TABLE] [--dry-run]

# Show current status
python manage.py anon_status [-v 2]

# Create anonymized database dump (requires PostgreSQL Anonymizer extension)
python manage.py anon_dump output.sql [--masked-role ROLE_NAME]
# Note: Only 'plain' format supported for anonymized dumps

# Load rules from YAML preset or file
python manage.py anon_load_yaml django_auth
python manage.py anon_load_yaml my_rules.yaml --preset-name "My Custom Rules"

# Validate existing rules
python manage.py anon_validate

# Remove anonymization
python manage.py anon_drop [--confirm]
```

### Dynamic Role Switching

#### Context Managers

```python
from django_postgres_anon.context_managers import anonymized_data, database_role

# Use anonymized data in a view
def sensitive_report(request):
    with anonymized_data():
        users = User.objects.all()  # Data is automatically anonymized
        return render(request, 'report.html', {'users': users})

# Use a custom masked role
def custom_report(request):
    with anonymized_data('custom_masked_role'):
        data = SensitiveModel.objects.all()
        return JsonResponse({'data': list(data.values())})

# Switch to any database role
def read_only_operation():
    with database_role('readonly_user'):
        # All queries run as readonly_user
        return MyModel.objects.all()
```

#### Decorators

```python
from django_postgres_anon.decorators import use_anonymized_data, database_role_required
from django.utils.decorators import method_decorator

# Function-based views
@use_anonymized_data
def api_endpoint(request):
    return JsonResponse({'users': list(User.objects.values())})

@use_anonymized_data('custom_masked_role')
def custom_api_endpoint(request):
    return JsonResponse({'data': list(SensitiveModel.objects.values())})

# Require specific database role
@database_role_required('readonly_user')
def read_only_operation():
    return MyModel.objects.all()

# Class-based views with method decorator
class SensitiveDataView(View):
    @method_decorator(use_anonymized_data)
    def get(self, request):
        data = SensitiveModel.objects.all()
        return JsonResponse({'data': list(data.values())})
```

#### Class-Based View Mixins

```python
from django_postgres_anon.decorators import AnonymizedDataMixin
from django.views.generic import ListView, View

# Automatic anonymization for ListView
class SensitiveReportView(AnonymizedDataMixin, ListView):
    model = User
    template_name = 'sensitive_report.html'
    anonymized_role = 'custom_masked_role'  # Optional custom role
    auto_create_role = True  # Default: True

# APIView with anonymized data
class SensitiveAPIView(AnonymizedDataMixin, View):
    def get(self, request):
        users = User.objects.all()  # Automatically anonymized
        return JsonResponse({'users': list(users.values())})

# Multiple inheritance works seamlessly
class ProtectedReportView(AnonymizedDataMixin, LoginRequiredMixin, ListView):
    model = SensitiveModel
    template_name = 'protected_report.html'
```

#### Middleware (Group-Based Automatic Switching)

```python
# settings.py
MIDDLEWARE = [
    # ... other middleware
    'django_postgres_anon.middleware.AnonRoleMiddleware',
]

POSTGRES_ANON = {
    'ENABLED': True,
    'MASKED_GROUP': 'analysts',  # Users in this group see anonymized data
    'DEFAULT_MASKED_ROLE': 'masked_reader',
}
```

```python
# Usage: No code changes needed! Users in the 'analysts' group
# will automatically see anonymized data across all views
def any_view(request):
    # If user is in 'analysts' group, data is automatically anonymized
    users = User.objects.all()
    return render(request, 'report.html', {'users': users})
```

### Utility Functions & Developer Tools

#### Smart Function Suggestions

```python
from django_postgres_anon.utils import suggest_anonymization_functions

# Get AI-powered suggestions based on column name and type
suggestions = suggest_anonymization_functions('varchar', 'email_address')
# Returns: ['anon.fake_email()', 'anon.hash({col})', ...]

suggestions = suggest_anonymization_functions('varchar', 'first_name')
# Returns: ['anon.fake_first_name()', 'anon.hash({col})', ...]

suggestions = suggest_anonymization_functions('integer', 'age')
# Returns: ['anon.random_int_between(1, 1000)', 'anon.noise({col}, 0.1)', 'anon.hash({col})']
```

#### Database Introspection

```python
from django_postgres_anon.utils import (
    get_table_columns,
    check_table_exists,
    validate_anon_extension,
    get_anon_extension_info
)

# Check if PostgreSQL Anonymizer extension is installed
if validate_anon_extension():
    print("PostgreSQL Anonymizer is ready!")

# Get detailed extension information
info = get_anon_extension_info()
print(f"Extension installed: {info['installed']}")

# Introspect table structure
columns = get_table_columns('auth_user')
print(f"Columns in auth_user: {columns}")

# Verify table exists
if check_table_exists('my_sensitive_table'):
    print("Table exists and can be anonymized")
```

#### Function Validation & Security

```python
from django_postgres_anon.utils import validate_function_syntax

# Validate anonymization function syntax
valid = validate_function_syntax('anon.fake_email()')  # True
valid = validate_function_syntax('DROP TABLE users;')  # False - SQL injection blocked!
valid = validate_function_syntax('invalid_func()')     # False - must use anon. namespace

# Built-in security checks prevent:
# - SQL injection attempts
# - Functions outside anon namespace
# - Malformed syntax
```

#### Role Management Utilities

```python
from django_postgres_anon.utils import switch_to_role, reset_role, create_masked_role

# Create a new masked role
if create_masked_role('analyst_role', inherit_from='postgres'):
    print("Role created successfully")

# Switch to role programmatically
if switch_to_role('analyst_role', auto_create=True):
    # All queries now run as analyst_role
    data = SensitiveModel.objects.all()

    # Reset back to original role
    reset_role()
```

#### Logging & Audit Trail

```python
from django_postgres_anon.utils import create_operation_log

# All operations are automatically logged, but you can create custom logs
log_entry = create_operation_log(
    operation='custom_operation',
    user='admin@example.com',
    details={'rules_processed': 15, 'tables_affected': 3},
    success=True
)

# View logs in Django admin or programmatically
from django_postgres_anon.models import MaskingLog

recent_operations = MaskingLog.objects.filter(
    operation='apply',
    success=True
).order_by('-timestamp')[:10]
```

### Model & Admin Integration

#### Working with Models

```python
from django_postgres_anon.models import MaskingRule, MaskingPreset, MaskedRole, MaskingLog

# Create rules programmatically
rule = MaskingRule.objects.create(
    table_name='auth_user',
    column_name='email',
    function_expr='anon.fake_email()',
    enabled=True,
    notes='Anonymize user email addresses',
    depends_on_unique=False,  # Column has unique constraint
    performance_heavy=False   # Function is computationally expensive
)

# Mark rule as applied
rule.mark_applied()  # Sets applied_at timestamp

# Create presets for rule collections
preset = MaskingPreset.objects.create(
    name='User Data Anonymization',
    preset_type='custom',
    description='Anonymize all user PII'
)
preset.rules.add(rule)

# Load rules from YAML files
preset, rules_created = MaskingPreset.load_from_yaml(
    'path/to/rules.yaml',
    preset_name='My Custom Rules'
)

# Track database roles
role = MaskedRole.objects.create(
    role_name='analyst_reader',
    inherits_from='postgres',
    is_applied=True,
    description='Role for data analysts'
)
```

#### Django Admin Features

The package provides a rich Django admin interface with:

- **Batch Operations**: Apply/drop rules in bulk
- **Rule Validation**: Real-time syntax checking
- **Preview Mode**: See SQL without executing
- **Rule Suggestions**: AI-powered function recommendations
- **Audit Logs**: Complete operation history
- **Role Management**: Create and manage database roles
- **Preset Management**: Import/export rule collections

Navigate to `/admin/django_postgres_anon/` to access all features.

## 📊 Project Stats

- **🏷️ Version**: 0.1.0-alpha.1
- **🐍 Python**: 3.8+ (tested on 3.8, 3.9, 3.10, 3.11, 3.12)
- **🎸 Django**: 3.2+ (tested on 3.2, 4.0, 4.1, 4.2, 5.0)
- **🐘 PostgreSQL**: 12+ with anonymizer extension
- **📈 Test Coverage**: 90%+
- **🔧 Code Quality**: Black, isort, flake8, mypy, bandit
- **🛡️ Security**: SQL injection prevention, parameterized queries, audit logging

## 🛠️ Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/CuriousLearner/django-postgres-anonymizer.git
cd django-postgres-anonymizer

# Set up development environment
make dev

# Or manually:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
pip install -r requirements.txt
```

### 🧪 Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-all

# Run specific test types
make test-models
make test-commands
make test-integration  # Requires PostgreSQL with anon extension

# Run in Docker (includes PostgreSQL)
make docker-test        # Run all tests
make docker-shell       # Interactive shell for debugging
make docker-lint        # Run code quality checks
make docker-example     # Run example project on localhost:8000
make docker-clean       # Clean up Docker resources
```

### 🔍 Code Quality

```bash
# Install pre-commit hooks (one-time setup)
make pre-commit-install

# Run pre-commit hooks on staged files
make pre-commit-run

# Run pre-commit hooks on all files
make pre-commit-all

# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Security checks
make security

# Run all checks
make check
```

### 🚀 Example Project

```bash
# Set up example project
make example-setup

# Create demo data
make example-demo-data

# Run example server
make example-run

# Visit http://localhost:8000 for interactive demo
```

## 📚 API Reference

### Context Managers

```python
# anonymized_data(role_name=None, auto_create=True)
with anonymized_data():                    # Use default masked role
with anonymized_data('custom_role'):       # Use specific role
with anonymized_data('role', False):       # Don't auto-create role

# database_role(role_name)
with database_role('readonly_user'):       # Switch to any database role
```

### Decorators

```python
# @use_anonymized_data(role_name=None, auto_create=True)
@use_anonymized_data                       # Use default settings
@use_anonymized_data()                     # Same as above
@use_anonymized_data('custom_role')        # Use specific role
@use_anonymized_data('role', False)        # Don't auto-create role

# @database_role_required(role_name)
@database_role_required('readonly_user')   # Require specific role

# Aliases for semantic clarity
@anonymized_view                           # Alias for @use_anonymized_data
@masked_data                               # Alternative alias
```

### Mixins

```python
class AnonymizedDataMixin:
    anonymized_role = None          # Role name (optional)
    auto_create_role = True         # Auto-create role if missing

    # Override dispatch to use anonymized data
    def dispatch(self, request, *args, **kwargs):
        # Implementation handles role switching automatically
```

### Utility Functions

```python
# Database introspection
get_table_columns(table_name)                    # Get column list
check_table_exists(table_name)                   # Verify table exists
validate_anon_extension()                        # Check extension installed
get_anon_extension_info()                        # Get extension details

# Function validation & suggestions
validate_function_syntax(function_expr)          # Validate anon function
suggest_anonymization_functions(data_type, col)  # AI-powered suggestions
get_anon_functions()                             # List available functions

# Role management
switch_to_role(role_name, auto_create=True)      # Switch database role
reset_role()                                     # Reset to default role
create_masked_role(role_name, inherit_from)      # Create new role

# SQL generation
generate_anonymization_sql(rule)                 # Generate SECURITY LABEL SQL
generate_remove_anonymization_sql(table, col)    # Generate removal SQL

# Logging
create_operation_log(operation, user, **kwargs)  # Create audit log entry
```

### Models

```python
# MaskingRule - Core anonymization rules
class MaskingRule(models.Model):
    table_name = CharField(max_length=128)
    column_name = CharField(max_length=128)
    function_expr = CharField(max_length=512)
    enabled = BooleanField(default=True)
    applied_at = DateTimeField(null=True)

    def mark_applied()                            # Mark rule as applied
    def get_rendered_function()                   # Get function with {col} replaced

# MaskingPreset - Rule collections
class MaskingPreset(models.Model):
    name = CharField(max_length=100, unique=True)
    preset_type = CharField(choices=PRESET_CHOICES)
    rules = ManyToManyField(MaskingRule)

    @classmethod
    def load_from_yaml(yaml_path, preset_name)    # Load rules from YAML

# MaskedRole - Database role tracking
class MaskedRole(models.Model):
    role_name = CharField(max_length=64, unique=True)
    inherits_from = CharField(default='postgres')
    is_applied = BooleanField(default=False)

# MaskingLog - Audit trail
class MaskingLog(models.Model):
    operation = CharField(choices=OPERATION_CHOICES)
    details = JSONField(default=dict)
    success = BooleanField(default=True)
    user = CharField(max_length=150)
    timestamp = DateTimeField(auto_now_add=True)
```

### Management Commands

```bash
# Core operations
python manage.py anon_init [--force]              # Initialize extension
python manage.py anon_apply [--table] [--dry-run] # Apply rules
python manage.py anon_drop [--confirm]             # Remove anonymization
python manage.py anon_status [-v 2]               # Show status

# Rule management
python manage.py anon_load_yaml <preset_or_file>  # Load rules
python manage.py anon_validate                    # Validate rules
python manage.py anon_dump <output.sql>           # Create anonymized dump
```

### Configuration Settings

```python
POSTGRES_ANON = {
    # Core settings
    'DEFAULT_MASKED_ROLE': 'masked_reader',     # Default role for anonymization
    'ANONYMIZED_DATA_ROLE': 'masked_reader',    # Role for anonymized_data()
    'MASKED_GROUP': 'masked_users',             # Django group for middleware

    # Behavior settings
    'ENABLED': True,                            # Enable anonymization features
    'AUTO_APPLY_RULES': False,                  # Auto-apply when enabled
    'VALIDATE_FUNCTIONS': True,                 # Validate function syntax
    'ALLOW_CUSTOM_FUNCTIONS': False,            # Allow non-anon functions
    'ENABLE_LOGGING': True,                     # Enable audit logging
}
```

## Documentation

### Anonymization Functions

PostgreSQL Anonymizer provides numerous built-in functions:

| Function                         | Purpose                    | Example            |
| -------------------------------- | -------------------------- | ------------------ |
| `anon.fake_email()`              | Generate fake email        | `user@example.com` |
| `anon.fake_first_name()`         | Generate fake first name   | `John`             |
| `anon.fake_last_name()`          | Generate fake last name    | `Smith`            |
| `anon.fake_phone()`              | Generate fake phone number | `555-123-4567`     |
| `anon.fake_ssn()`                | Generate fake SSN          | `123-45-6789`      |
| `anon.partial(col, 2, '***', 2)` | Partial masking            | `Jo***th`          |
| `anon.hash(col)`                 | Hash the value             | `a1b2c3d4...`      |
| `anon.noise(col, 0.1)`           | Add noise to numbers       | `100` → `103.7`    |
| `anon.lorem_ipsum()`             | Lorem ipsum text           | Random text        |

#### Extended Function List

| Personal Data          | Contact Info          | Location              | Financial                        | Business                 |
| ---------------------- | --------------------- | --------------------- | -------------------------------- | ------------------------ |
| `anon.fake_name()`     | `anon.fake_phone()`   | `anon.fake_address()` | `anon.fake_ssn()`                | `anon.fake_company()`    |
| `anon.fake_username()` | `anon.fake_email()`   | `anon.fake_city()`    | `anon.fake_credit_card_number()` | `anon.fake_department()` |
| `anon.fake_password()` | `anon.fake_website()` | `anon.fake_state()`   | `anon.fake_iban()`               | `anon.fake_job_title()`  |
|                        |                       | `anon.fake_zipcode()` |                                  |                          |
|                        |                       | `anon.fake_country()` |                                  |                          |

#### Utility Functions

| Function                                    | Purpose               | Example                                                |
| ------------------------------------------- | --------------------- | ------------------------------------------------------ |
| `anon.random_string(length)`                | Random string         | `anon.random_string(10)`                               |
| `anon.random_int_between(min, max)`         | Random integer        | `anon.random_int_between(1, 100)`                      |
| `anon.random_date_between('start', 'end')`  | Random date           | `anon.random_date_between('2020-01-01', '2025-12-31')` |
| `anon.partial({col}, prefix, mask, suffix)` | Partial masking       | `anon.partial({col}, 2, '***', 2)`                     |
| `anon.hash({col})`                          | One-way hash          | `anon.hash({col})`                                     |
| `anon.noise({col}, ratio)`                  | Add statistical noise | `anon.noise({col}, 0.1)`                               |

### Advanced Configuration

#### Custom Anonymization Functions

```sql
-- Create custom function
CREATE OR REPLACE FUNCTION anon.fake_department()
RETURNS TEXT AS $$
SELECT CASE (random() * 5)::INT
    WHEN 0 THEN 'Engineering'
    WHEN 1 THEN 'Marketing'
    WHEN 2 THEN 'Sales'
    WHEN 3 THEN 'Support'
    ELSE 'Operations'
END;
$$ LANGUAGE SQL;
```

#### Environment-Specific Settings

```python
# settings/production.py
POSTGRES_ANON = {
    'AUTO_APPLY_RULES': False,  # Never auto-apply in production
    'VALIDATE_FUNCTIONS': True,
    'ALLOW_CUSTOM_FUNCTIONS': False,  # Restrict to built-in functions
    'ENABLE_LOGGING': True,
}

# settings/development.py
POSTGRES_ANON = {
    'AUTO_APPLY_RULES': True,   # Auto-apply for development
    'VALIDATE_FUNCTIONS': False,
    'ALLOW_CUSTOM_FUNCTIONS': True,
}
```

#### Performance Tuning

Performance tuning options are not yet implemented. Future versions may include batch processing and transaction control options.

## 🔒 Security Considerations

1. **Function Validation**: All anonymization functions are validated to prevent SQL injection
2. **Role-Based Access**: Separate database roles ensure proper data isolation
3. **Audit Logging**: All operations are logged for compliance and monitoring
4. **Parameterized Queries**: All database operations use parameterized queries
5. **Permission Checks**: Proper Django permissions for all admin actions

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test-all`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [PostgreSQL Anonymizer](https://postgresql-anonymizer.readthedocs.io/) - The core anonymization engine
- [Django](https://www.djangoproject.com/) - The web framework we love
- All contributors who help make this project better

## 📞 Support

- **Documentation**: [GitHub Wiki](https://github.com/CuriousLearner/django-postgres-anonymizer/wiki)
- **Issues**: [GitHub Issues](https://github.com/CuriousLearner/django-postgres-anonymizer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/CuriousLearner/django-postgres-anonymizer/discussions)

---

⭐ **If this project helps you, please consider giving it a star on GitHub!** ⭐

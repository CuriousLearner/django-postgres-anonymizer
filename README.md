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
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Professional-grade data anonymization for Django applications using PostgreSQL's native anonymizer extension.**

Anonymize sensitive data in development, testing, and analytics environments. Django PostgreSQL Anonymizer provides seamless integration with the PostgreSQL Anonymizer extension, enabling you to anonymize data at the database level with zero performance overhead. Ideal for development workflows, safe data sharing, and reducing privacy risks.

> **⚠️ Beta Status:** This package is currently in beta. Core features are stable, but APIs may still change before 1.0. Test thoroughly before production use.

## ✨ Why Choose This Library?

- **🚀 Zero Performance Overhead** - Database-level anonymization means no application slowdown
- **🔒 Role-Based Access** - Database role switching with audit logging
- **🎯 Effortless Django Integration** - Middleware, context managers, decorators, and admin interface
- **📋 Industry Presets** - Pre-built anonymization rules for healthcare, finance, e-commerce domains
- **⚡ Real-time Data Switching** - Toggle between real and anonymized data instantly, no downtime
- **🛡️ Security-First Design** - Built-in SQL injection prevention and function validation
- **🔄 Multiple Access Patterns** - Choose automatic (middleware), manual (context managers), or decorator-based approaches
- **🧪 Well-Tested** - Comprehensive test coverage with type safety

## 🚀 Quick Start

**Install:**

```bash
pip install django-postgres-anonymizer
```

**Configure:**

```python
# settings.py
INSTALLED_APPS = ['django_postgres_anon']
POSTGRES_ANON = {
    'ENABLED': True,
    'MASKED_GROUPS': ['analysts', 'qa_team'],
}
```

**Initialize:**

```bash
python manage.py migrate
python manage.py anon_init
```

**Use:**

```python
# Automatic (middleware) - users in masked groups see anonymized data
User.objects.all()  # Automatically anonymized for analysts/qa_team

# Manual (context manager)
from django_postgres_anon.context_managers import anonymized_data
with anonymized_data():
    users = User.objects.all()  # Anonymized data

# Decorator
from django_postgres_anon.decorators import use_anonymized_data
@use_anonymized_data
def sensitive_report(request):
    return render(request, 'report.html', {
        'users': User.objects.all()  # Automatically anonymized
    })
```

## 📚 Documentation

**📖 [Full Documentation](https://django-postgres-anonymizer.readthedocs.io/)**

- **[Installation Guide](https://django-postgres-anonymizer.readthedocs.io/en/latest/getting-started/installation.html)** - PostgreSQL setup and package installation
- **[Quick Start](https://django-postgres-anonymizer.readthedocs.io/en/latest/getting-started/quick-start.html)** - Get running in 10 minutes
- **[Configuration](https://django-postgres-anonymizer.readthedocs.io/en/latest/getting-started/configuration.html)** - 12-factor compliant settings
- **[User Guides](https://django-postgres-anonymizer.readthedocs.io/en/latest/guides/middleware.html)** - Middleware, context managers, decorators
- **[Examples](https://django-postgres-anonymizer.readthedocs.io/en/latest/examples/django-auth.html)** - Real-world use cases
- **[API Reference](https://django-postgres-anonymizer.readthedocs.io/en/latest/reference/settings.html)** - Complete API documentation

## 🎯 Real-World Use Cases

### Development & Testing

- **🔧 Safe Development** - Use realistic production-like data without privacy risks
- **🧪 QA & Testing** - Test with anonymized datasets that mirror production
- **🐛 Bug Reproduction** - Debug with real data patterns safely

### Data Sharing & Analytics

- **📊 Business Intelligence** - Share anonymized data with internal analysts
- **🤝 Third-party Integration** - Safely export data to vendors and partners
- **🎓 Training & Demos** - Create realistic demos without exposing sensitive data

### Privacy & Compliance

- **🔒 Privacy by Design** - Reduce risk of data exposure in non-production environments
- **📋 Compliance Support** - Tool to help with data protection requirements (consult legal counsel for compliance certification)
- **🛡️ Data Minimization** - Limit exposure of sensitive data to development teams

## 🤔 Why Not Just...?

**"Why not use fake data generators like Faker?"**
Application-level anonymization is slow and risky. Database-level anonymization is instant, secure, and happens before data ever reaches your application code.

**"Why not just delete sensitive data?"**
You lose referential integrity and realistic data patterns needed for proper testing and debugging. Anonymization preserves data structure and relationships.

**"Why not use separate test fixtures?"**
Fixtures don't reflect real-world edge cases, data distributions, or production issues. Anonymized production data gives you the real picture without the risk.

**"Why not query-by-query anonymization in views?"**
Manual anonymization is error-prone and easy to forget. This library provides automatic, middleware-based anonymization that just works.

## 🏗️ Architecture

```mermaid
graph LR
    A[Django App] --> B[Middleware/Context Manager]
    B --> C[PostgreSQL Role Switch]
    C --> D[Anonymized Views]
    D --> E[Masked Data]
```

**Core Components:**

- **Middleware** - Automatic anonymization for user groups
- **Context Managers** - Manual anonymized data access
- **Decorators** - View-level anonymization
- **Admin Interface** - Rule management and monitoring
- **Management Commands** - CLI operations and automation

## 🛡️ Security Features

- **SQL Injection Prevention** - Function validation and sanitization
- **Role-based Access Control** - Database-level security isolation
- **Audit Logging** - Complete operation tracking
- **Zero Data Leakage** - Original data never leaves the database
- **Validated Functions** - Whitelist-based anonymization function validation

## 📦 Requirements

- **Python** 3.8+
- **Django** 3.2+
- **PostgreSQL** 12+ with [Anonymizer extension](https://postgresql-anonymizer.readthedocs.io/)

## 🚧 Cloud Platform Support

| Platform | Support | Notes |
|----------|---------|-------|
| **Self-hosted PostgreSQL** | ✅ Full | Recommended for production |
| **Docker** | ✅ Full | Pre-built images available |
| **AWS RDS** | ❌ Limited | Extension requires superuser |
| **Azure PostgreSQL** | ❌ Limited | Extension not available |
| **Google Cloud SQL** | ❌ Limited | Extension not available |
| **Heroku Postgres** | ❌ Limited | Extension not available |

> **Note:** Managed cloud services don't support the PostgreSQL Anonymizer extension. Use self-hosted PostgreSQL or Docker for full functionality.

## 🧪 Example Project

```bash
git clone https://github.com/CuriousLearner/django-postgres-anonymizer.git
cd django-postgres-anonymizer/example_project
pip install -r requirements.txt
python manage.py migrate
python manage.py anon_init
python manage.py runserver
```

Visit `http://localhost:8000` to explore the interactive demo.

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](https://django-postgres-anonymizer.readthedocs.io/en/latest/contributing.html) for details.

- **🐛 Bug Reports** - [GitHub Issues](https://github.com/CuriousLearner/django-postgres-anonymizer/issues)
- **💡 Feature Requests** - [GitHub Discussions](https://github.com/CuriousLearner/django-postgres-anonymizer/discussions)
- **🔒 Security Issues** - <sanyam@sanyamkhurana.com>

## 📄 License

BSD-3-Clause License. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [PostgreSQL Anonymizer](https://postgresql-anonymizer.readthedocs.io/) - Core anonymization engine
- Django community - Framework excellence
- Contributors and early adopters - Valuable feedback

---

**⭐ Star this project** if you find it useful!

**📚 [Read the Docs](https://django-postgres-anonymizer.readthedocs.io/) | 🐛 [Report Issues](https://github.com/CuriousLearner/django-postgres-anonymizer/issues) | 💬 [Discussions](https://github.com/CuriousLearner/django-postgres-anonymizer/discussions)**

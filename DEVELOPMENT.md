# Development Guide

This guide covers development setup, code quality standards, and contribution guidelines for django-postgres-anonymizer.

## Quick Start

1. **Clone and set up the project:**

   ```bash
   git clone https://github.com/CuriousLearner/django-postgres-anonymizer.git
   cd django-postgres-anonymizer
   make install
   ```

2. **Install pre-commit hooks:**

   ```bash
   make pre-commit-install
   ```

3. **Run tests:**

   ```bash
   make test
   # or with Docker (includes PostgreSQL anonymizer extension)
   make docker-test
   ```

## Code Quality

This project uses automated code quality tools to maintain consistent, secure, and readable code.

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit to catch issues early:

```bash
# Install hooks (one-time setup)
make pre-commit-install

# Run on staged files only
make pre-commit-run

# Run on all files
make pre-commit-all
```

### Tools Used

- **Ruff**: Fast Python linter and formatter (replaces flake8, isort, and parts of pylint)
- **Black**: Code formatting (consistent with ruff)
- **Bandit**: Security vulnerability scanning
- **MyPy**: Static type checking
- **yamllint**: YAML file linting
- **markdownlint**: Markdown file linting

### Manual Code Quality Commands

```bash
# Format code with ruff
ruff format .

# Lint with ruff (auto-fix safe issues)
ruff check . --fix

# Format with black (if preferred)
make format

# Run all linting
make lint

# Security checks
make security

# Type checking
make type-check
```

## Configuration

### Ruff Configuration

The project uses comprehensive ruff configuration in `pyproject.toml`:

- **Line length**: 120 characters
- **Target Python**: 3.8+
- **Enabled rules**: pycodestyle, pyflakes, isort, bugbear, comprehensions, pyupgrade, naming, security, and more
- **Per-file ignores**: Different rules for tests, migrations, and example code

### Pre-commit Configuration

See `.pre-commit-config.yaml` for the complete list of hooks and their configurations.

## Testing

### Local Testing

```bash
# Run all tests
make test

# Run specific test types
make test-models
make test-commands
make test-integration  # Requires PostgreSQL with anon extension

# Run with coverage
pytest --cov=django_postgres_anon
```

### Docker Testing

Docker provides a complete environment with PostgreSQL anonymizer extension:

```bash
# Run tests in Docker
make docker-test

# Interactive development shell
make docker-shell

# Run example project
make docker-example
```

## Contributing

1. **Fork the repository** and create a feature branch
2. **Make your changes** following the code quality standards
3. **Add tests** for new functionality
4. **Run the test suite**: `make test` and `make docker-test`
5. **Run code quality checks**: `make pre-commit-all`
6. **Submit a pull request** with a clear description

### Commit Message Format

Follow conventional commit format:

```
type(scope): description

Examples:
feat(models): add new anonymization rule model
fix(utils): handle edge case in function validation
docs(readme): update installation instructions
test(commands): add tests for anon_apply command
```

### Code Style Guidelines

- **Line length**: 120 characters maximum
- **Type hints**: Use type hints for public APIs
- **Docstrings**: Use Google-style docstrings for functions and classes
- **Imports**: Group imports as: stdlib, django, third-party, first-party
- **Security**: Never commit secrets or hardcoded credentials

## Project Structure

```
django-postgres-anonymizer/
├── django_postgres_anon/           # Main package
│   ├── admin.py                    # Django admin interface
│   ├── models.py                   # Database models
│   ├── views.py                    # Web views
│   ├── utils.py                    # Utility functions
│   ├── management/commands/        # Django commands
│   └── config/presets/             # Anonymization presets
├── tests/                          # Test suite
├── example_project/                # Example Django project
├── docker/                         # Docker configuration
├── docs/                           # Documentation
└── .pre-commit-config.yaml         # Pre-commit configuration
```

## Environment Variables

For development and testing:

```bash
# Database configuration
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=postgres_anon_example
export DB_USER=your_username
export DB_PASSWORD=your_password

# Testing
export DJANGO_SETTINGS_MODULE=tests.settings
```

## Debugging

### Using the example project

```bash
cd example_project
python manage.py runserver
# Visit http://localhost:8000/admin
```

### Using Docker for debugging

```bash
make docker-shell
# Interactive Python shell with full environment
```

### Database debugging

```bash
# Local PostgreSQL
psql -h localhost -U your_username -d postgres_anon_example

# Docker PostgreSQL
docker-compose -f docker/docker-compose.yml exec db psql -U postgres test_anon_db
```

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite: `make docker-test`
4. Run code quality checks: `make pre-commit-all`
5. Create and push a git tag
6. GitHub Actions will handle the release

## Getting Help

- **Issues**: Report bugs or request features on GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Security**: Report security issues privately via email

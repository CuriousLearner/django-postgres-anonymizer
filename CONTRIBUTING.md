# Contributing to Django PostgreSQL Anonymizer

Thank you for your interest in contributing to Django PostgreSQL Anonymizer! This guide will help you get started.

## 🚀 Quick Start

1. **Fork the repository**

   ```bash
   git clone https://github.com/CuriousLearner/django-postgres-anonymizer.git
   cd django-postgres-anonymizer
   ```

2. **Set up development environment**

   ```bash
   make dev
   # Or manually:
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   pip install -r requirements.txt
   ```

3. **Run tests to ensure everything works**

   ```bash
   make test-all
   ```

## 📝 Commit Message Format

This project follows [Conventional Commits](https://www.conventionalcommits.org/) specification. Please format your commit messages as:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `build`: Changes that affect the build system or external dependencies
- `ci`: Changes to CI configuration files and scripts
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

### Examples

```bash
feat: add support for custom anonymization functions
fix: resolve memory leak in batch processing
docs: update installation instructions
feat(presets): add new healthcare anonymization preset
fix(utils)!: breaking change to table introspection API
```

### Setup Git Message Template

```bash
git config commit.template .gitmessage
```

## 🧪 Testing

- **Run all tests**: `make test-all`
- **Run specific tests**: `make test-models`, `make test-commands`
- **Run integration tests**: `make test-integration` (requires PostgreSQL with anon extension)
- **Check coverage**: Coverage reports are generated in `htmlcov/`

## 🔍 Code Quality

Before submitting a PR, ensure your code passes all quality checks:

```bash
make check  # Runs all checks below
make lint   # Flake8 linting
make format # Black + isort formatting
make type-check  # MyPy type checking
make security    # Bandit security scanning
```

## 📋 Pull Request Process

1. **Create a feature branch**

   ```bash
   git checkout -b feat/amazing-new-feature
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed
   - Add your changes to `CHANGELOG.md` under `[Unreleased]`

3. **Test your changes**

   ```bash
   make test-all
   make check
   ```

4. **Commit your changes** (using conventional commits format)

   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   ```

5. **Push to your fork and create a PR**

   ```bash
   git push origin feat/amazing-new-feature
   ```

6. **PR Requirements**
   - [ ] All tests pass
   - [ ] Code quality checks pass
   - [ ] Documentation updated (if applicable)
   - [ ] Changelog updated
   - [ ] Conventional commit format used

## 🎯 Areas for Contribution

### High Priority

- **New Anonymization Presets**: Industry-specific rule sets
- **Additional Anonymization Functions**: Custom PostgreSQL functions
- **Performance Optimizations**: Large dataset handling improvements
- **Documentation**: Examples, tutorials, best practices

### Medium Priority

- **Admin Interface Enhancements**: Better UX for rule management
- **API Improvements**: Additional REST endpoints
- **Monitoring & Alerting**: Integration with monitoring systems
- **Database Support**: Support for other PostgreSQL-compatible databases

### Good First Issues

- **Test Coverage**: Increase test coverage for edge cases
- **Documentation**: Fix typos, improve examples
- **Bug Fixes**: Address issues marked as "good first issue"
- **Code Cleanup**: Refactoring, type hints improvements

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment Details**
   - Python version
   - Django version
   - PostgreSQL version
   - Package version

2. **Steps to Reproduce**
   - Minimal code example
   - Expected vs actual behavior
   - Error messages/stack traces

3. **Additional Context**
   - Relevant configuration
   - Database schema (if relevant)
   - Anonymization rules (if relevant)

## 💡 Feature Requests

For new features, please:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** - why is this needed?
3. **Provide examples** - how would it work?
4. **Consider backwards compatibility**
5. **Offer to implement** - we welcome contributions!

## 📚 Development Guidelines

### Code Style

- Follow PEP 8 (enforced by flake8)
- Use Black for code formatting
- Use isort for import sorting
- Add type hints where possible
- Write docstrings for public APIs

### Testing

- Write tests for all new functionality
- Aim for >95% test coverage
- Use descriptive test names
- Include both unit and integration tests
- Mock external dependencies appropriately

### Documentation

- Update docstrings for API changes
- Add examples for new features
- Update README if user-facing changes
- Consider adding to example project

### Security

- Never commit secrets or credentials
- Validate all user inputs
- Use parameterized queries
- Follow security best practices
- Run security checks with `make security`

## 🙋‍♀️ Getting Help

- **Documentation**: Check the README and example project
- **Issues**: Search existing issues for similar problems
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Don't hesitate to ask for feedback

## 📄 License

By contributing to Django PostgreSQL Anonymizer, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Django PostgreSQL Anonymizer! 🎉

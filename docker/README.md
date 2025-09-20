# Docker Setup for Django PostgreSQL Anonymizer

This directory contains Docker configuration for development, testing, and running the example project.

## Quick Start

```bash
# Run tests in Docker
make docker-test

# Open interactive shell
make docker-shell

# Run linting checks
make docker-lint

# Run example project
make docker-example

# Clean up resources
make docker-clean
```

## Services

### `db` - PostgreSQL Database

- PostgreSQL 16 database server
- Automatically configured for testing
- Health checks enabled

### `test` - Test Runner

- Runs the full test suite
- Includes all testing dependencies
- Connected to PostgreSQL database

### `lint` - Code Quality Checks

- Runs flake8, black, and isort
- Validates code formatting and style

### `shell` - Development Shell

- Interactive bash shell for debugging
- Full access to the codebase
- Connected to PostgreSQL database

### `example` - Example Project

- Runs the example Django project
- Available at <http://localhost:8000>
- Demonstrates package usage

## Files

- `Dockerfile` - Multi-stage build for different environments
- `docker-compose.yml` - Service definitions and configuration

## Usage Examples

### Running Specific Tests

```bash
docker-compose -f docker/docker-compose.yml run --rm test pytest tests/test_models.py -v
```

### Interactive Python Shell

```bash
docker-compose -f docker/docker-compose.yml run --rm shell python
```

### Database Access

```bash
docker-compose -f docker/docker-compose.yml exec db psql -U postgres test_anon_db
```

## Notes

- The Docker setup uses the official PostgreSQL Anonymizer image from GitLab
- This provides PostgreSQL with the `anon` extension pre-installed
- The extension is the core functionality that this Django package wraps
- Volumes are used to persist database data and test reports
- The setup is optimized for development and testing, not production use

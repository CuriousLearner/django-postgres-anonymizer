# Use the official PostgreSQL Anonymizer Docker image
FROM registry.gitlab.com/dalibo/postgresql_anonymizer:latest

# The image already includes PostgreSQL with the anonymizer extension installed
# Just add our initialization script
COPY docker/init-anon.sql /docker-entrypoint-initdb.d/

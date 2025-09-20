-- Initialize anonymizer extension
CREATE EXTENSION IF NOT EXISTS anon CASCADE;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE test_anon_db TO postgres;

-- Database initialization script for Quote Master Pro

-- Create databases
CREATE DATABASE IF NOT EXISTS quote_master;
CREATE DATABASE IF NOT EXISTS quote_master_test;

-- Create user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'quote_user') THEN
        CREATE USER quote_user WITH PASSWORD 'quote_password';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE quote_master TO quote_user;
GRANT ALL PRIVILEGES ON DATABASE quote_master_test TO quote_user;

-- Connect to main database
\c quote_master;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS ml;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO quote_user;
GRANT ALL ON SCHEMA analytics TO quote_user;
GRANT ALL ON SCHEMA ml TO quote_user;

-- Connect to test database
\c quote_master_test;

-- Enable extensions for test database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create schemas for test database
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS ml;

-- Grant schema permissions for test database
GRANT ALL ON SCHEMA public TO quote_user;
GRANT ALL ON SCHEMA analytics TO quote_user;
GRANT ALL ON SCHEMA ml TO quote_user;
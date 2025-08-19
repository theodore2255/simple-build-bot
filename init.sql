-- Database initialization script
-- This script creates the necessary extensions and sets up initial configuration

-- Create UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create vector extension for pgvector (if using vector database)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Set timezone
SET timezone = 'UTC';

-- Create indexes that might be useful
-- These will be created by SQLAlchemy migrations, but we can prepare them here

-- Example: Create index on document filename for faster searches
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_filename ON documents(filename);

-- Example: Create index on document upload timestamp
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_created_at ON documents(created_at);

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE rag_documents TO rag_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rag_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rag_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO rag_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO rag_user;

-- Add evaluation columns to mcp_test_results table
ALTER TABLE mcp_test_results
ADD COLUMN final_score INTEGER,
ADD COLUMN sustainability_score INTEGER,
ADD COLUMN popularity_score INTEGER,
ADD COLUMN sustainability_details JSONB,
ADD COLUMN popularity_details JSONB,
ADD COLUMN evaluation_timestamp TIMESTAMP WITH TIME ZONE;

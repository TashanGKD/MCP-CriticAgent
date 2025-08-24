-- Create the repository evaluations table
CREATE TABLE mcp_repository_evaluations (
    github_url TEXT PRIMARY KEY,
    final_score INTEGER,
    sustainability_score INTEGER,
    popularity_score INTEGER,
    sustainability_details JSONB,
    popularity_details JSONB,
    last_evaluated_at TIMESTAMP WITH TIME ZONE
);

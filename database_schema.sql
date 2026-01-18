-- HiveCodr Database Schema
-- Execute this in your Supabase SQL Editor

-- Table: generations
-- Stores all code generations created by users
CREATE TABLE IF NOT EXISTS generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users NOT NULL,
    requirements TEXT NOT NULL,
    generated_code JSONB,
    agent_outputs JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: user_usage
-- Tracks user generation counts for rate limiting
CREATE TABLE IF NOT EXISTS user_usage (
    user_id UUID PRIMARY KEY REFERENCES auth.users,
    generation_count INT DEFAULT 0,
    last_reset TIMESTAMP DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE generations ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_usage ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their own generations
CREATE POLICY "Users see own generations" ON generations
    FOR ALL
    USING (auth.uid() = user_id);

-- RLS Policy: Users can only see their own usage data
CREATE POLICY "Users see own usage" ON user_usage
    FOR ALL
    USING (auth.uid() = user_id);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_generations_user_id ON generations(user_id);
CREATE INDEX IF NOT EXISTS idx_generations_created_at ON generations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_usage_user_id ON user_usage(user_id);

-- Grant permissions (Supabase handles this automatically, but included for completeness)
GRANT ALL ON generations TO authenticated;
GRANT ALL ON user_usage TO authenticated;

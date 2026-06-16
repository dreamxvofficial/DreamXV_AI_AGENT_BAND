-- Migration: Ensure users table has the correct schema
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    onboarded BOOLEAN DEFAULT FALSE,
    onboarding_answers JSONB DEFAULT '{}'::jsonb
);

-- If full_name does not exist but name does, copy the data and drop name
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='users' AND column_name='name'
    ) AND NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='users' AND column_name='full_name'
    ) THEN
        ALTER TABLE users RENAME COLUMN name TO full_name;
    ELSIF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='users' AND column_name='name'
    ) AND EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='users' AND column_name='full_name'
    ) THEN
        -- Both exist, copy data from name to full_name if full_name is null
        UPDATE users SET full_name = name WHERE full_name IS NULL;
        ALTER TABLE users DROP COLUMN name;
    END IF;
END $$;

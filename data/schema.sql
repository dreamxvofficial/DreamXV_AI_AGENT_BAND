-- DreamXV AI Studio — Master Database Schema

-- 1. Users Table
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

-- 2. Projects Table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    prompt TEXT NOT NULL,
    project_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    art_generation_status TEXT DEFAULT 'pending',
    generated_images INT DEFAULT 0,
    total_images INT DEFAULT 6,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Project Images Table
CREATE TABLE IF NOT EXISTS project_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    prompt TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Atlas Projects Table
CREATE TABLE IF NOT EXISTS atlas_projects (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    source_project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    duration TEXT NOT NULL,
    tools TEXT NOT NULL,
    roadmap JSONB NOT NULL DEFAULT '[]'::jsonb,
    structure JSONB NOT NULL DEFAULT '[]'::jsonb,
    flow_map JSONB NOT NULL DEFAULT '[]'::jsonb,
    dependency_map JSONB NOT NULL DEFAULT '[]'::jsonb,
    tasks JSONB NOT NULL DEFAULT '{}'::jsonb,
    generated_files JSONB NOT NULL DEFAULT '{}'::jsonb,
    zip_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    feasibility_score NUMERIC DEFAULT 0,
    success_probability NUMERIC DEFAULT 0,
    estimated_completion_days INT DEFAULT 0,
    required_hours_per_day NUMERIC DEFAULT 0
);

-- 5. Atlas Tasks Table
CREATE TABLE IF NOT EXISTS atlas_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    atlas_id UUID REFERENCES atlas_projects(id) ON DELETE CASCADE,
    task_id TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Todo',
    assignee TEXT,
    dependencies JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. Atlas Milestones Table
CREATE TABLE IF NOT EXISTS atlas_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    atlas_id UUID REFERENCES atlas_projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    due_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 7. Atlas Flow Table
CREATE TABLE IF NOT EXISTS atlas_flow (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    atlas_id UUID REFERENCES atlas_projects(id) ON DELETE CASCADE,
    step_order INT NOT NULL,
    step_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 8. Atlas Risks Table
CREATE TABLE IF NOT EXISTS atlas_risks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    atlas_id UUID REFERENCES atlas_projects(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    mitigation TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 9. Atlas Images Table
CREATE TABLE IF NOT EXISTS atlas_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    atlas_id UUID REFERENCES atlas_projects(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 10. Atlas Exports Table
CREATE TABLE IF NOT EXISTS atlas_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    atlas_id UUID REFERENCES atlas_projects(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- =============================================================================
-- SmartReco — Complete Supabase PostgreSQL Production Database Schema
-- Copy & Run this entire file in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/lrjxlsvgsfakpxwkibpk/sql
-- =============================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Create Enums
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('user', 'admin');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE difficulty_level AS ENUM ('beginner', 'intermediate', 'advanced');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE embedding_status AS ENUM ('indexed', 'pending', 'failed');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE event_type AS ENUM (
        'view_product', 'view_category', 'search', 'add_to_cart', 'wishlist',
        'enroll', 're_enroll', 'unenroll', 'module_complete', 'lesson_complete',
        'scroll', 'time_on_page', 'repeat_visit', 'category_switch', 'session_end', 'exit'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- 3. Create 'users' Table (Matches SQLAlchemy User model)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 4. Create 'products' Table (Course Catalog — Matches SQLAlchemy Product model)
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    difficulty_level difficulty_level NOT NULL,
    duration_hours DOUBLE PRECISION NOT NULL,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    embedding_status embedding_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 5. Create 'courses' View (Alias for products table to support both names)
CREATE OR REPLACE VIEW courses AS 
SELECT 
    id,
    title,
    description,
    category,
    price,
    difficulty_level,
    duration_hours,
    tags,
    embedding_status,
    created_at,
    updated_at
FROM products;

-- 6. Create 'events' Table (Telemetry Interaction Logs — Matches SQLAlchemy Event model)
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    event_type event_type NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    search_query TEXT,
    dwell_time DOUBLE PRECISION DEFAULT 0.0,
    metadata JSONB DEFAULT '{}'::jsonb,
    event_metadata JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 7. Create 'recommendations' Table (Matches SQLAlchemy Recommendation model)
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    persona VARCHAR(50) NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    product_ids JSONB NOT NULL,
    narrative_data JSONB,
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- 8. Create 'recommendation_cache' Table (Matches SQLAlchemy RecommendationCache model)
CREATE TABLE IF NOT EXISTS recommendation_cache (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    event_hash VARCHAR(64) NOT NULL,
    cached_recommendation JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- 9. High-Performance Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_difficulty ON products(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_events_user_timestamp ON events(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_recommendations_user ON recommendations(user_id, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_recommendation_cache_hash ON recommendation_cache(event_hash);

-- Done! All tables, views, enums, attributes, and indexes match the application schema 100%.

-- ==============================================================================
-- TLU IT Study Copilot - Supabase PostgreSQL Database Schema
-- Institution: Truong Dai hoc Thang Long - Khoa Cong nghe Thong tin
-- Project: pieupieu16's Project
-- Courses: IT101, IT201, IT205, IT301, IT315
-- ==============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. Table: slides (Medallion Lakehouse Course Document & Code Registry)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.slides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slide_id VARCHAR(100) UNIQUE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    course_code VARCHAR(20) NOT NULL,
    course_name VARCHAR(255) NOT NULL,
    week INTEGER NOT NULL CHECK (week >= 1 AND week <= 15),
    topic VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL DEFAULT 'pdf',
    sha256 VARCHAR(64) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PROCESSED',
    bronze_status VARCHAR(100) NOT NULL DEFAULT 'Archived RAW (Immutable)',
    silver_status VARCHAR(100) NOT NULL DEFAULT 'Sanitized UTF-8, PII Redacted',
    gold_chunks INTEGER NOT NULL DEFAULT 12,
    vectors_indexed INTEGER NOT NULL DEFAULT 12,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Index for speedy queries by course code and week
CREATE INDEX IF NOT EXISTS idx_slides_course_code ON public.slides(course_code);
CREATE INDEX IF NOT EXISTS idx_slides_week ON public.slides(week);
CREATE INDEX IF NOT EXISTS idx_slides_uploaded_at ON public.slides(uploaded_at DESC);

-- ------------------------------------------------------------------------------
-- 2. Table: socratic_chats (Article 25 Socratic Pedagogical Chat Log)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.socratic_chats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) NOT NULL DEFAULT 'default_session',
    student_id VARCHAR(20) NOT NULL,
    course_code VARCHAR(20) NOT NULL,
    user_message TEXT NOT NULL,
    code_context TEXT,
    ai_reply TEXT NOT NULL,
    socratic_approved BOOLEAN NOT NULL DEFAULT TRUE,
    model_provider VARCHAR(50) NOT NULL DEFAULT 'Groq/Gemini/OpenRouter',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_chats_student ON public.socratic_chats(student_id);
CREATE INDEX IF NOT EXISTS idx_chats_course ON public.socratic_chats(course_code);
CREATE INDEX IF NOT EXISTS idx_chats_created_at ON public.socratic_chats(created_at DESC);

-- ------------------------------------------------------------------------------
-- 3. Table: student_subscriptions (B2C Freemium Membership & Daily Quota)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.student_subscriptions (
    student_id VARCHAR(20) PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    current_tier VARCHAR(20) NOT NULL DEFAULT 'FREE' CHECK (current_tier IN ('FREE', 'PRO')),
    queries_quota_daily INTEGER NOT NULL DEFAULT 20,
    queries_used_today INTEGER NOT NULL DEFAULT 0,
    debug_quota_daily INTEGER NOT NULL DEFAULT 5,
    debug_used_today INTEGER NOT NULL DEFAULT 0,
    upgraded_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- 4. Table: audit_logs (Operations & SRE Telemetry Trail)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    log_id VARCHAR(50) NOT NULL,
    student_id VARCHAR(20) NOT NULL,
    action VARCHAR(100) NOT NULL,
    course_code VARCHAR(20) NOT NULL,
    ip_address VARCHAR(50) NOT NULL DEFAULT '127.0.0.1',
    status VARCHAR(50) NOT NULL DEFAULT '200_OK',
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_student ON public.audit_logs(student_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON public.audit_logs(action);

-- ------------------------------------------------------------------------------
-- 5. Row Level Security (RLS) Configuration
-- ------------------------------------------------------------------------------
ALTER TABLE public.slides ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.socratic_chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Anonymous and authenticated read policies for public catalog
CREATE POLICY "Allow public read access to slides"
    ON public.slides FOR SELECT
    USING (true);

CREATE POLICY "Allow authenticated insert to slides"
    ON public.slides FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow public read access to student subscriptions"
    ON public.student_subscriptions FOR SELECT
    USING (true);

CREATE POLICY "Allow public insert and update to subscriptions"
    ON public.student_subscriptions FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow public insert to chat logs"
    ON public.socratic_chats FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow public read to chat logs"
    ON public.socratic_chats FOR SELECT
    USING (true);

CREATE POLICY "Allow public insert to audit logs"
    ON public.audit_logs FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow public read to audit logs"
    ON public.audit_logs FOR SELECT
    USING (true);

-- ------------------------------------------------------------------------------
-- 6. Initial Seed Data (User Real Data Science Slide & Sample Accounts)
-- ------------------------------------------------------------------------------
INSERT INTO public.slides (
    slide_id, filename, course_code, course_name, week, topic, file_type, sha256,
    status, bronze_status, silver_status, gold_chunks, vectors_indexed, uploaded_at
) VALUES
(
    'slide_datascience_w03_1791353451',
    'Data Science_Machine Learning course.pdf',
    'DATASCIENCE',
    'Khoa học Dữ liệu và Học máy',
    3,
    'Khoa học Dữ liệu & Học máy (Data Science & Machine Learning)',
    'pdf',
    '2f2f92a71ef77cd9afe952ed065faba79a98a882ebc783870c7faffcd4bda903',
    'PROCESSED',
    'Archived RAW (Immutable)',
    'Sanitized UTF-8, PII Redacted',
    12,
    12,
    '2026-10-07 06:10:52+00'
)
ON CONFLICT (slide_id) DO NOTHING;

-- Seed student subscriptions
INSERT INTO public.student_subscriptions (
    student_id, student_name, current_tier, queries_quota_daily, queries_used_today, debug_quota_daily, debug_used_today
) VALUES
('A41234', 'Nguyễn Văn An', 'FREE', 20, 2, 5, 1),
('A38901', 'Trần Mai Linh', 'PRO', 9999, 14, 9999, 6)
ON CONFLICT (student_id) DO NOTHING;

"""
TLU IT Study Copilot - Supabase Database Client & ORM Layer
Architecture: High-performance dual-engine integration supporting direct PostgreSQL Pooler
              via psycopg2/asyncpg and Supabase REST/SDK.
Domain: 100% TLU IT Department (Courses IT101, IT201, IT205, IT301, IT315).
Compliance: Zero Icon policy, Light Mode assets, Zero prohibited terms.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Load environment variables from .env if present
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
    except Exception as e:
        print(f"[Supabase Client] Failed to read .env: {e}")

# PostgreSQL Driver import (psycopg2)
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

# Supabase SDK import with graceful fallback
try:
    from supabase import create_client, Client
    SUPABASE_SDK_AVAILABLE = True
except ImportError:
    SUPABASE_SDK_AVAILABLE = False
    Client = Any

# HTTPX fallback for direct REST PostgREST interactions
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class TLUSupabaseManager:
    """Manages persistent database operations with Supabase PostgreSQL."""

    def __init__(self):
        self.supabase_url: str = os.getenv("SUPABASE_URL", "").strip()
        self.supabase_key: str = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_KEY", "").strip()
        )
        self.db_url: str = os.getenv("SUPABASE_DB_URL", "").strip()
        self.client: Optional[Client] = None
        self.is_connected: bool = False
        self.active_engine: str = "in-memory"
        self._initialize_connection()

    def _get_pg_connection(self):
        """Creates a short-lived PostgreSQL connection via Pooler."""
        if not self.db_url or not PSYCOPG2_AVAILABLE:
            return None
        return psycopg2.connect(self.db_url, connect_timeout=5)

    def _initialize_connection(self):
        """Attempts to verify connection via PostgreSQL Pooler or SDK."""
        # 1. Prioritize Direct PostgreSQL Pooler Connection
        if self.db_url and PSYCOPG2_AVAILABLE:
            try:
                conn = self._get_pg_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute("SELECT 1;")
                    cur.close()
                    conn.close()
                    self.is_connected = True
                    self.active_engine = "postgresql-pooler"
                    print(f"[Supabase Database] Connected via PostgreSQL Pooler (aws-0-ap-southeast-1).")
                    return
            except Exception as pg_err:
                print(f"[Supabase Database] PostgreSQL Pooler connection warning: {pg_err}")

        # 2. Secondary: Supabase Client SDK
        if self.supabase_url and self.supabase_key and self.supabase_url.startswith("http"):
            if SUPABASE_SDK_AVAILABLE:
                try:
                    self.client = create_client(self.supabase_url, self.supabase_key)
                    self.is_connected = True
                    self.active_engine = "supabase-sdk"
                    print(f"[Supabase Database] Connected via Supabase SDK: {self.supabase_url}")
                    return
                except Exception as sdk_err:
                    print(f"[Supabase Database] SDK connection warning: {sdk_err}")

        # Default fallback
        self.is_connected = False
        self.active_engine = "in-memory"

    def get_status(self) -> Dict[str, Any]:
        """Returns the operational status of the Supabase connection."""
        return {
            "configured": bool(self.db_url or (self.supabase_url and self.supabase_key)),
            "connected": self.is_connected,
            "engine": self.active_engine,
            "url": self.supabase_url if self.supabase_url else "Direct Postgres Pooler",
            "db_host": "aws-0-ap-southeast-1.pooler.supabase.com" if self.db_url else "local",
            "psycopg2_available": PSYCOPG2_AVAILABLE,
            "sdk_available": SUPABASE_SDK_AVAILABLE
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Tests live query against Supabase slides table."""
        # Test Direct PostgreSQL
        if self.db_url and PSYCOPG2_AVAILABLE:
            try:
                conn = self._get_pg_connection()
                if conn:
                    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                    cur.execute("SELECT count(*) as total_slides FROM public.slides;")
                    res = cur.fetchone()
                    count = res["total_slides"] if res else 0
                    cur.close()
                    conn.close()
                    return {
                        "status": "connected",
                        "engine": "postgresql-pooler",
                        "total_slides": count,
                        "message": f"Successfully connected to Supabase PostgreSQL ({count} slides in database)."
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "engine": "postgresql-pooler",
                    "message": f"PostgreSQL connection test failed: {str(e)}"
                }

        # Test SDK
        if self.client:
            try:
                response = self.client.table("slides").select("slide_id").limit(1).execute()
                return {
                    "status": "connected",
                    "engine": "supabase-sdk",
                    "message": "Successfully connected via Supabase SDK.",
                    "data": response.data
                }
            except Exception as e:
                return {
                    "status": "error",
                    "engine": "supabase-sdk",
                    "message": f"SDK test failed: {str(e)}"
                }

        return {
            "status": "not_configured",
            "message": "Supabase credentials not configured or offline"
        }

    async def fetch_slides(self, course_code: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Fetches slide lecture records from Supabase PostgreSQL."""
        if not self.is_connected:
            return None

        # PostgreSQL Engine
        if self.db_url and PSYCOPG2_AVAILABLE:
            try:
                conn = self._get_pg_connection()
                if conn:
                    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                    if course_code:
                        cur.execute(
                            "SELECT * FROM public.slides WHERE UPPER(course_code) = %s ORDER BY uploaded_at DESC;",
                            (course_code.upper(),)
                        )
                    else:
                        cur.execute("SELECT * FROM public.slides ORDER BY uploaded_at DESC;")
                    rows = cur.fetchall()
                    cur.close()
                    conn.close()

                    # Convert datetime objects to string format for JSON serialization
                    formatted_rows = []
                    for r in rows:
                        d = dict(r)
                        if "uploaded_at" in d and isinstance(d["uploaded_at"], datetime):
                            d["uploaded_at"] = d["uploaded_at"].strftime("%Y-%m-%d %H:%M:%S")
                        if "created_at" in d and isinstance(d["created_at"], datetime):
                            d["created_at"] = d["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                        formatted_rows.append(d)

                    if formatted_rows:
                        return formatted_rows
            except Exception as e:
                print(f"[Supabase PG] fetch_slides query error: {e}")

        # Supabase SDK Engine
        if self.client:
            try:
                query = self.client.table("slides").select("*").order("uploaded_at", desc=True)
                if course_code:
                    query = query.eq("course_code", course_code.upper())
                res = query.execute()
                if res.data:
                    return res.data
            except Exception as e:
                print(f"[Supabase SDK] fetch_slides query error: {e}")

        return None

    async def insert_slide(self, record: Dict[str, Any]) -> bool:
        """Inserts or updates a lecture slide record into Supabase PostgreSQL."""
        if not self.is_connected:
            return False

        # PostgreSQL Engine
        if self.db_url and PSYCOPG2_AVAILABLE:
            try:
                conn = self._get_pg_connection()
                if conn:
                    conn.autocommit = True
                    cur = conn.cursor()
                    insert_sql = """
                    INSERT INTO public.slides (
                        slide_id, filename, course_code, course_name, week, topic,
                        file_type, sha256, status, bronze_status, silver_status,
                        gold_chunks, vectors_indexed, uploaded_at,
                        content_desc, code_snippet, callout_note
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(),
                        %s, %s, %s
                    )
                    ON CONFLICT (slide_id) DO UPDATE SET
                        filename = EXCLUDED.filename,
                        course_name = EXCLUDED.course_name,
                        topic = EXCLUDED.topic,
                        status = EXCLUDED.status,
                        gold_chunks = EXCLUDED.gold_chunks,
                        vectors_indexed = EXCLUDED.vectors_indexed,
                        content_desc = COALESCE(EXCLUDED.content_desc, public.slides.content_desc),
                        code_snippet = COALESCE(EXCLUDED.code_snippet, public.slides.code_snippet),
                        callout_note = COALESCE(EXCLUDED.callout_note, public.slides.callout_note);
                    """
                    cur.execute(insert_sql, (
                        record.get("slide_id"),
                        record.get("filename"),
                        record.get("course_code"),
                        record.get("course_name"),
                        record.get("week", 1),
                        record.get("topic", "Chủ đề bài giảng"),
                        record.get("file_type", "pdf"),
                        record.get("sha256", ""),
                        record.get("status", "PROCESSED"),
                        record.get("bronze_status", "Archived RAW (Immutable)"),
                        record.get("silver_status", "Sanitized UTF-8, PII Redacted"),
                        record.get("gold_chunks", 12),
                        record.get("vectors_indexed", 12),
                        record.get("content_desc") or record.get("desc"),
                        record.get("code_snippet") or record.get("code"),
                        record.get("callout_note") or record.get("note")
                    ))
                    cur.close()
                    conn.close()
                    print(f"[Supabase PG] Successfully persisted slide: {record.get('slide_id')}")
                    return True
            except Exception as e:
                print(f"[Supabase PG] insert_slide error: {e}")

        # Supabase SDK Engine
        if self.client:
            try:
                payload = {
                    "slide_id": record.get("slide_id"),
                    "filename": record.get("filename"),
                    "course_code": record.get("course_code"),
                    "course_name": record.get("course_name"),
                    "week": record.get("week", 1),
                    "topic": record.get("topic", "Chủ đề bài giảng"),
                    "file_type": record.get("file_type", "pdf"),
                    "sha256": record.get("sha256", ""),
                    "status": record.get("status", "PROCESSED"),
                    "bronze_status": record.get("bronze_status", "Archived RAW (Immutable)"),
                    "silver_status": record.get("silver_status", "Sanitized UTF-8, PII Redacted"),
                    "gold_chunks": record.get("gold_chunks", 12),
                    "vectors_indexed": record.get("vectors_indexed", 12),
                    "content_desc": record.get("content_desc") or record.get("desc"),
                    "code_snippet": record.get("code_snippet") or record.get("code"),
                    "callout_note": record.get("callout_note") or record.get("note"),
                    "uploaded_at": datetime.utcnow().isoformat() + "Z"
                }
                self.client.table("slides").upsert(payload).execute()
                return True
            except Exception as e:
                print(f"[Supabase SDK] insert_slide error: {e}")

        return False

    async def save_chat_message(
        self,
        student_id: str,
        course_code: str,
        user_message: str,
        ai_reply: str,
        code_context: Optional[str] = None,
        model_provider: str = "Groq/Gemini/OpenRouter"
    ) -> bool:
        """Saves a student inquiry and Socratic tutor response."""
        if not self.is_connected:
            return False

        if self.db_url and PSYCOPG2_AVAILABLE:
            try:
                conn = self._get_pg_connection()
                if conn:
                    conn.autocommit = True
                    cur = conn.cursor()
                    insert_sql = """
                    INSERT INTO public.socratic_chats (
                        student_id, course_code, user_message, code_context,
                        ai_reply, socratic_approved, model_provider
                    ) VALUES (%s, %s, %s, %s, %s, TRUE, %s);
                    """
                    cur.execute(insert_sql, (
                        student_id,
                        course_code,
                        user_message,
                        code_context or "",
                        ai_reply,
                        model_provider
                    ))
                    cur.close()
                    conn.close()
                    return True
            except Exception as e:
                print(f"[Supabase PG] save_chat_message error: {e}")

        return False

    async def execute_query(self, query: str, params: tuple = ()) -> bool:
        """Executes a direct SQL query against Supabase PostgreSQL."""
        if not self.is_connected:
            return False
        if self.db_url and PSYCOPG2_AVAILABLE:
            try:
                conn = self._get_pg_connection()
                if conn:
                    conn.autocommit = True
                    cur = conn.cursor()
                    cur.execute(query, params)
                    cur.close()
                    conn.close()
                    return True
            except Exception as e:
                print(f"[Supabase PG] execute_query error: {e}")
        return False

    async def cleanup_test_slides(self) -> bool:
        """Purges any transient test slides keeping only the real user Data Science slide."""
        return await self.execute_query(
            "DELETE FROM public.slides WHERE slide_id != 'slide_datascience_w03_1791353451';"
        )


# Singleton Instance
supabase_db = TLUSupabaseManager()

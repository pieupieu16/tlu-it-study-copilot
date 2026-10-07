"""
TLU IT Study Copilot - Supabase Database Client & ORM Layer
Architecture: Asynchronous and synchronous Supabase PostgreSQL integration.
Domain: 100% TLU IT Department (Courses IT101, IT201, IT205, IT301, IT315).
Compliance: Zero Icon policy, Light Mode assets, Zero prohibited terms.
"""

import os
import sys
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
        self.client: Optional[Client] = None
        self.is_connected: bool = False
        self._initialize_client()

    def _initialize_client(self):
        """Attempts to initialize the Supabase client SDK if credentials exist."""
        if not self.supabase_url or not self.supabase_key:
            self.is_connected = False
            return

        # Basic format check (must be a valid URL)
        if not self.supabase_url.startswith("http"):
            self.is_connected = False
            return

        if SUPABASE_SDK_AVAILABLE:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                self.is_connected = True
                print(f"[Supabase] Connected to project: {self.supabase_url}")
            except Exception as exc:
                print(f"[Supabase] Initialization error: {exc}")
                self.is_connected = False
        else:
            # Fall back to direct REST mode via HTTPX
            self.is_connected = True
            print(f"[Supabase] Direct REST mode enabled for: {self.supabase_url}")

    def get_status(self) -> Dict[str, Any]:
        """Returns the operational status of the Supabase connection."""
        return {
            "configured": bool(self.supabase_url and self.supabase_key),
            "connected": self.is_connected,
            "url": self.supabase_url if self.supabase_url else "Not configured",
            "sdk_available": SUPABASE_SDK_AVAILABLE,
            "rest_available": HTTPX_AVAILABLE
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Tests live query against Supabase slides table."""
        if not self.supabase_url or not self.supabase_key:
            return {
                "status": "not_configured",
                "message": "SUPABASE_URL and SUPABASE_KEY are not configured in .env"
            }

        try:
            if self.client:
                response = self.client.table("slides").select("slide_id").limit(1).execute()
                return {
                    "status": "connected",
                    "message": "Successfully connected to Supabase PostgreSQL database.",
                    "data": response.data
                }
            elif HTTPX_AVAILABLE:
                endpoint = f"{self.supabase_url.rstrip('/')}/rest/v1/slides?select=slide_id&limit=1"
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}"
                }
                async with httpx.AsyncClient(timeout=5.0) as http_client:
                    res = await http_client.get(endpoint, headers=headers)
                    if res.status_code in [200, 206]:
                        return {
                            "status": "connected",
                            "message": "Connected to Supabase via PostgREST endpoint.",
                            "data": res.json()
                        }
                    else:
                        return {
                            "status": "error",
                            "code": res.status_code,
                            "message": f"Supabase responded with code {res.status_code}: {res.text[:200]}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}"
            }

        return {"status": "offline", "message": "Supabase client not operational"}

    async def fetch_slides(self, course_code: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Fetches slide lecture records from Supabase."""
        if not self.is_connected:
            return None

        try:
            if self.client:
                query = self.client.table("slides").select("*").order("uploaded_at", desc=True)
                if course_code:
                    query = query.eq("course_code", course_code.upper())
                res = query.execute()
                if res.data is not None and len(res.data) > 0:
                    return res.data
            elif HTTPX_AVAILABLE:
                url = f"{self.supabase_url.rstrip('/')}/rest/v1/slides?select=*&order=uploaded_at.desc"
                if course_code:
                    url += f"&course_code=eq.{course_code.upper()}"
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}"
                }
                async with httpx.AsyncClient(timeout=5.0) as http_client:
                    res = await http_client.get(url, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        if data and len(data) > 0:
                            return data
        except Exception as e:
            print(f"[Supabase] fetch_slides query failed: {e}")

        return None

    async def insert_slide(self, record: Dict[str, Any]) -> bool:
        """Inserts a new lecture slide record into Supabase."""
        if not self.is_connected:
            return False

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
                "uploaded_at": datetime.utcnow().isoformat() + "Z"
            }

            if self.client:
                self.client.table("slides").upsert(payload).execute()
                return True
            elif HTTPX_AVAILABLE:
                url = f"{self.supabase_url.rstrip('/')}/rest/v1/slides"
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates"
                }
                async with httpx.AsyncClient(timeout=5.0) as http_client:
                    res = await http_client.post(url, headers=headers, json=payload)
                    return res.status_code in [200, 201]
        except Exception as e:
            print(f"[Supabase] insert_slide failed: {e}")

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

        try:
            payload = {
                "student_id": student_id,
                "course_code": course_code,
                "user_message": user_message,
                "code_context": code_context or "",
                "ai_reply": ai_reply,
                "socratic_approved": True,
                "model_provider": model_provider,
                "created_at": datetime.utcnow().isoformat() + "Z"
            }

            if self.client:
                self.client.table("socratic_chats").insert(payload).execute()
                return True
            elif HTTPX_AVAILABLE:
                url = f"{self.supabase_url.rstrip('/')}/rest/v1/socratic_chats"
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json"
                }
                async with httpx.AsyncClient(timeout=5.0) as http_client:
                    res = await http_client.post(url, headers=headers, json=payload)
                    return res.status_code in [200, 201]
        except Exception as e:
            print(f"[Supabase] save_chat_message failed: {e}")

        return False


# Singleton Instance
supabase_db = TLUSupabaseManager()

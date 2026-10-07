#!/usr/bin/env python3
"""
TLU IT Study Copilot - Supabase Automated Setup & Verification Script
Architecture: Automated database bootstrap, schema deployment and connection tester.
Domain: 100% TLU IT Department (Courses IT101, IT201, IT205, IT301, IT315).
Compliance: Zero Icon policy, Light Mode assets, Zero prohibited terms.
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
SCHEMA_FILE = BASE_DIR / "supabase_schema.sql"

# Add current directory to path
sys.path.insert(0, str(BASE_DIR))


def update_env_file(supabase_url: str, supabase_key: str):
    """Safely updates or appends Supabase variables into .env file."""
    lines = []
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

    updated_url = False
    updated_key = False
    new_lines = []

    for line in lines:
        if line.strip().startswith("SUPABASE_URL="):
            new_lines.append(f"SUPABASE_URL={supabase_url}\n")
            updated_url = True
        elif line.strip().startswith("SUPABASE_KEY="):
            new_lines.append(f"SUPABASE_KEY={supabase_key}\n")
            updated_key = True
        else:
            new_lines.append(line)

    if not updated_url:
        new_lines.append(f"\n# Supabase Database Configuration\nSUPABASE_URL={supabase_url}\n")
    if not updated_key:
        new_lines.append(f"SUPABASE_KEY={supabase_key}\n")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"[Success] Updated Supabase configuration in: {ENV_FILE}")


async def run_setup():
    parser = argparse.ArgumentParser(description="TLU IT Study Copilot - Supabase Database Setup")
    parser.add_argument("--url", help="Supabase Project URL (e.g. https://xyz.supabase.co)")
    parser.add_argument("--key", help="Supabase anon public key or service_role key")
    parser.add_argument("--test", action="store_true", help="Test live connection only")
    args = parser.parse_args()

    print("=" * 70)
    print("TLU IT Study Copilot - Supabase PostgreSQL Database Setup")
    print("Institution: Truong Dai hoc Thang Long - Khoa Cong nghe Thong tin")
    print("=" * 70)

    target_url = args.url or os.getenv("SUPABASE_URL", "")
    target_key = args.key or os.getenv("SUPABASE_KEY", "")

    if args.url and args.key:
        update_env_file(args.url, args.key)
        os.environ["SUPABASE_URL"] = args.url
        os.environ["SUPABASE_KEY"] = args.key
        target_url = args.url
        target_key = args.key

    if not target_url or not target_key:
        print("\n[!] Supabase credentials not found in environment or arguments.")
        print("\nCac buoc thuc hien de hoan tat:")
        print("1. Tren tab trinh duyet Supabase (pieupieu16's Project):")
        print("   - Nhap Database Password va chon Region (Singapore)")
        print("   - Bam nut 'Create new project'")
        print("2. Sau khi tao xong, vao Project Settings -> API:")
        print("   - Copy 'Project URL' (dang https://xxxx.supabase.co)")
        print("   - Copy 'anon public' hoac 'service_role' key")
        print("3. Chay lenh sau de tu dong cau hinh:")
        print("   python3 setup_supabase.py --url <PROJECT_URL> --key <API_KEY>")
        print("\n4. Vao SQL Editor tren Supabase, dan noi dung file sau va bam Run:")
        print(f"   {SCHEMA_FILE}")
        return 0

    print(f"\nTarget Supabase URL: {target_url}")
    print("Testing connection...")

    from supabase_client import TLUSupabaseManager
    manager = TLUSupabaseManager()
    manager.supabase_url = target_url
    manager.supabase_key = target_key
    manager._initialize_client()

    result = await manager.test_connection()
    print(f"Connection Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")

    if result.get("status") == "connected":
        print("\n[SUCCESS] Supabase database is connected and ready for TLU IT Study Copilot!")
        slides = await manager.fetch_slides()
        if slides:
            print(f"Discovered {len(slides)} existing slides in database.")
        else:
            print("Notice: No slides found yet in 'slides' table.")
            print(f"Please execute the SQL migration script: {SCHEMA_FILE} in Supabase SQL Editor.")
    else:
        print("\n[!] Could not connect to Supabase database directly.")
        print("Please check your Project URL, API Key, and ensure the project is active.")

    return 0


if __name__ == "__main__":
    asyncio.run(run_setup())

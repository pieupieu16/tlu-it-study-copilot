"""
TLU IT Study Copilot - Concurrency & Event Loop Benchmark (Milestone M2 & R2 Verification)
Verifies:
1. Event Loop latency remains < 50ms while AI Advisor LLM tasks run in parallel.
2. HTTP ping response latency remains < 200ms under concurrent AI Advisor workload.
3. Zero dropped connections, zero deadlocks, and zero unhandled exceptions.
"""

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List
import requests
import uvicorn
import threading

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from classroom.concurrency import get_event_loop_lag_monitor, run_in_advisor_pool
from classroom.database import SessionLocal, Base, engine
from classroom.models import Session, User, Room, Course, Participant, LearningEvent
from classroom.security import create_token

BENCHMARK_HOST = "127.0.0.1"
BENCHMARK_PORT = 19992
BASE_URL = f"http://{BENCHMARK_HOST}:{BENCHMARK_PORT}"


class EphemeralBenchmarkServer:
    def __init__(self, host: str = BENCHMARK_HOST, port: int = BENCHMARK_PORT):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.started_event = threading.Event()

    def start(self):
        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="error",
            loop="asyncio",
        )
        self.server = uvicorn.Server(config)

        def _run():
            self.started_event.set()
            self.server.run()

        self.thread = threading.Thread(target=_run, daemon=True)
        self.thread.start()
        self.started_event.wait(timeout=5.0)
        time.sleep(1.2)

    def stop(self):
        if self.server:
            self.server.should_exit = True
        if self.thread:
            self.thread.join(timeout=3.0)


def setup_benchmark_data():
    with SessionLocal() as db:
        user = db.query(User).filter_by(email="benchmark_test@tlu.edu.vn").first()
        if not user:
            user = User(email="benchmark_test@tlu.edu.vn", password_hash="hash_bench", full_name="Giang Vien Benchmark")
            db.add(user)
            db.commit()
            db.refresh(user)

        course = db.query(Course).filter_by(owner_id=user.id).first()
        if not course:
            course = Course(title="Tin hoc dai cuong TLU", description="Lap trinh C/C++ co ban", owner_id=user.id)
            db.add(course)
            db.commit()
            db.refresh(course)

        room = db.query(Room).filter_by(code="BENCH_01").first()
        if not room:
            room = Room(code="BENCH_01", name="Phong Hoc Benchmark", course_id=course.id, owner_id=user.id)
            db.add(room)
            db.commit()
            db.refresh(room)

        session = db.query(Session).filter_by(room_id=room.id, ended_at=None).first()
        if not session:
            session = Session(room_id=room.id, current_slide_index=0)
            db.add(session)
            db.commit()
            db.refresh(session)

        token = create_token(user)
        return session.id, token


def run_benchmark():
    print("=" * 70)
    print("  TLU IT STUDY COPILOT - CONCURRENCY & EVENT LOOP AUDIT BENCHMARK")
    print("=" * 70)

    server = EphemeralBenchmarkServer()
    server.start()
    session_id, jwt_token = setup_benchmark_data()
    print(f"[Benchmark Setup] Seeded Session ID={session_id}, Server running at {BASE_URL}")

    monitor = get_event_loop_lag_monitor()
    monitor.start(reset=True)

    headers = {"Authorization": f"Bearer {jwt_token}"}
    advice_url = f"{BASE_URL}/api/teaching/sessions/{session_id}/advice"
    health_url = f"{BASE_URL}/api/health"
    lag_url = f"{BASE_URL}/api/health/lag"

    # Concurrency Test Parameters
    num_ai_calls = 12
    num_pings = 60
    ai_latencies: List[float] = []
    ping_latencies: List[float] = []
    errors: List[str] = []

    print(f"\n[Phase 1] Launching {num_ai_calls} concurrent AI Advisor inference tasks...")
    print(f"[Phase 2] Simulating {num_pings} parallel HTTP pings to measure Event Loop latency...")

    def call_ai_advisor(idx: int):
        s = requests.Session()
        t0 = time.perf_counter()
        try:
            resp = s.post(advice_url, headers=headers, json={"prompt": f"Benchmark request {idx}", "slide_index": 0}, timeout=10.0)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if resp.status_code == 200:
                ai_latencies.append(elapsed_ms)
            else:
                errors.append(f"AI call {idx} returned {resp.status_code}: {resp.text}")
        except Exception as e:
            errors.append(f"AI call {idx} error: {e}")

    def call_http_ping(idx: int):
        s = requests.Session()
        target = health_url if idx % 2 == 0 else lag_url
        t0 = time.perf_counter()
        try:
            resp = s.get(target, timeout=5.0)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if resp.status_code == 200:
                ping_latencies.append(elapsed_ms)
            else:
                errors.append(f"Ping {idx} returned {resp.status_code}")
        except Exception as e:
            errors.append(f"Ping {idx} error: {e}")

    threads = []
    # Launch AI threads
    for i in range(num_ai_calls):
        t = threading.Thread(target=call_ai_advisor, args=(i,))
        threads.append(t)
        t.start()

    time.sleep(0.05)

    # Launch Ping threads while AI is actively running
    for j in range(num_pings):
        t = threading.Thread(target=call_http_ping, args=(j,))
        threads.append(t)
        t.start()
        time.sleep(0.02)

    # Await all threads
    for t in threads:
        t.join(timeout=15.0)

    # Fetch Event Loop Lag statistics from live server
    lag_stats_resp = requests.get(lag_url, timeout=3.0)
    lag_stats = lag_stats_resp.json() if lag_stats_resp.status_code == 200 else {}

    server.stop()
    print("[Teardown] Benchmark server stopped.\n")

    # Metrics calculation
    ping_latencies.sort()
    p50_ping = ping_latencies[int(len(ping_latencies) * 0.50)] if ping_latencies else 0.0
    p95_ping = ping_latencies[int(len(ping_latencies) * 0.95)] if ping_latencies else 0.0
    p99_ping = ping_latencies[min(int(len(ping_latencies) * 0.99), len(ping_latencies) - 1)] if ping_latencies else 0.0

    p99_lag = lag_stats.get("p99_lag_ms", 0.0)
    current_lag = lag_stats.get("current_lag_ms", 0.0)
    max_lag = lag_stats.get("max_lag_ms", 0.0)

    print("-" * 70)
    print("  BENCHMARK AUDIT RESULTS")
    print("-" * 70)
    print(f"  AI Advisor Tasks Succeeded : {len(ai_latencies)} / {num_ai_calls}")
    print(f"  HTTP Pings Succeeded       : {len(ping_latencies)} / {num_pings}")
    print(f"  HTTP Ping Latency p50      : {p50_ping:.2f} ms")
    print(f"  HTTP Ping Latency p95      : {p95_ping:.2f} ms")
    print(f"  HTTP Ping Latency p99      : {p99_ping:.2f} ms  (Target: < 200 ms)")
    print(f"  Event Loop Current Lag     : {current_lag:.2f} ms")
    print(f"  Event Loop p99 Lag         : {p99_lag:.2f} ms  (Target: < 50 ms)")
    print(f"  Event Loop Max Lag         : {max_lag:.2f} ms")
    print(f"  Total Errors Encountered   : {len(errors)}")
    print("-" * 70)

    # Verification Gates
    gate_lag = p99_lag < 50.0
    gate_ping = p99_ping < 200.0
    gate_success = (len(errors) == 0) and (len(ai_latencies) == num_ai_calls) and (len(ping_latencies) == num_pings)

    overall_pass = gate_lag and gate_ping and gate_success
    result_str = "PASS" if overall_pass else "FAIL"

    print(f"  Gate 1 (Event Loop Lag < 50ms)   : {'[PASS]' if gate_lag else '[FAIL]'}")
    print(f"  Gate 2 (HTTP Ping Latency < 200ms): {'[PASS]' if gate_ping else '[FAIL]'}")
    print(f"  Gate 3 (Zero Error & 100% Delivery): {'[PASS]' if gate_success else '[FAIL]'}")
    print(f"  OVERALL AUDIT VERDICT            : {result_str}")
    print("=" * 70)

    report_payload = {
        "verdict": result_str,
        "metrics": {
            "p99_lag_ms": p99_lag,
            "max_lag_ms": max_lag,
            "p99_ping_ms": p99_ping,
            "ai_tasks_completed": len(ai_latencies),
            "pings_completed": len(ping_latencies),
            "errors": errors,
        },
    }
    with open("benchmark_results.json", "w") as f:
        json.dump(report_payload, f, indent=2)

    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(run_benchmark())

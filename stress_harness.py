"""
TLU IT Study Copilot - Empirical Concurrency & Stress Verification Harness
Challenger M1_2 Stress Harness for Milestone M1 Integration

Evaluates:
1. Concurrently hammering REST endpoints and Socket.IO connections.
2. Lack of memory leaks, socket drops, or thread deadlocks.
3. Event loop lag and HTTP ping latency under concurrent heavy load.
4. Database concurrency safety and state tracking integrity.
"""

import asyncio
import gc
import json
import os
import resource
import sys
import threading
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

import requests
import uvicorn

# Import target system components
from app import app, fastapi_app
from classroom.concurrency import get_event_loop_lag_monitor, run_in_advisor_pool
from classroom.realtime import sio, tracking
from classroom.security import create_token
from classroom.database import SessionLocal, Base, engine
from classroom.models import Session, User, Room, Course, Slide, Participant, LearningEvent


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 19991
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"


class StressTestReport:
    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.passed: bool = True
        self.failures: List[str] = []

    def record(self, test_name: str, status: bool, metrics: Dict[str, Any], notes: str = ""):
        self.results[test_name] = {
            "status": "PASS" if status else "FAIL",
            "metrics": metrics,
            "notes": notes,
        }
        if not status:
            self.passed = False
            self.failures.append(f"{test_name}: {notes}")


report = StressTestReport()


def seed_test_database():
    """Ensure database has valid test data for sessions and participants."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = db.query(User).filter_by(email="challenger_test@tlu.edu.vn").first()
        if not user:
            user = User(
                email="challenger_test@tlu.edu.vn",
                password_hash="challenger_test_hash",
                full_name="Challenger Tester",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        course = db.query(Course).filter_by(owner_id=user.id).first()
        if not course:
            course = Course(
                title="Challenger Test Course IT101",
                description="Concurrency Verification Course",
                owner_id=user.id,
            )
            db.add(course)
            db.commit()
            db.refresh(course)

        slides = db.query(Slide).filter_by(course_id=course.id).all()
        if not slides:
            for idx in range(10):
                slide = Slide(
                    course_id=course.id,
                    index=idx,
                    title=f"Slide {idx}: Concurrency Test",
                    blocks=[],
                )
                db.add(slide)
            db.commit()

        room = db.query(Room).filter_by(code="CHALL_01").first()
        if not room:
            room = Room(
                code="CHALL_01",
                name="Challenger Room",
                course_id=course.id,
                owner_id=user.id,
            )
            db.add(room)
            db.commit()
            db.refresh(room)

        session = db.query(Session).filter_by(room_id=room.id, ended_at=None).first()
        if not session:
            session = Session(
                room_id=room.id,
                current_slide_index=0,
            )
            db.add(session)
            db.commit()
            db.refresh(session)

        # Seed 100 participants for high concurrency simulation
        existing_count = db.query(Participant).filter_by(session_id=session.id).count()
        if existing_count < 100:
            for p_idx in range(existing_count, 100):
                participant = Participant(
                    session_id=session.id,
                    display_name=f"Student Challenger {p_idx}",
                    token=f"challenger_token_{p_idx}",
                    online=True,
                )
                db.add(participant)
            db.commit()

        jwt_token = create_token(user)
        student = db.query(Participant).filter_by(session_id=session.id).first()
        student_token = student.token

        return session.id, user.id, room.id, jwt_token, student_token


class EphemeralServer:
    def __init__(self, host: str = SERVER_HOST, port: int = SERVER_PORT):
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
        time.sleep(1.0)

    def stop(self):
        if self.server:
            self.server.should_exit = True
        if self.thread:
            self.thread.join(timeout=3.0)


# ============================================================================
# STRESS TEST 1: REST Endpoints Hammering (Burst & High Concurrency)
# ============================================================================
def stress_test_rest_endpoints(session_id: int, room_id: int, jwt_token: str, student_token: str):
    print("\n[STRESS 1] Hammering REST Endpoints with High Concurrency...")
    headers = {"Authorization": f"Bearer {jwt_token}"}
    endpoints = [
        ("GET", f"{BASE_URL}/api/health", None, None),
        ("GET", f"{BASE_URL}/api/health/lag", None, None),
        ("GET", f"{BASE_URL}/api/courses", None, None),
        ("GET", f"{BASE_URL}/api/admin/logs", None, None),
        ("GET", f"{BASE_URL}/api/admin/finops", None, None),
        ("GET", f"{BASE_URL}/api/sessions/rooms", None, headers),
        ("GET", f"{BASE_URL}/api/sessions/sessions/{session_id}", None, headers),
        ("GET", f"{BASE_URL}/api/analytics/sessions/{session_id}/summary", None, headers),
        ("GET", f"{BASE_URL}/api/teaching/sessions/{session_id}/dashboard", None, headers),
        ("GET", f"{BASE_URL}/api/teaching/sessions/{session_id}/slide-tracking", None, headers),
        ("GET", f"{BASE_URL}/api/student/sessions/{session_id}/state?token={student_token}", None, None),
    ]

    total_requests = 1000
    concurrent_workers = 30
    latencies: List[float] = []
    status_codes: Dict[int, int] = {}
    errors: List[str] = []

    import threading
    _thread_local = threading.local()

    def get_session():
        if not hasattr(_thread_local, "session"):
            _thread_local.session = requests.Session()
        return _thread_local.session

    def make_request(idx: int):
        method, url, payload, req_headers = endpoints[idx % len(endpoints)]
        session = get_session()
        start = time.perf_counter()
        try:
            if method == "GET":
                resp = session.get(url, headers=req_headers, timeout=3.0)
            else:
                resp = session.post(url, json=payload, headers=req_headers, timeout=3.0)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return resp.status_code, elapsed_ms, None
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return 0, elapsed_ms, str(e)

    start_total = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrent_workers) as pool:
        futures = [pool.submit(make_request, i) for i in range(total_requests)]
        for f in as_completed(futures):
            code, lat, err = f.result()
            latencies.append(lat)
            status_codes[code] = status_codes.get(code, 0) + 1
            if err:
                errors.append(err)

    total_time_s = time.perf_counter() - start_total
    rps = total_requests / total_time_s
    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[min(int(len(latencies) * 0.99), len(latencies) - 1)]
    max_lat = latencies[-1]
    success_count = sum(cnt for code, cnt in status_codes.items() if 200 <= code < 400)
    success_rate = (success_count / total_requests) * 100.0

    metrics = {
        "total_requests": total_requests,
        "concurrent_workers": concurrent_workers,
        "throughput_rps": round(rps, 2),
        "success_rate_percent": round(success_rate, 2),
        "status_distribution": status_codes,
        "latency_p50_ms": round(p50, 2),
        "latency_p95_ms": round(p95, 2),
        "latency_p99_ms": round(p99, 2),
        "latency_max_ms": round(max_lat, 2),
        "error_count": len(errors),
    }
    print(f"  Results: {total_requests} reqs in {total_time_s:.2f}s ({rps:.1f} RPS)")
    print(f"  Success: {success_rate:.1f}%, Statuses: {status_codes}")
    print(f"  Latency: p50={p50:.1f}ms, p95={p95:.1f}ms, p99={p99:.1f}ms, max={max_lat:.1f}ms")

    passed = (success_rate >= 99.0) and (p99 < 150.0) and (len(errors) == 0)
    report.record("REST_Hammering_Concurrency", passed, metrics, f"RPS: {rps:.1f}, p99: {p99:.1f}ms, Errors: {len(errors)}")


# ============================================================================
# STRESS TEST 2: Concurrent Socket.IO Connection & Protocol Hammering
# ============================================================================
def stress_test_socketio_concurrency(session_id: int):
    print("\n[STRESS 2] Hammering Socket.IO Connection Paths with 50 Concurrent Clients...")
    import socketio

    client_count = 50
    events_per_client = 3
    successful_connections = 0
    successful_joins = 0
    successful_slides = 0
    dropped_sockets = 0
    errors: List[str] = []
    latencies: List[float] = []

    def simulate_student_client(client_idx: int):
        nonlocal successful_connections, successful_joins, successful_slides, dropped_sockets
        sio_client = socketio.Client(reconnection=False)
        received_joined = threading.Event()
        received_update = threading.Event()

        @sio_client.on("joined")
        def on_joined(data):
            received_joined.set()

        @sio_client.on("slide_tracking_updated")
        def on_slide_updated(data):
            received_update.set()

        t0 = time.perf_counter()
        try:
            sio_client.connect(BASE_URL, socketio_path="socket.io", transports=["polling"])
            successful_connections += 1

            token = f"challenger_token_{client_idx}"
            sio_client.emit("join_session", {
                "session_id": session_id,
                "role": "student",
                "token": token,
                "slide_index": 0,
                "following": True,
            })
            if received_joined.wait(timeout=3.0):
                successful_joins += 1

            for slide_num in range(1, events_per_client + 1):
                received_update.clear()
                sio_client.emit("student_slide_changed", {
                    "session_id": session_id,
                    "slide_index": slide_num % 5,
                    "following": False,
                })
                if received_update.wait(timeout=2.0):
                    successful_slides += 1

            sio_client.emit("leave_session", {})
            time.sleep(0.01)
            sio_client.eio.disconnect(abort=True)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(elapsed_ms)
        except Exception as e:
            dropped_sockets += 1
            errors.append(f"Client {client_idx} failure: {e}")
            try:
                sio_client.eio.disconnect(abort=True)
            except Exception:
                pass

    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=25) as pool:
        futures = [pool.submit(simulate_student_client, i) for i in range(client_count)]
        for f in as_completed(futures):
            f.result()
    total_time_s = time.perf_counter() - t_start

    metrics = {
        "clients_simulated": client_count,
        "successful_connections": successful_connections,
        "successful_joins": successful_joins,
        "slide_updates_acknowledged": successful_slides,
        "dropped_sockets": dropped_sockets,
        "total_duration_s": round(total_time_s, 2),
        "errors": errors[:5],
    }
    print(f"  Connected: {successful_connections}/{client_count}")
    print(f"  Joined: {successful_joins}/{client_count}")
    print(f"  Slide updates acknowledged: {successful_slides}/{client_count * events_per_client}")
    print(f"  Dropped sockets: {dropped_sockets}")

    passed = (successful_connections == client_count) and (dropped_sockets == 0) and (successful_joins >= client_count * 0.95)
    report.record("SocketIO_Concurrent_Hammering", passed, metrics, f"Connected: {successful_connections}/{client_count}, Dropped: {dropped_sockets}")


# ============================================================================
# STRESS TEST 3: Memory Leak & Orphan Resource Detection
# ============================================================================
def stress_test_memory_leaks(session_id: int):
    print("\n[STRESS 3] Analyzing Memory Profile and Resource Retention...")
    
    async def run_memory_cycles():
        tracemalloc.start()
        gc.collect()
        snap1 = tracemalloc.take_snapshot()
        initial_rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        cycles = 500
        for i in range(cycles):
            sid = f"stress_socket_{i}"
            pid = (i % 50) + 1
            await tracking.track_student(
                participant_id=pid,
                session_id=session_id,
                slide_index=i % 10,
                following_lecturer=False,
                lecturer_slide_index=0,
                socket_id=sid,
            )
            await tracking.detach_socket(sid)

        gc.collect()
        snap2 = tracemalloc.take_snapshot()
        final_rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        tracemalloc.stop()

        top_stats = snap2.compare_to(snap1, "lineno")
        total_diff_kb = sum(stat.size_diff for stat in top_stats) / 1024.0

        active_states = len(tracking._states)
        active_tasks = len(tracking._tasks)
        lag_history_len = len(get_event_loop_lag_monitor().history)

        return {
            "cycles": cycles,
            "initial_rss_kb": initial_rss_kb,
            "final_rss_kb": final_rss_kb,
            "rss_delta_kb": final_rss_kb - initial_rss_kb,
            "tracemalloc_diff_kb": round(total_diff_kb, 2),
            "lingering_tracking_states": active_states,
            "lingering_tracking_tasks": active_tasks,
            "lag_monitor_history_size": lag_history_len,
        }

    metrics = asyncio.run(run_memory_cycles())
    print(f"  Cycles: {metrics['cycles']}")
    print(f"  Memory Diff (tracemalloc): {metrics['tracemalloc_diff_kb']} KB")
    print(f"  RSS Delta: {metrics['rss_delta_kb']} KB")
    print(f"  Lingering tracking states: {metrics['lingering_tracking_states']}")
    print(f"  Lingering tracking tasks: {metrics['lingering_tracking_tasks']}")

    passed = (metrics["lingering_tracking_states"] == 0) and (metrics["tracemalloc_diff_kb"] < 2000.0)
    report.record("Memory_Leak_Resource_Retention", passed, metrics, f"Diff: {metrics['tracemalloc_diff_kb']} KB, Lingering states: {metrics['lingering_tracking_states']}")


# ============================================================================
# STRESS TEST 4: Thread Deadlocks, Database Locks, and Event Loop Lag Under Realistic AI Load
# ============================================================================
def stress_test_thread_deadlocks_and_event_loop(session_id: int):
    print("\n[STRESS 4] Testing Thread Deadlocks, SQLite Concurrent Writes, and Event Loop Latency...")
    
    # Realistic advisor offloaded task: IO simulation (sleeping releases GIL) + SQLite DB transaction
    def realistic_advisor_task(task_id: int):
        # Simulate network LLM latency (releases GIL)
        time.sleep(0.05)
        with SessionLocal() as db:
            audit = LearningEvent(
                session_id=session_id,
                participant_id=None,
                slide_index=0,
                type="advisor_simulation_audit",
                payload={"task_id": task_id, "status": "computed"},
            )
            db.add(audit)
            db.commit()
        return task_id

    async def async_stress_runner():
        lag_monitor = get_event_loop_lag_monitor()
        lag_monitor.start(reset=True)

        # Saturate 16 worker threads concurrently
        tasks = [run_in_advisor_pool(realistic_advisor_task, i) for i in range(16)]

        # Concurrently perform event loop pings
        ping_latencies: List[float] = []
        for _ in range(25):
            t0 = time.perf_counter()
            await asyncio.sleep(0.01)
            ping_latencies.append((time.perf_counter() - t0) * 1000.0)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        stats = lag_monitor.get_stats()
        return results, ping_latencies, stats

    loop_results, ping_lats, lag_stats = asyncio.run(async_stress_runner())
    exceptions = [r for r in loop_results if isinstance(r, Exception)]

    p99_lag = lag_stats.get("p99_lag_ms", 0.0)
    current_lag = lag_stats.get("current_lag_ms", 0.0)
    max_lag = lag_stats.get("max_lag_ms", 0.0)
    avg_ping = sum(ping_lats) / len(ping_lats) if ping_lats else 0.0

    metrics = {
        "tasks_executed": len(loop_results),
        "exceptions_encountered": len(exceptions),
        "event_loop_current_lag_ms": current_lag,
        "event_loop_p99_lag_ms": p99_lag,
        "event_loop_max_lag_ms": max_lag,
        "asyncio_sleep_avg_ms": round(avg_ping, 2),
    }
    print(f"  Advisor tasks completed: {len(loop_results) - len(exceptions)}/16 (Exceptions: {len(exceptions)})")
    print(f"  Event loop lag: current={current_lag}ms, p99={p99_lag}ms, max={max_lag}ms")
    print(f"  Async sleep latency avg: {avg_ping:.2f}ms")

    passed = (len(exceptions) == 0) and (p99_lag < 50.0)
    report.record("Deadlock_And_EventLoop_Lag", passed, metrics, f"Exceptions: {len(exceptions)}, p99 lag: {p99_lag}ms")


# ============================================================================
# Main Stress Execution Runner
# ============================================================================
def main():
    print("=" * 80)
    print("  TLU STUDY ASSISTANT - EMPIRICAL STRESS TEST SUITE (CHALLENGER M1_2)")
    print("=" * 80)

    session_id, user_id, room_id, jwt_token, student_token = seed_test_database()
    print(f"[Setup] Seeded session_id={session_id}, user_id={user_id}, room_id={room_id}")

    server = EphemeralServer(SERVER_HOST, SERVER_PORT)
    server.start()
    print(f"[Setup] Ephemeral server running at {BASE_URL}")

    try:
        stress_test_rest_endpoints(session_id, room_id, jwt_token, student_token)
        stress_test_socketio_concurrency(session_id)
        stress_test_memory_leaks(session_id)
        stress_test_thread_deadlocks_and_event_loop(session_id)
    finally:
        print("\n[Teardown] Shutting down ephemeral server...")
        server.stop()
        print("[Teardown] Ephemeral server stopped.")

    print("\n" + "=" * 80)
    print("  STRESS TEST SUMMARY")
    print("=" * 80)
    for test, res in report.results.items():
        print(f"  [{res['status']}] {test}: {res['notes']}")
    print(f"\nFinal Verdict: {'PASS' if report.passed else 'FAIL'}")
    print("=" * 80)

    report_file = os.path.join(
        os.path.dirname(__file__),
        "stress_results.json"
    )
    with open(report_file, "w") as f:
        json.dump(report.results, f, indent=2)
    print(f"Results dumped to {report_file}")

    if not report.passed:
        sys.exit(1)


if __name__ == "__main__":
    main()

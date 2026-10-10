"""Concurrency architecture: Dedicated ThreadPoolExecutor & Event Loop Lag Monitor.

Target module: tlu_study_assistant_web.classroom.concurrency
"""
from __future__ import annotations

import asyncio
from collections import deque
import concurrent.futures
import functools
import logging
import os
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

ADVISOR_MAX_WORKERS = int(os.getenv("ADVISOR_MAX_WORKERS", "16"))


class AdvisorThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor):
    """Dedicated ThreadPoolExecutor for AI Advisor and heavy CPU/IO tasks."""

    def __init__(self, max_workers: int = ADVISOR_MAX_WORKERS):
        super().__init__(max_workers=max_workers, thread_name_prefix="advisor_worker")


# Singleton instance configured with 16 workers
advisor_executor = AdvisorThreadPoolExecutor(max_workers=ADVISOR_MAX_WORKERS)


async def run_in_advisor_pool(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Execute a heavy blocking synchronous callable in the dedicated advisor thread pool."""
    loop = asyncio.get_running_loop()
    if kwargs:
        target = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(advisor_executor, target)
    return await loop.run_in_executor(advisor_executor, func, *args)


class EventLoopLagMonitor:
    """Continuously probes the asyncio event loop for tick drift / latency."""

    def __init__(self, check_interval_ms: float = 10.0, history_size: int = 1000):
        self.interval = check_interval_ms / 1000.0
        self.history: deque[float] = deque(maxlen=history_size)
        self.running: bool = False
        self._task: asyncio.Task | None = None

    async def _monitor_loop(self):
        while self.running:
            start = time.perf_counter()
            await asyncio.sleep(self.interval)
            elapsed = time.perf_counter() - start
            lag_ms = max(0.0, (elapsed - self.interval) * 1000.0)
            self.history.append(lag_ms)

    def clear(self):
        self.history.clear()

    def start(self, reset: bool = False):
        if reset:
            self.history.clear()
        if not self.running:
            self.running = True
            try:
                self._task = asyncio.create_task(self._monitor_loop())
            except RuntimeError:
                pass

    def stop(self):
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()

    def get_stats(self) -> dict[str, Any]:
        if not self.history:
            return {
                "status": "ok",
                "current_lag_ms": 0.0,
                "p50_lag_ms": 0.0,
                "p95_lag_ms": 0.0,
                "p99_lag_ms": 0.0,
                "max_lag_ms": 0.0,
                "samples": 0,
            }
        sorted_history = sorted(self.history)
        n = len(sorted_history)
        return {
            "status": "ok",
            "current_lag_ms": round(self.history[-1], 2),
            "p50_lag_ms": round(sorted_history[int(n * 0.50)], 2),
            "p95_lag_ms": round(sorted_history[int(n * 0.95)], 2),
            "p99_lag_ms": round(sorted_history[min(int(n * 0.99), n - 1)], 2),
            "max_lag_ms": round(sorted_history[-1], 2),
            "samples": n,
        }

    def get_metrics(self) -> dict[str, Any]:
        return self.get_stats()


_global_monitor: EventLoopLagMonitor | None = None


def get_event_loop_lag_monitor() -> EventLoopLagMonitor:
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = EventLoopLagMonitor()
    return _global_monitor

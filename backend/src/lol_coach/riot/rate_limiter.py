"""In-process token-bucket rate limiter for Riot API.

Riot enforces multiple windows: app-level (e.g. 20/1s, 100/120s) and per-method
limits. This module models each window as a single bucket; `acquire()` blocks
until all buckets have capacity for a unit of work.

We don't track method limits here yet — the app limit is the binding constraint
for low-volume use. The DESIGN doc upgrades this to a Redis-backed limiter when
we move beyond a single process.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Self


@dataclass
class Window:
    capacity: int
    period_sec: float
    _events: deque[float] = field(default_factory=deque)

    def _purge(self, now: float) -> None:
        cutoff = now - self.period_sec
        while self._events and self._events[0] <= cutoff:
            self._events.popleft()

    def wait_seconds(self, now: float) -> float:
        self._purge(now)
        if len(self._events) < self.capacity:
            return 0.0
        # earliest event leaves the window at events[0] + period
        return max(0.0, self._events[0] + self.period_sec - now)

    def record(self, now: float) -> None:
        self._events.append(now)


class TokenBucketRateLimiter:
    """Async rate limiter combining multiple time windows.

    Usage:
        limiter = TokenBucketRateLimiter([(20, 1.0), (100, 120.0)])
        await limiter.acquire()
        # ... make request ...
    """

    def __init__(self, windows: list[tuple[int, float]]) -> None:
        self._windows = [Window(capacity=c, period_sec=p) for c, p in windows]
        self._lock = asyncio.Lock()

    @classmethod
    def riot_default(cls) -> Self:
        """Riot development key defaults: 20/1s, 100/2min."""
        return cls([(20, 1.0), (100, 120.0)])

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                wait = max(w.wait_seconds(now) for w in self._windows)
                if wait <= 0:
                    for w in self._windows:
                        w.record(now)
                    return
                await asyncio.sleep(wait)

"""Rate limiter tests use a fake clock injected via monkeypatching time.monotonic
inside the module under test. asyncio.sleep is also patched to advance the clock
deterministically instead of waiting for real time.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest

from lol_coach.riot import rate_limiter as rl

# Capture the real asyncio.sleep before any module-level patching
_real_sleep = asyncio.sleep


class FakeClock:
    def __init__(self) -> None:
        self.now: float = 1000.0

    def monotonic(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.now += seconds
        await _real_sleep(0)


@pytest.fixture
async def clock(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[FakeClock]:
    fake = FakeClock()
    monkeypatch.setattr(rl.time, "monotonic", fake.monotonic)
    monkeypatch.setattr(rl.asyncio, "sleep", fake.sleep)
    yield fake


async def test_single_window_allows_up_to_capacity(clock: FakeClock) -> None:
    limiter = rl.TokenBucketRateLimiter([(3, 1.0)])
    for _ in range(3):
        await limiter.acquire()
    # all three should have been instant
    assert clock.now == 1000.0


async def test_single_window_blocks_at_capacity(clock: FakeClock) -> None:
    limiter = rl.TokenBucketRateLimiter([(3, 1.0)])
    for _ in range(3):
        await limiter.acquire()
    await limiter.acquire()
    # fourth call had to wait ~1s
    assert clock.now == pytest.approx(1001.0, abs=1e-6)


async def test_multiple_windows_take_max_wait(clock: FakeClock) -> None:
    # tight 1s window + larger 10s window — both must be satisfied
    limiter = rl.TokenBucketRateLimiter([(2, 1.0), (5, 10.0)])
    for _ in range(5):
        await limiter.acquire()
    # 5 calls under 2/1s + 5/10s. After 2 calls @1000, must wait 1s; pattern continues.
    # Final time = 1000 + 1 + 1 = 1002 (after 5th call) — but the 10s window now full
    assert clock.now >= 1002.0
    await limiter.acquire()
    # 6th call should be bounded by the 10s window
    assert clock.now >= 1010.0


async def test_riot_default_factory() -> None:
    limiter = rl.TokenBucketRateLimiter.riot_default()
    # Just ensure no exception and two windows configured
    assert len(limiter._windows) == 2

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
import respx

from lol_coach.riot.client import AsyncRiotClient
from lol_coach.riot.errors import (
    NotFoundError,
    RateLimitError,
    ServerError,
    UnauthorizedError,
)
from lol_coach.riot.rate_limiter import TokenBucketRateLimiter


@pytest.fixture
async def client() -> AsyncIterator[AsyncRiotClient]:
    # Use a generous rate limiter so tests aren't slowed by limits
    limiter = TokenBucketRateLimiter([(1000, 1.0)])
    async with AsyncRiotClient(api_key="test-key", rate_limiter=limiter) as c:
        yield c


async def test_get_success_sends_api_key_header(client: AsyncRiotClient) -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get("https://jp1.api.riotgames.com/foo").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        result = await client.get("jp1", "/foo")
        assert result == {"ok": True}
        sent = route.calls.last.request
        assert sent.headers["x-riot-token"] == "test-key"


async def test_get_401_raises_unauthorized(client: AsyncRiotClient) -> None:
    with respx.mock() as mock:
        mock.get("https://jp1.api.riotgames.com/foo").mock(
            return_value=httpx.Response(401, json={"status": {"message": "no"}})
        )
        with pytest.raises(UnauthorizedError) as exc:
            await client.get("jp1", "/foo")
        assert exc.value.status_code == 401


async def test_get_404_raises_not_found(client: AsyncRiotClient) -> None:
    with respx.mock() as mock:
        mock.get("https://asia.api.riotgames.com/x").mock(return_value=httpx.Response(404))
        with pytest.raises(NotFoundError):
            await client.get("asia", "/x")


async def test_get_500_retries_then_succeeds(client: AsyncRiotClient) -> None:
    with respx.mock() as mock:
        mock.get("https://jp1.api.riotgames.com/foo").mock(
            side_effect=[
                httpx.Response(500),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        result = await client.get("jp1", "/foo")
        assert result == {"ok": True}


async def test_get_500_exhausts_retries_raises_server_error(client: AsyncRiotClient) -> None:
    # max_retries=3, so 4 total attempts; mock all of them
    with respx.mock() as mock:
        mock.get("https://jp1.api.riotgames.com/foo").mock(return_value=httpx.Response(503))
        with pytest.raises(ServerError):
            await client.get("jp1", "/foo")


async def test_429_retries_with_retry_after_header(client: AsyncRiotClient) -> None:
    with respx.mock() as mock:
        mock.get("https://jp1.api.riotgames.com/foo").mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": "0"}),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        result = await client.get("jp1", "/foo")
        assert result == {"ok": True}


async def test_429_exhausts_retries_raises_rate_limit_error(client: AsyncRiotClient) -> None:
    with respx.mock() as mock:
        mock.get("https://jp1.api.riotgames.com/foo").mock(
            return_value=httpx.Response(429, headers={"Retry-After": "0"})
        )
        with pytest.raises(RateLimitError):
            await client.get("jp1", "/foo")


async def test_query_params_are_passed(client: AsyncRiotClient) -> None:
    with respx.mock() as mock:
        route = mock.get("https://asia.api.riotgames.com/q").mock(
            return_value=httpx.Response(200, json=[])
        )
        await client.get("asia", "/q", params={"count": 5, "queue": 420})
        sent = route.calls.last.request
        assert sent.url.params["count"] == "5"
        assert sent.url.params["queue"] == "420"

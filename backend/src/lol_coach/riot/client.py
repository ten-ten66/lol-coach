from __future__ import annotations

import asyncio
from types import TracebackType
from typing import Any, Self

import httpx
import structlog

from lol_coach.riot.errors import (
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    ServerError,
    UnauthorizedError,
)
from lol_coach.riot.rate_limiter import TokenBucketRateLimiter

log = structlog.get_logger(__name__)

_HOST_TEMPLATE = "https://{host}.api.riotgames.com"


class AsyncRiotClient:
    """Async HTTP client for Riot Games API with rate limiting and retries.

    Hosts come in two flavors:
      - platform: 'jp1', 'kr', 'na1', etc. (for status/league/summoner endpoints)
      - regional: 'asia', 'americas', 'europe', 'sea' (for match-v5, account-v1)

    Callers pass the appropriate host per request.
    """

    def __init__(
        self,
        api_key: str,
        rate_limiter: TokenBucketRateLimiter | None = None,
        timeout: float = 10.0,
        max_retries: int = 3,
    ) -> None:
        self._api_key = api_key
        self._rate_limiter = rate_limiter or TokenBucketRateLimiter.riot_default()
        self._max_retries = max_retries
        self._http = httpx.AsyncClient(
            timeout=timeout,
            headers={"X-Riot-Token": api_key, "Accept": "application/json"},
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()

    async def get(
        self,
        host: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = _HOST_TEMPLATE.format(host=host) + path
        attempt = 0
        while True:
            attempt += 1
            await self._rate_limiter.acquire()
            try:
                response = await self._http.get(url, params=params)
            except httpx.RequestError as e:
                if attempt > self._max_retries:
                    raise
                backoff = min(2 ** (attempt - 1), 8)
                log.warning("riot_request_error", url=url, attempt=attempt, exc=str(e))
                await asyncio.sleep(backoff)
                continue

            if 200 <= response.status_code < 300:
                return response.json()

            error = _classify(response, url)
            if isinstance(error, RateLimitError) and attempt <= self._max_retries:
                log.warning("riot_rate_limited", url=url, retry_after=error.retry_after)
                await asyncio.sleep(error.retry_after)
                continue
            if isinstance(error, ServerError) and attempt <= self._max_retries:
                backoff = min(2 ** (attempt - 1), 8)
                log.warning(
                    "riot_server_error", url=url, attempt=attempt, status=response.status_code
                )
                await asyncio.sleep(backoff)
                continue
            raise error


def _classify(response: httpx.Response, url: str) -> RiotAPIError:
    status = response.status_code
    if status == 401:
        return UnauthorizedError(status, "unauthorized — check RIOT_API_KEY", url)
    if status == 403:
        return ForbiddenError(status, "forbidden — key may be expired or wrong region", url)
    if status == 404:
        return NotFoundError(status, "not found", url)
    if status == 429:
        retry_after = float(response.headers.get("Retry-After", "1"))
        return RateLimitError(retry_after, url)
    if 500 <= status < 600:
        return ServerError(status, "server error", url)
    return RiotAPIError(status, response.text[:200], url)
